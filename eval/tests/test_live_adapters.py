"""Offline unit tests for live adapter classes with mocked network responses."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from lajur_agent.adapters.deepgram import DeepgramSTTAdapter
from lajur_agent.adapters.edge_tts import EdgeTTSAdapter
from lajur_agent.adapters.gemini import GeminiLLMAdapter
from lajur_agent.adapters.groq import GroqSTTAdapter


@pytest.mark.asyncio
async def test_edge_tts_adapter_properties_and_empty() -> None:
    adapter = EdgeTTSAdapter(voice="id-ID-GadisNeural")
    assert adapter.name == "edge-tts-gadisneural"
    assert adapter.voice == "id-ID-GadisNeural"
    empty_bytes = await adapter.synthesize_text("   ")
    assert empty_bytes == b""


@pytest.mark.asyncio
async def test_gemini_adapter_empty_transcript() -> None:
    adapter = GeminiLLMAdapter(api_key="mock_key", model="gemini-2.5-flash")
    assert adapter.name == "gemini-gemini-2.5-flash"

    result = await adapter.parse_intent("")
    assert result.intents[0]["type"] == "unknown"
    assert "suaranya belum terdengar" in result.bot_reply


@pytest.mark.asyncio
async def test_gemini_adapter_parse_success() -> None:
    adapter = GeminiLLMAdapter(api_key="mock_key", model="gemini-2.5-flash")

    mock_response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                '{"intents": [{"type": "add_item", "params": {"item_id": "burger_sapi"}}],'
                                ' "bot_reply": "Siap kak, 1 burger sapi."}'
                            )
                        }
                    ]
                }
            }
        ],
        "usageMetadata": {"promptTokenCount": 50, "candidatesTokenCount": 25},
    }

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value=mock_response_data)

    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_resp)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        res = await adapter.parse_intent("pesan burger sapi")
        assert len(res.intents) == 1
        assert res.intents[0]["type"] == "add_item"
        assert res.bot_reply == "Siap kak, 1 burger sapi."
        assert res.tokens_in == 50
        assert res.tokens_out == 25


@pytest.mark.asyncio
async def test_groq_adapter_file_not_found() -> None:
    adapter = GroqSTTAdapter(api_key="mock_key")
    assert adapter.name == "groq-whisper-large-v3-turbo"

    with pytest.raises(FileNotFoundError):
        await adapter.transcribe_file("non_existent_audio.wav")


@pytest.mark.asyncio
async def test_deepgram_adapter_file_not_found() -> None:
    adapter = DeepgramSTTAdapter(api_key="mock_key")
    assert adapter.name == "deepgram-nova-2"

    with pytest.raises(FileNotFoundError):
        await adapter.transcribe_file("non_existent_audio.wav")
