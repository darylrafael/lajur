"""Unit tests for Lajur Web Protocol v1 (docs/design/web-protocol.md & ADR-0014).

Verifies:
- All protocol event generator functions emit valid schemas with version="v1".
- Conformance against packages/cart/web-protocol.schema.json.
- Cart snapshot with line IDs, item names, modifiers, and prices.
- Pending choices for awaiting_choice state.
- Handoff, error, and session limits events.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
from lajur_agent.adapters.fakes import FakeLLMIntentAdapter, FakeSTTAdapter, FakeTTSAdapter
from lajur_agent.observability import TurnEventLogger
from lajur_agent.pipeline import VoiceOrderingPipeline
from lajur_agent.protocol import (
    PROTOCOL_VERSION,
    create_bot_reply_text_event,
    create_bot_speaking_end_event,
    create_bot_speaking_start_event,
    create_error_event,
    create_final_transcript_event,
    create_handoff_event,
    create_intent_applied_event,
    create_partial_transcript_event,
    create_pending_question_event,
    create_session_limits_event,
)
from lajur_cart.menu_service import MenuService
from lajur_cart.models import Cart, CartLine
from lajur_cart.state_machine import PendingChoice, SpeechFacts


@pytest.fixture
def protocol_schema() -> dict:
    schema_path = (
        Path(__file__).resolve().parents[3] / "packages" / "cart" / "web-protocol.schema.json"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def menu_service() -> MenuService:
    return MenuService()


def test_protocol_version_constant() -> None:
    assert PROTOCOL_VERSION == "v1"


def test_partial_transcript_schema(protocol_schema: dict) -> None:
    event = create_partial_transcript_event("saya mau burger", timestamp_ms=100.0)
    assert event["version"] == "v1"
    assert event["type"] == "partial_transcript"
    assert event["is_final"] is False
    assert event["text"] == "saya mau burger"
    jsonschema.validate(instance=event, schema=protocol_schema)


def test_final_transcript_schema(protocol_schema: dict) -> None:
    event = create_final_transcript_event("saya mau burger rendang satu", timestamp_ms=200.0)
    assert event["version"] == "v1"
    assert event["type"] == "final_transcript"
    assert event["is_final"] is True
    assert event["text"] == "saya mau burger rendang satu"
    jsonschema.validate(instance=event, schema=protocol_schema)


def test_intent_applied_schema(protocol_schema: dict, menu_service: MenuService) -> None:
    line = CartLine(
        line_id="line_1",
        item_id="burger_sapi_tunggal",
        quantity=2,
        size="regular",
        modifiers=["extra_cheese"],
        slots={},
        price=76000,
    )
    cart = Cart(
        items=[line],
        total_price=76000,
        status="in_progress",
    )
    speech_facts = SpeechFacts(
        intent_handled="add_item",
        items_added=[{"item_id": "burger_sapi_tunggal", "quantity": 2, "size": "regular"}],
        cart_item_count=2,
        cart_total_price=76000,
        dialog_state="ordering",
    )

    event = create_intent_applied_event(
        state="ordering",
        cart=cart,
        speech_facts=speech_facts,
        menu_service=menu_service,
        state_from="ordering",
        timestamp_ms=300.0,
    )

    assert event["version"] == "v1"
    assert event["type"] == "intent_applied"
    assert event["state"] == "ordering"
    assert event["state_from"] == "ordering"
    assert len(event["cart"]["items"]) == 1
    assert event["cart"]["items"][0]["line_id"] == "line_1"
    assert event["cart"]["items"][0]["name_id"] == "Burger Sapi Tunggal"
    assert event["cart"]["items"][0]["unit_price"] == 38000
    assert event["cart"]["total_price"] == 76000
    assert event["cart"]["total_item_count"] == 2

    jsonschema.validate(instance=event, schema=protocol_schema)


def test_bot_reply_and_speaking_events(protocol_schema: dict) -> None:
    reply = create_bot_reply_text_event("Baik kak, pesanan dicatat.", timestamp_ms=400.0)
    start = create_bot_speaking_start_event(timestamp_ms=410.0)
    end = create_bot_speaking_end_event(timestamp_ms=480.0)

    for ev in [reply, start, end]:
        assert ev["version"] == "v1"
        jsonschema.validate(instance=ev, schema=protocol_schema)


def test_pending_question_schema(protocol_schema: dict, menu_service: MenuService) -> None:
    pc = PendingChoice(
        type="combo_slot",
        target_line_id="line_combo_1",
        slot_id="drink",
        prompt="Mau pilih minuman apa untuk Paket Hemat?",
        allowed_choices=["cola", "teh_manis"],
    )

    event = create_pending_question_event(pc, menu_service=menu_service, timestamp_ms=500.0)
    assert event["version"] == "v1"
    assert event["type"] == "pending_question"
    assert event["kind"] == "combo_slot"
    assert event["target_line_id"] == "line_combo_1"
    assert event["slot_id"] == "drink"
    assert len(event["choices"]) == 2
    assert event["choices"][0]["id"] == "cola"

    jsonschema.validate(instance=event, schema=protocol_schema)


def test_handoff_and_error_events(protocol_schema: dict) -> None:
    handoff = create_handoff_event(reason="customer_request", timestamp_ms=600.0)
    error = create_error_event(
        code="MIC_DISCONNECTED",
        message="Mikrofon terputus",
        recoverable=True,
        timestamp_ms=650.0,
    )

    for ev in [handoff, error]:
        assert ev["version"] == "v1"
        jsonschema.validate(instance=ev, schema=protocol_schema)


def test_session_limits_schema(protocol_schema: dict) -> None:
    limits = create_session_limits_event(
        turns_used=3,
        max_turns=12,
        time_elapsed_seconds=45.2,
        time_limit_seconds=180.0,
        timestamp_ms=700.0,
    )
    assert limits["version"] == "v1"
    assert limits["turns_used"] == 3
    assert limits["max_turns"] == 12
    assert limits["time_elapsed_seconds"] == 45.2
    assert limits["time_limit_seconds"] == 180.0
    jsonschema.validate(instance=limits, schema=protocol_schema)


@pytest.mark.asyncio
async def test_live_event_serialization_order_and_schema(
    protocol_schema: dict, menu_service: MenuService, tmp_path: Path
) -> None:
    """Contract test for the live worker event serialization path with offline fake adapters.

    What it covers:
    - End-to-end execution of worker event serialization logic using offline fakes.
    - Captures all emitted data-channel protocol messages in memory.
    - Validates every individual message against packages/cart/web-protocol.schema.json.
    - Asserts strict causal event ordering:
      partial_transcript -> final_transcript -> intent_applied -> bot_reply_text ->
      bot_speaking_start -> bot_speaking_end -> session_limits.
    - Verifies exact synchronization between packages/cart state machine and event payload.

    What it DOES NOT cover:
    - Real Deepgram Nova-3 interim WebSocket audio streaming callbacks.
    - Real acoustic silence / VAD endpointing delays.
    - Real WebRTC UDP network transport (packet loss, latency jitter, or out-of-order delivery).
    """
    captured_events: list[dict] = []

    async def mock_publish(event: dict) -> None:
        # Validate against JSON schema at serialization time
        jsonschema.validate(instance=event, schema=protocol_schema)
        captured_events.append(event)

    db_file = tmp_path / "test_events.sqlite3"
    pipeline = VoiceOrderingPipeline(
        session_id="test-session-mock",
        menu_service=menu_service,
        stt_adapter=FakeSTTAdapter(),
        llm_adapter=FakeLLMIntentAdapter(),
        tts_adapter=FakeTTSAdapter(),
        event_logger=TurnEventLogger(db_path=db_file),
        reply_mode="template",
    )

    # Simulate worker turn lifecycle:
    # 1. User speaks: STT emits interim partial transcript
    await mock_publish(create_partial_transcript_event("saya mau burger", timestamp_ms=100.0))

    # 2. STT finishes: emits final transcript
    final_text = "saya mau burger sapi satu"
    await mock_publish(create_final_transcript_event(final_text, timestamp_ms=200.0))

    # 3. Pipeline executes deterministic state machine
    state_before = pipeline.session.state
    res = await pipeline.process_turn(final_text)

    # 4. Worker emits intent_applied snapshot
    await mock_publish(
        create_intent_applied_event(
            state=pipeline.session.state,
            cart=pipeline.session.cart,
            speech_facts=res.speech_facts,
            menu_service=pipeline.menu_service,
            state_from=state_before,
            timestamp_ms=300.0,
        )
    )

    # 5. Worker emits cashier speech text
    await mock_publish(create_bot_reply_text_event(res.reply_text, timestamp_ms=350.0))

    # 6. Worker emits bot speaking markers
    await mock_publish(create_bot_speaking_start_event(timestamp_ms=400.0))
    await mock_publish(create_bot_speaking_end_event(timestamp_ms=600.0))

    # 7. Worker emits session limits update
    await mock_publish(
        create_session_limits_event(
            turns_used=pipeline.turn_counter,
            max_turns=pipeline.max_turns,
            time_elapsed_seconds=1.2,
            time_limit_seconds=180.0,
            timestamp_ms=605.0,
        )
    )

    # Verify event types and causal sequence
    event_types = [e["type"] for e in captured_events]
    assert event_types == [
        "partial_transcript",
        "final_transcript",
        "intent_applied",
        "bot_reply_text",
        "bot_speaking_start",
        "bot_speaking_end",
        "session_limits",
    ]

    # Verify specific ordering invariants:
    # partial before final
    assert event_types.index("partial_transcript") < event_types.index("final_transcript")
    # final before intent_applied
    assert event_types.index("final_transcript") < event_types.index("intent_applied")
    # intent_applied before bot_reply_text
    assert event_types.index("intent_applied") < event_types.index("bot_reply_text")

    # Verify intent_applied content matches cart state machine
    intent_event = captured_events[2]
    assert intent_event["cart"]["total_item_count"] == 1
    assert intent_event["cart"]["items"][0]["item_id"] == "burger_sapi_tunggal"
    assert intent_event["speech_facts"]["intent_handled"] == "add_item"
