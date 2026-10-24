"""Unit tests for Intent Schema v1 and JSON Schema export (§13, ADR-0002)."""

import json
from pathlib import Path

import jsonschema
import pytest
from lajur_cart.intents import (
    AddItemIntent,
    IntentEnvelope,
    RemoveItemIntent,
    export_intent_json_schema,
)
from pydantic import ValidationError


@pytest.fixture
def schema_path(tmp_path: Path) -> Path:
    target = tmp_path / "intent.schema.json"
    export_intent_json_schema(target)
    return target


@pytest.fixture
def schema_dict(schema_path: Path) -> dict:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def test_schema_file_exported_and_valid():
    repo_schema = Path("packages/cart/intent.schema.json")
    assert repo_schema.exists(), "intent.schema.json must exist in packages/cart"
    data = json.loads(repo_schema.read_text(encoding="utf-8"))
    assert "properties" in data
    assert "intents" in data["properties"]


def test_valid_sample_intents(schema_dict: dict):
    samples = [
        {
            "type": "add_item",
            "item_id": "burger_sapi_tunggal",
            "quantity": 1,
            "size": "regular",
            "modifiers": [],
            "slot_choices": {},
        },
        {
            "type": "remove_item",
            "line_id": "line_1",
            "item_id": "burger_sapi_tunggal",
            "quantity": 1,
        },
        {
            "type": "modify_item",
            "line_id": "line_1",
            "size": "large",
            "add_modifiers": ["opt_no_ice"],
        },
        {
            "type": "replace_item",
            "target_line_id": "line_1",
            "replacement_item_id": "nasi_putih",
            "quantity": 1,
        },
        {"type": "undo_last"},
        {"type": "clear_cart"},
        {"type": "answer_choice", "choice_id": "coca_cola", "slot_id": "drink"},
        {"type": "confirm", "payment_method": "cash"},
        {"type": "decline_more"},
        {"type": "handoff", "reason": "customer_requested"},
        {"type": "ask_info", "query_type": "operating_hours", "target_item_id": "bubur_ayam"},
        {"type": "unknown", "raw_text": "halo halo", "reason": "unrecognized"},
    ]

    for sample in samples:
        envelope_data = {"intents": [sample], "customer_language": "id"}
        # 1. Pydantic validation
        env = IntentEnvelope.model_validate(envelope_data)
        assert len(env.intents) == 1
        assert env.intents[0].type == sample["type"]

        # 2. jsonschema validation
        jsonschema.validate(instance=envelope_data, schema=schema_dict)


def test_financial_fields_strictly_forbidden(schema_dict: dict):
    """Ensure no intent or envelope can accept price, discount, or total fields."""
    forbidden_payloads = [
        {"type": "add_item", "item_id": "burger_sapi_tunggal", "price": 0},
        {"type": "add_item", "item_id": "burger_sapi_tunggal", "total_price": 1000},
        {"type": "add_item", "item_id": "burger_sapi_tunggal", "discount": 0.5},
        {"type": "confirm", "total": 0},
        {"type": "modify_item", "line_id": "line_1", "price": 5000},
    ]

    for payload in forbidden_payloads:
        # Pydantic must reject with extra field error
        with pytest.raises(ValidationError):
            IntentEnvelope.model_validate({"intents": [payload]})

        # jsonschema must reject
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance={"intents": [payload]}, schema=schema_dict)


def test_invalid_quantities_and_sizes():
    with pytest.raises(ValidationError):
        AddItemIntent(item_id="burger_sapi_tunggal", quantity=0)

    with pytest.raises(ValidationError):
        AddItemIntent(item_id="burger_sapi_tunggal", size="extra_large")  # type: ignore

    with pytest.raises(ValidationError):
        RemoveItemIntent(quantity=-1)
