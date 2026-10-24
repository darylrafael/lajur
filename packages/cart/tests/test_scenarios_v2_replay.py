"""Replay test for all 135 dataset scenarios using gold_intents_v2.jsonl.

Validates that the pure, deterministic Cart state machine reproduces the
exact expected_cart (items, quantities, sizes, modifiers, slots, total_price, and status)
for 100% of the scenarios in the evaluation dataset.
"""

import json
from datetime import time
from pathlib import Path

import pytest
from lajur_cart.intents import Intent
from lajur_cart.menu_service import MenuService
from lajur_cart.state_machine import CartSession
from pydantic import TypeAdapter

DATASETS_DIR = Path(__file__).resolve().parents[3] / "eval" / "datasets" / "v0"
SCENARIOS_PATH = DATASETS_DIR / "scenarios.jsonl"
GOLD_V2_PATH = DATASETS_DIR / "gold_intents_v2.jsonl"

intent_adapter = TypeAdapter(Intent)


def load_all_scenarios():
    scenarios_by_id = {
        s["id"]: s for s in [json.loads(line) for line in open(SCENARIOS_PATH, encoding="utf-8")]
    }
    gold_records = [json.loads(line) for line in open(GOLD_V2_PATH, encoding="utf-8")]
    return scenarios_by_id, gold_records


SCENARIOS_BY_ID, GOLD_RECORDS = load_all_scenarios()


@pytest.mark.parametrize("gold_record", GOLD_RECORDS, ids=[r["scenario_id"] for r in GOLD_RECORDS])
def test_scenario_gold_v2_replay(gold_record):
    sid = gold_record["scenario_id"]
    sc = SCENARIOS_BY_ID[sid]
    exp = gold_record["expected_cart"]
    tags = sc.get("tags", [])

    # Operating hours clock injection
    if "breakfast" in tags or "sarapan" in tags:
        if sid == "scen_094":

            def clock_fn():
                return time(7, 0)
        else:

            def clock_fn():
                return time(8, 0)
    else:

        def clock_fn():
            return time(12, 0)

    ms = MenuService(clock=clock_fn)
    sess = CartSession(ms, clock=clock_fn)

    # Replay sequence of intents
    for raw_it in gold_record["intents"]:
        it = intent_adapter.validate_python(raw_it)
        sess.apply(it)

    cart = sess.cart

    # 1. Compare Cart Status
    assert cart.status == exp.get("status"), (
        f"[{sid}] Status mismatch: got '{cart.status}', expected '{exp.get('status')}'"
    )

    # 2. Compare Total Price
    assert cart.total_price == exp.get("total_price", 0), (
        f"[{sid}] Total price mismatch: got {cart.total_price}, expected {exp.get('total_price')}"
    )

    # 3. Compare Items
    cart_items = [
        {
            "item_id": line.item_id,
            "quantity": line.quantity,
            "size": line.size,
            "modifiers": sorted(line.modifiers),
            "slots": line.slots,
            "upsell_rules": sorted(line.upsell_rules),
            "price": line.price,
        }
        for line in cart.items
    ]

    exp_items = [
        {
            "item_id": item["item_id"],
            "quantity": item.get("quantity", 1),
            "size": item.get("size", "regular"),
            "modifiers": sorted(item.get("modifiers", [])),
            "slots": item.get("slots", {}),
            "upsell_rules": sorted(item.get("upsell_rules", [])),
            "price": item.get("price", 0),
        }
        for item in exp.get("items", [])
    ]

    cart_sorted = sorted(cart_items, key=lambda x: (x["item_id"], x["quantity"], x["price"]))
    exp_sorted = sorted(exp_items, key=lambda x: (x["item_id"], x["quantity"], x["price"]))

    assert cart_sorted == exp_sorted, (
        f"[{sid}] Items mismatch:\nGot: {cart_sorted}\nExp: {exp_sorted}"
    )


def test_category_pass_rates_summary():
    """Aggregates and verifies 100% pass rate across all primary categories."""
    categories = [
        "simple",
        "quantity",
        "modifier",
        "combo",
        "correction",
        "out_of_stock",
        "breakfast",
        "handoff",
        "injection",
    ]

    counts = {cat: {"total": 0, "passed": 0} for cat in categories}

    for gold_record in GOLD_RECORDS:
        sid = gold_record["scenario_id"]
        sc = SCENARIOS_BY_ID[sid]
        exp = gold_record["expected_cart"]
        tags = sc.get("tags", [])

        if "breakfast" in tags or "sarapan" in tags:
            clock_fn = (lambda: time(7, 0)) if sid == "scen_094" else (lambda: time(8, 0))
        else:

            def clock_fn():
                return time(12, 0)

        ms = MenuService(clock=clock_fn)
        sess = CartSession(ms, clock=clock_fn)

        for raw_it in gold_record["intents"]:
            it = intent_adapter.validate_python(raw_it)
            sess.apply(it)

        cart = sess.cart
        cart_items_sorted = sorted(
            [
                {
                    "item_id": cart_line.item_id,
                    "quantity": cart_line.quantity,
                    "size": cart_line.size,
                    "modifiers": sorted(cart_line.modifiers),
                    "slots": cart_line.slots,
                    "upsell_rules": sorted(cart_line.upsell_rules),
                    "price": cart_line.price,
                }
                for cart_line in cart.items
            ],
            key=lambda x: (x["item_id"], x["quantity"], x["price"]),
        )

        exp_items_sorted = sorted(
            [
                {
                    "item_id": i["item_id"],
                    "quantity": i.get("quantity", 1),
                    "size": i.get("size", "regular"),
                    "modifiers": sorted(i.get("modifiers", [])),
                    "slots": i.get("slots", {}),
                    "upsell_rules": sorted(i.get("upsell_rules", [])),
                    "price": i.get("price", 0),
                }
                for i in exp.get("items", [])
            ],
            key=lambda x: (x["item_id"], x["quantity"], x["price"]),
        )

        is_passed = (
            cart.status == exp.get("status")
            and cart.total_price == exp.get("total_price", 0)
            and cart_items_sorted == exp_items_sorted
        )

        for cat in categories:
            match = False
            if cat == "breakfast" and ("breakfast" in tags or "sarapan" in tags):
                match = True
            elif cat == "injection" and ("injection" in tags or "prank" in tags or "abuse" in tags):
                match = True
            elif cat in tags:
                match = True

            if match:
                counts[cat]["total"] += 1
                if is_passed:
                    counts[cat]["passed"] += 1

    print("\n=== Per-Category Pass Rate Report ===")
    for cat, data in counts.items():
        total = data["total"]
        passed = data["passed"]
        pct = (passed / total * 100.0) if total > 0 else 0.0
        print(f"Category '{cat}': {passed}/{total} ({pct:.1f}%)")
        assert passed == total, f"Category '{cat}' had failures: {passed}/{total}"
