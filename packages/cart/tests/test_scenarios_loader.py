"""Tests loading and verifying every scenario in eval/datasets/v0/ against MenuService."""

import json
from pathlib import Path

import pytest
from lajur_cart.menu_service import MenuService
from lajur_cart.models import Cart, CartLine


def load_all_scenarios():
    # Look for scenarios file in repository
    scenarios_path = Path("eval/datasets/v0/scenarios.jsonl")
    if not scenarios_path.exists():
        scenarios_path = (
            Path(__file__).resolve().parents[4] / "eval" / "datasets" / "v0" / "scenarios.jsonl"
        )

    scenarios = []
    with open(scenarios_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                scenarios.append(json.loads(line_str))
    return scenarios


@pytest.fixture(scope="module")
def menu_service() -> MenuService:
    return MenuService()


@pytest.mark.parametrize("scenario", load_all_scenarios(), ids=lambda s: s["id"])
def test_scenario_expected_cart_validation_and_price(menu_service: MenuService, scenario: dict):
    expected_cart_data = scenario["expected_cart"]
    items_data = expected_cart_data.get("items", [])
    stated_total = expected_cart_data.get("total_price", 0)

    # Build Cart domain model
    cart_lines = []
    for item_raw in items_data:
        cart_lines.append(
            CartLine(
                item_id=item_raw["item_id"],
                quantity=item_raw.get("quantity", 1),
                size=item_raw.get("size", "regular"),
                modifiers=item_raw.get("modifiers", []),
                slots=item_raw.get("slots", {}),
                upsell_rules=item_raw.get("upsell_rules", []),
                price=item_raw.get("price", 0),
            )
        )

    cart = Cart(
        items=cart_lines,
        total_price=stated_total,
        status=expected_cart_data.get("status", "confirmed"),
    )

    # Calculate price strictly using MenuService
    computed_total = menu_service.calculate_cart_total(cart)

    # Assert computed price matches scenario stated total price
    assert computed_total == stated_total, (
        f"Scenario {scenario['id']} price mismatch: computed {computed_total} != stated {stated_total}"
    )
