"""Tests for FR-09 (Handoff), FR-10 (Upsell), and Vendor Graceful Degradation."""

from __future__ import annotations

from typing import Any

import pytest
from lajur_agent.adapters.base import TTSAdapter
from lajur_agent.adapters.fakes import FakeLLMIntentAdapter, FakeSTTAdapter, FakeTTSAdapter
from lajur_agent.observability import TurnEventLogger
from lajur_agent.pipeline import VoiceOrderingPipeline
from lajur_cart.menu_service import MenuService


class FailingTTSAdapter(TTSAdapter):
    """Simulates TTS quota exhaustion or network failure."""

    @property
    def name(self) -> str:
        return "failing-tts"

    async def synthesize_text(self, text: str) -> bytes:
        raise RuntimeError("ElevenLabs quota exhausted: 401 Unauthorized / Limit Exceeded")

    async def synthesize_stream(self, text_stream: Any) -> Any:
        raise RuntimeError("ElevenLabs quota exhausted: 401 Unauthorized / Limit Exceeded")


def create_test_pipeline(
    tts_adapter: TTSAdapter | None = None,
    canned_intents: dict[str, list[dict[str, Any]]] | None = None,
    max_unknown_intents: int = 3,
) -> VoiceOrderingPipeline:
    ms = MenuService()
    stt = FakeSTTAdapter()
    llm = FakeLLMIntentAdapter(canned_intents=canned_intents)
    tts = tts_adapter or FakeTTSAdapter()
    logger = TurnEventLogger()

    pipeline = VoiceOrderingPipeline(
        session_id="test_sess_robustness",
        menu_service=ms,
        stt_adapter=stt,
        llm_adapter=llm,
        tts_adapter=tts,
        event_logger=logger,
        reply_mode="template",
    )
    pipeline.max_unknown_intents = max_unknown_intents
    return pipeline


@pytest.mark.asyncio
async def test_fr09_handoff_explicit_request() -> None:
    """Customer explicit request ('panggil kasir') triggers handoff with cart preserved."""
    canned = {
        "panggil kasir dong": [{"type": "handoff", "reason": "customer_request"}],
    }
    p = create_test_pipeline(canned_intents=canned)

    # 1. Add item
    await p.process_turn("pesan kentang goreng satu")
    assert p.session.cart.total_item_count == 1
    assert p.session.state == "ordering"

    # 2. Explicit handoff
    res = await p.process_turn("panggil kasir dong")
    assert p.session.state == "handoff"
    assert p.session.cart.total_item_count == 1  # Cart is preserved!
    assert "kasir" in res.reply_text.lower()


@pytest.mark.asyncio
async def test_fr09_handoff_repeated_unknown_intents() -> None:
    """Repeated unrecognized speech (>= 3 consecutive unknown turns) automatically triggers handoff."""
    canned = {
        "gibberish turn 1": [{"type": "unknown", "raw_text": "gibberish 1"}],
        "gibberish turn 2": [{"type": "unknown", "raw_text": "gibberish 2"}],
        "gibberish turn 3": [{"type": "unknown", "raw_text": "gibberish 3"}],
    }
    p = create_test_pipeline(canned_intents=canned, max_unknown_intents=3)

    # Turn 1: unknown -> count = 1
    await p.process_turn("gibberish turn 1")
    assert p.consecutive_unknown_count == 1
    assert p.session.state == "ordering"

    # Turn 2: unknown -> count = 2
    await p.process_turn("gibberish turn 2")
    assert p.consecutive_unknown_count == 2
    assert p.session.state == "ordering"

    # Turn 3: unknown -> count = 3 -> handoff triggered!
    res = await p.process_turn("gibberish turn 3")
    assert p.session.state == "handoff"
    assert "kasir" in res.reply_text.lower()


@pytest.mark.asyncio
async def test_fr10_upsell_offered_once_and_never_repeated_after_decline() -> None:
    """Upsell is offered at most once per order and never repeated after customer declines."""
    canned = {
        "pesan paket hemat burger tunggal satu": [
            {
                "type": "add_item",
                "item_id": "paket_hemat_burger_tunggal",
                "quantity": 1,
                "params": {"item_id": "paket_hemat_burger_tunggal", "quantity": 1},
            }
        ],
        "tidak usah": [{"type": "decline_more"}],
        "tambah burger rendang satu": [
            {
                "type": "add_item",
                "item_id": "burger_rendang",
                "quantity": 1,
                "params": {"item_id": "burger_rendang", "quantity": 1},
            }
        ],
    }
    p = create_test_pipeline(canned_intents=canned)

    # Turn 1: Add combo with upsell_rules -> upsell should be offered in reply
    res1 = await p.process_turn("pesan paket hemat burger tunggal satu")
    assert p.upsell_offered is True
    assert p.pending_upsell is not None
    assert "upsize" in res1.reply_text.lower() or "kentang" in res1.reply_text.lower()

    # Turn 2: Customer declines upsell
    await p.process_turn("tidak usah")
    assert p.upsell_declined is True
    assert p.pending_upsell is None

    # Turn 3: Customer adds another item -> upsell must NOT be repeated!
    res3 = await p.process_turn("tambah burger rendang satu")
    assert p.upsell_offered is True
    assert "upsize" not in res3.reply_text.lower()


@pytest.mark.asyncio
async def test_graceful_degradation_tts_quota_exhausted() -> None:
    """When TTS synthesis fails, pipeline falls back to text-only mode seamlessly without crash."""
    failing_tts = FailingTTSAdapter()
    p = create_test_pipeline(tts_adapter=failing_tts)

    # Process turn with broken TTS
    res = await p.process_turn("pesan kentang goreng satu")

    # Reply text is generated and cart mutated normally
    assert "kentang goreng" in res.reply_text.lower()
    assert res.audio_bytes == b""
    assert res.tts_degraded is True
    assert res.turn_event.tts_model_id == "text_only_fallback"
    assert p.session.cart.total_item_count == 1
