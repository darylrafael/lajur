"""Generates gold intent labels for all 135 evaluation scenarios in eval/datasets/v0/.

Derived from customer utterances and expected_cart ground truth.
Labeled with author='agent'.
Selects 20 seeded scenario IDs for human spot-checking.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

RANDOM_SEED = 42


def derive_intents_for_scenario(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    intents: list[dict[str, Any]] = []
    scen_id = scenario["id"]
    tags = set(scenario.get("tags", []))
    expected_cart = scenario.get("expected_cart", {})
    cart_items = expected_cart.get("items", [])

    # 1. Handoff scenarios
    if "handoff" in tags:
        intents.append(
            {
                "type": "handoff",
                "params": {"reason": "customer_requested_human_crew"},
            }
        )
        return intents

    # 2. Prompt injection / Prank scenarios
    if "injection" in tags or "prank" in tags:
        intents.append(
            {
                "type": "unknown",
                "params": {
                    "raw_text": " ".join(scenario.get("utterances", [])),
                    "reason": "adversarial_prompt_or_prank",
                },
            }
        )
        return intents

    # 3. Corrections / Undo
    if "correction" in tags or "undo" in tags:
        # If scenario represents a cancellation / modification
        # For simplicity in gold evaluation, record the intermediate undo/remove before final state
        intents.append({"type": "undo", "params": {"steps": 1}})

    # 4. Standard item addition from expected_cart
    for item in cart_items:
        params: dict[str, Any] = {
            "item_id": item["item_id"],
            "quantity": item.get("quantity", 1),
            "size": item.get("size", "size_regular") if "size" in item else None,
            "modifiers": item.get("modifiers", []),
            "combo_choices": item.get("combo_choices", []),
        }
        intents.append({"type": "add_item", "params": params})

    # 5. Confirmation
    if expected_cart.get("status") == "confirmed":
        intents.append({"type": "confirm", "params": {"payment_method": None}})

    return intents


def main() -> None:
    scenarios_path = Path("eval/datasets/v0/scenarios.jsonl")
    with open(scenarios_path, "r", encoding="utf-8") as f:
        scenarios = [json.loads(line) for line in f if line.strip()]

    gold_entries: list[dict[str, Any]] = []
    for s in scenarios:
        intents = derive_intents_for_scenario(s)
        gold_entry = {
            "scenario_id": s["id"],
            "author": "agent",
            "version": "v0.1-draft",
            "utterances": s.get("utterances", []),
            "intents": intents,
            "expected_cart": s.get("expected_cart", {}),
        }
        gold_entries.append(gold_entry)

    gold_path = Path("eval/datasets/v0/gold_intents.jsonl")
    with open(gold_path, "w", encoding="utf-8") as f:
        for entry in gold_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Generated {len(gold_entries)} gold intent records at {gold_path}.")

    # Pick 20 scenario IDs at random using fixed seed
    random.seed(RANDOM_SEED)
    all_ids = [s["id"] for s in scenarios]
    spot_check_ids = sorted(random.sample(all_ids, 20))

    print(f"\n20 Seeded Spot-Check Scenario IDs (Seed={RANDOM_SEED}):")
    for i, scen_id in enumerate(spot_check_ids, 1):
        print(f"  {i:02d}. {scen_id}")

    # Save spot check list to a text file for checklist reference
    with open("eval/datasets/v0/spot_check_20.json", "w", encoding="utf-8") as f:
        json.dump({"seed": RANDOM_SEED, "spot_check_scenario_ids": spot_check_ids}, f, indent=2)


if __name__ == "__main__":
    main()
