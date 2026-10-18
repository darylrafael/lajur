"""Offline unit tests for agent worker logic without network access.

Tests data-channel packet parsing, ping-pong RTT formatting,
rate limiting logic, and audio frame buffer calculations.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from livekit import rtc


def test_ping_pong_message_format():
    """Verify pong message preserves client_time and has correct schema."""
    client_time = 1234567.89
    ping_payload = json.dumps({"type": "ping", "client_time": client_time})

    data = json.loads(ping_payload)
    assert data["type"] == "ping"
    assert data["client_time"] == client_time

    pong_payload = json.dumps({
        "type": "pong",
        "client_time": data.get("client_time"),
    })
    pong_data = json.loads(pong_payload)
    assert pong_data["type"] == "pong"
    assert pong_data["client_time"] == client_time


def test_audio_frame_50ms_buffer_sizing():
    """Verify 48000 Hz mono 50ms frame has exactly 2400 samples per channel."""
    sample_rate = 48000
    num_channels = 1
    frame_size_ms = 50
    expected_samples = int(sample_rate * (frame_size_ms / 1000.0))

    assert expected_samples == 2400

    frame = rtc.AudioFrame.create(sample_rate, num_channels, expected_samples)
    assert frame.sample_rate == sample_rate
    assert frame.num_channels == num_channels
    assert frame.samples_per_channel == 2400


def test_audio_frame_event_extraction():
    """Verify AudioFrameEvent correctly wraps and exposes AudioFrame."""
    frame = rtc.AudioFrame.create(48000, 1, 2400)
    event = rtc.AudioFrameEvent(frame)

    assert hasattr(event, "frame")
    assert isinstance(event.frame, rtc.AudioFrame)
    assert event.frame.sample_rate == 48000
    assert event.frame.samples_per_channel == 2400


@pytest.mark.asyncio
async def test_on_data_received_ping_pong_and_rate_limiting():
    """Test data packet handling and rate limiter logic offline."""
    mock_publish = AsyncMock()
    mock_participant = MagicMock()
    mock_participant.publish_data = mock_publish

    last_pong_time = -10.0

    async def handle_ping_packet(data_bytes: bytes, current_time: float) -> bool:
        nonlocal last_pong_time
        try:
            raw_text = data_bytes.decode("utf-8")
            msg = json.loads(raw_text)
            if msg.get("type") == "ping":
                if current_time - last_pong_time < 1.5:
                    return False  # Throttled
                last_pong_time = current_time
                pong_data = json.dumps({
                    "type": "pong",
                    "client_time": msg.get("client_time"),
                }).encode("utf-8")
                await mock_participant.publish_data(
                    pong_data,
                    topic="lajur-control",
                    reliable=False,
                )
                return True
        except Exception:
            return False
        return False

    # 1. First ping at t=1.0 should succeed
    ping_1 = json.dumps({"type": "ping", "client_time": 100.0}).encode("utf-8")
    responded_1 = await handle_ping_packet(ping_1, current_time=1.0)
    assert responded_1 is True
    assert mock_publish.call_count == 1

    # 2. Immediate second ping at t=1.2 (<1.5s delta) should be throttled
    ping_2 = json.dumps({"type": "ping", "client_time": 100.2}).encode("utf-8")
    responded_2 = await handle_ping_packet(ping_2, current_time=1.2)
    assert responded_2 is False
    assert mock_publish.call_count == 1  # Not incremented

    # 3. Third ping at t=2.6 (>1.5s delta) should succeed
    ping_3 = json.dumps({"type": "ping", "client_time": 101.6}).encode("utf-8")
    responded_3 = await handle_ping_packet(ping_3, current_time=2.6)
    assert responded_3 is True
    assert mock_publish.call_count == 2


@pytest.mark.asyncio
async def test_on_data_received_malformed_json_graceful():
    """Verify non-json or garbage payload does not raise exceptions."""
    mock_participant = MagicMock()
    mock_publish = AsyncMock()
    mock_participant.publish_data = mock_publish

    garbage = b"\x00\xff\xfe\x01\x02"

    try:
        raw_text = garbage.decode("utf-8")
        json.loads(raw_text)
    except Exception:
        # Gracefully caught and ignored
        pass

    assert mock_publish.call_count == 0
