"""Tests for corrections and undo through the full pipeline with fake adapters.

Evaluates the 11 pre-registered correction and undo scenarios from eval/datasets/v0.
NOTE: Gold labels in gold_intents_v2.jsonl are agent-authored and unverified.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from lajur_agent.adapters.base import IntentResult
from lajur_agent.adapters.fakes import FakeLLMIntentAdapter, FakeSTTAdapter, FakeTTSAdapter
from lajur_agent.observability import TurnEventLogger
from lajur_agent.pipeline import VoiceOrderingPipeline
from lajur_cart.menu_service import MenuService

CORRECTION_SCENARIO_IDS = [
    "scen_071",
    "scen_072",
    "scen_073",
    "scen_074",
    "scen_075",
    "scen_076",
    "scen_077",
    "scen_078",
    "scen_079",
    "scen_080",
    "scen_134",
]

DATASETS_DIR = Path(__file__).resolve().parents[3] / "eval" / "datasets" / "v0"
GOLD_V2_PATH = DATASETS_DIR / "gold_intents_v2.jsonl"


def load_correction_records() -> dict[str, dict[str, Any]]:
    records = {}
    with open(GOLD_V2_PATH, encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            if obj["scenario_id"] in CORRECTION_SCENARIO_IDS:
                records[obj["scenario_id"]] = obj
    return records


RECORDS_BY_ID = load_correction_records()


class CannedScenarioLLM(FakeLLMIntentAdapter):
    """LLM adapter returning pre-registered gold intents for each turn of a scenario."""

    def __init__(self, intents_per_turn: list[list[dict[str, Any]]]) -> None:
        super().__init__()
        self._intents_per_turn = intents_per_turn
        self._call_index = 0

    async def parse_intent(
        self,
        transcript: str,
        history: list[dict[str, str]] | None = None,
        cart_snapshot: dict[str, Any] | None = None,
        pending_choice: dict[str, Any] | None = None,
        menu_context: dict[str, Any] | None = None,
    ) -> IntentResult:
        if self._call_index < len(self._intents_per_turn):
            turn_intents = self._intents_per_turn[self._call_index]
            self._call_index += 1
        else:
            turn_intents = [{"type": "unknown", "raw_text": transcript}]

        return IntentResult(
            intents=turn_intents,
            bot_reply="Baik kak.",
            ttft_ms=10.0,
            total_latency_ms=15.0,
            tokens_in=50,
            tokens_out=20,
            raw_response="{}",
        )


@pytest.mark.parametrize("scenario_id", CORRECTION_SCENARIO_IDS)
@pytest.mark.asyncio
async def test_correction_scenario_through_pipeline(scenario_id: str) -> None:
    record = RECORDS_BY_ID.get(scenario_id)
    assert record is not None, f"Scenario {scenario_id} not found in gold_intents_v2.jsonl"

    utterances = record.get("utterances", [])
    intents = record.get("intents", [])
    expected_cart = record.get("expected_cart", {})

    # Partition intents across utterances
    # If number of utterances is > 1, distribute intents sensibly
    num_utterances = max(1, len(utterances))
    if num_utterances == 1:
        intents_per_turn = [intents]
    else:
        # Divide intents among turns
        chunk_size = max(1, len(intents) // num_utterances)
        intents_per_turn = []
        for i in range(num_utterances):
            if i == num_utterances - 1:
                intents_per_turn.append(intents[i * chunk_size :])
            else:
                intents_per_turn.append(intents[i * chunk_size : (i + 1) * chunk_size])

    ms = MenuService()
    llm = CannedScenarioLLM(intents_per_turn)
    stt = FakeSTTAdapter()
    tts = FakeTTSAdapter()
    event_logger = TurnEventLogger()

    pipeline = VoiceOrderingPipeline(
        session_id=f"test_{scenario_id}",
        menu_service=ms,
        stt_adapter=stt,
        llm_adapter=llm,
        tts_adapter=tts,
        event_logger=event_logger,
        reply_mode="template",
    )

    # Process each utterance through the full pipeline
    for utt in utterances:
        await pipeline.process_turn(utt)

    final_cart = pipeline.session.cart

    # Validate against expected cart
    assert final_cart.total_price == expected_cart["total_price"], (
        f"Price mismatch in {scenario_id}: expected {expected_cart['total_price']}, got {final_cart.total_price}"
    )

    expected_items = expected_cart.get("items", [])
    # Check item count
    expected_count = sum(it.get("quantity", 1) for it in expected_items)
    assert final_cart.total_item_count == expected_count, (
        f"Item count mismatch in {scenario_id}: expected {expected_count}, got {final_cart.total_item_count}"
    )

    # Check item IDs present
    expected_item_ids = {it["item_id"] for it in expected_items}
    cart_item_ids = {line.item_id for line in final_cart.items}
    assert cart_item_ids == expected_item_ids, (
        f"Item IDs mismatch in {scenario_id}: expected {expected_item_ids}, got {cart_item_ids}"
    )
