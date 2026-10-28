"""Contract tests for VoiceOrderingPipeline using offline fakes."""

import os
from pathlib import Path

import pytest
from lajur_agent.adapters.fakes import FakeLLMIntentAdapter, FakeSTTAdapter, FakeTTSAdapter
from lajur_agent.observability import TurnEventLogger
from lajur_agent.pipeline import VoiceOrderingPipeline
from lajur_cart.menu_service import MenuService


@pytest.fixture
def test_pipeline(tmp_path: Path) -> VoiceOrderingPipeline:
    db_file = tmp_path / "test_events.sqlite3"
    ms = MenuService()
    stt = FakeSTTAdapter()
    llm = FakeLLMIntentAdapter()
    tts = FakeTTSAdapter()
    logger = TurnEventLogger(db_path=db_file)

    return VoiceOrderingPipeline(
        session_id="test-session-123",
        menu_service=ms,
        stt_adapter=stt,
        llm_adapter=llm,
        tts_adapter=tts,
        event_logger=logger,
        reply_mode="template",
    )


@pytest.mark.asyncio
async def test_pipeline_add_item_happy_path(test_pipeline: VoiceOrderingPipeline) -> None:
    res = await test_pipeline.process_turn("Saya pesan burger sapi satu ya")

    assert res.turn_event.intent_type == "add_item"
    assert res.turn_event.state_to == "ordering"
    assert len(res.cart["items"]) == 1
    assert res.cart["items"][0]["item_id"] == "burger_sapi_tunggal"
    assert "burger sapi" in res.reply_text.lower()
    assert len(res.audio_bytes) > 0

    events = test_pipeline.event_logger.get_events(session_id="test-session-123")
    assert len(events) == 1
    assert events[0]["turn_id"] == 1
    assert events[0]["intent_type"] == "add_item"


@pytest.mark.asyncio
async def test_pipeline_full_order_flow(test_pipeline: VoiceOrderingPipeline) -> None:
    # 1. Add Burger
    r1 = await test_pipeline.process_turn("Mau burger sapi satu")
    assert r1.cart["total_item_count"] == 1

    # 2. Add Kentang
    r2 = await test_pipeline.process_turn("Tambah kentang goreng satu")
    assert r2.cart["total_item_count"] == 2

    # 3. Confirm
    r3 = await test_pipeline.process_turn("Sudah itu aja, konfirmasi")
    assert r3.turn_event.state_to == "done"
    assert r3.cart["status"] == "confirmed"
    assert "dikonfirmasi" in r3.reply_text.lower()

    events = test_pipeline.event_logger.get_events(session_id="test-session-123")
    assert len(events) == 3


@pytest.mark.asyncio
async def test_pipeline_kill_switch_guardrail(test_pipeline: VoiceOrderingPipeline) -> None:
    os.environ["KILL_SWITCH"] = "1"
    try:
        res = await test_pipeline.process_turn("Pesan burger sapi satu")
        assert "KILL_SWITCH_ACTIVE" in res.rejections
        assert res.turn_event.state_to == "handoff"
        assert "pemeliharaan" in res.reply_text
    finally:
        os.environ.pop("KILL_SWITCH", None)


@pytest.mark.asyncio
async def test_pipeline_max_turns_guardrail(test_pipeline: VoiceOrderingPipeline) -> None:
    test_pipeline.max_turns = 2

    await test_pipeline.process_turn("Burger satu")
    await test_pipeline.process_turn("Kentang satu")
    res3 = await test_pipeline.process_turn("Es teh satu")

    assert "MAX_TURNS_EXCEEDED" in res3.rejections
    assert res3.turn_event.state_to == "handoff"


@pytest.mark.asyncio
async def test_pipeline_reply_mode_llm_verbalization(tmp_path: Path) -> None:
    db_file = tmp_path / "test_events_llm.sqlite3"
    ms = MenuService()
    stt = FakeSTTAdapter()
    llm = FakeLLMIntentAdapter()
    tts = FakeTTSAdapter()
    logger = TurnEventLogger(db_path=db_file)

    pipeline = VoiceOrderingPipeline(
        session_id="test-llm-mode",
        menu_service=ms,
        stt_adapter=stt,
        llm_adapter=llm,
        tts_adapter=tts,
        event_logger=logger,
        reply_mode="llm",
    )

    res = await pipeline.process_turn("Mau burger sapi satu")
    assert res.turn_event.mode == "llm"
    assert "dicatat" in res.reply_text
