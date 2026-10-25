"""Intent Schema v1 for Lajur Voice Ordering System.

Defines all structured intents that an LLM Semantic Parser may propose.
All models use ConfigDict(extra="forbid") ensuring no financial fields
(price, total, discount, etc.) can be received.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class BaseIntent(BaseModel):
    """Base class for all intents with strict forbidden extra fields."""

    model_config = ConfigDict(extra="forbid")


class AddItemIntent(BaseIntent):
    """Intent to add one or more units of an item or combo to the cart."""

    type: Literal["add_item"] = "add_item"
    item_id: str = Field(description="Canonical ID of the menu item or combo")
    quantity: int = Field(default=1, ge=1, description="Quantity to add (minimum 1)")
    size: Literal["regular", "medium", "large"] = Field(
        default="regular", description="Size variant"
    )
    modifiers: list[str] = Field(
        default_factory=list, description="List of chosen modifier option IDs"
    )
    slot_choices: dict[str, str] = Field(
        default_factory=dict, description="Combo slot_id -> chosen item_id"
    )
    upsell_rules: list[str] = Field(
        default_factory=list, description="Applied combo upsell rule IDs"
    )


class RemoveItemIntent(BaseIntent):
    """Intent to remove an item or reduce its quantity."""

    type: Literal["remove_item"] = "remove_item"
    line_id: str | None = Field(default=None, description="Specific cart line_id to remove from")
    item_id: str | None = Field(
        default=None, description="Item ID to match if line_id is not specified"
    )
    quantity: int | None = Field(
        default=None,
        ge=1,
        description="Quantity to remove. If None or >= line quantity, removes the whole line.",
    )


class ModifyItemIntent(BaseIntent):
    """Intent to modify size, modifiers, or quantity of an existing cart line."""

    type: Literal["modify_item"] = "modify_item"
    line_id: str | None = Field(default=None, description="Target cart line_id to modify")
    item_id: str | None = Field(
        default=None, description="Target item_id if line_id is not specified"
    )
    quantity: int | None = Field(
        default=None, ge=1, description="New quantity if changing quantity"
    )
    size: Literal["regular", "medium", "large"] | None = Field(
        default=None, description="New size variant if changing size"
    )
    add_modifiers: list[str] = Field(default_factory=list, description="Modifier option IDs to add")
    remove_modifiers: list[str] = Field(
        default_factory=list, description="Modifier option IDs to remove"
    )
    slot_choices: dict[str, str] = Field(
        default_factory=dict, description="Combo slot_id -> new chosen item_id"
    )
    add_upsell_rules: list[str] = Field(
        default_factory=list, description="Combo upsell rule IDs to apply"
    )
    remove_upsell_rules: list[str] = Field(
        default_factory=list, description="Combo upsell rule IDs to remove"
    )


class ReplaceItemIntent(BaseIntent):
    """Intent to swap an existing cart line with a different menu item."""

    type: Literal["replace_item"] = "replace_item"
    target_line_id: str | None = Field(
        default=None, description="Cart line_id of the item being replaced"
    )
    target_item_id: str | None = Field(
        default=None, description="Item ID of the item being replaced if line_id not specified"
    )
    replacement_item_id: str = Field(description="Canonical ID of the replacement menu item")
    quantity: int = Field(default=1, ge=1, description="Quantity for the replacement item")
    size: Literal["regular", "medium", "large"] = Field(
        default="regular", description="Size variant for replacement item"
    )
    modifiers: list[str] = Field(default_factory=list, description="Modifiers for replacement item")
    slot_choices: dict[str, str] = Field(
        default_factory=dict, description="Combo slots if replacement is a combo"
    )
    upsell_rules: list[str] = Field(
        default_factory=list, description="Combo upsell rule IDs if replacement is a combo"
    )


class UndoLastIntent(BaseIntent):
    """Intent to undo the last conversational ordering action."""

    type: Literal["undo_last"] = "undo_last"


class ClearCartIntent(BaseIntent):
    """Intent to empty all items from the current cart."""

    type: Literal["clear_cart"] = "clear_cart"


class AnswerChoiceIntent(BaseIntent):
    """Intent providing an answer to a pending choice (combo slot or required modifier)."""

    type: Literal["answer_choice"] = "answer_choice"
    choice_id: str = Field(description="Chosen item_id, modifier option_id, or line_id")
    slot_id: str | None = Field(
        default=None, description="Slot ID being answered if answering a combo slot"
    )
    line_id: str | None = Field(
        default=None, description="Line ID being disambiguated if resolving ambiguity"
    )


class ConfirmIntent(BaseIntent):
    """Intent confirming the order is complete and ready for checkout."""

    type: Literal["confirm"] = "confirm"
    payment_method: str | None = Field(
        default=None, description="Optional payment method mentioned by customer"
    )


class DeclineMoreIntent(BaseIntent):
    """Intent declining further items or upsell offers (e.g. 'itu aja', 'cukup')."""

    type: Literal["decline_more"] = "decline_more"


class HandoffIntent(BaseIntent):
    """Intent requesting immediate escalation to a human drive-thru crew member."""

    type: Literal["handoff"] = "handoff"
    reason: str = Field(
        default="customer_requested", description="Reason for transferring to human"
    )


class AskInfoIntent(BaseIntent):
    """Intent asking for menu, price, breakfast hours, or ingredient information."""

    type: Literal["ask_info"] = "ask_info"
    query_type: str = Field(
        default="general",
        description="Type of question (e.g. 'operating_hours', 'ingredients', 'price', 'menu')",
    )
    target_item_id: str | None = Field(
        default=None, description="Target item mentioned in the question"
    )


class UnknownIntent(BaseIntent):
    """Fallback intent when utterance is unparseable, out-of-domain, or chit-chat."""

    type: Literal["unknown"] = "unknown"
    raw_text: str = Field(default="", description="Raw transcript of the utterance")
    reason: str = Field(default="unrecognized", description="Reason why intent could not be parsed")


Intent = Annotated[
    Union[
        AddItemIntent,
        RemoveItemIntent,
        ModifyItemIntent,
        ReplaceItemIntent,
        UndoLastIntent,
        ClearCartIntent,
        AnswerChoiceIntent,
        ConfirmIntent,
        DeclineMoreIntent,
        HandoffIntent,
        AskInfoIntent,
        UnknownIntent,
    ],
    Field(discriminator="type"),
]


class IntentEnvelope(BaseModel):
    """Top-level envelope returned by the semantic intent parser."""

    model_config = ConfigDict(extra="forbid")

    intents: list[Intent] = Field(
        default_factory=list, description="Sequence of structured intents parsed from utterance"
    )
    customer_language: Literal["id", "en", "mixed"] = Field(
        default="id", description="Detected language blend"
    )


def export_intent_json_schema(target_path: Path | str | None = None) -> dict:
    """Export the Pydantic IntentEnvelope schema to a JSON Schema file."""
    schema = IntentEnvelope.model_json_schema()
    if target_path is not None:
        p = Path(target_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    return schema


if __name__ == "__main__":
    schema_path = Path(__file__).resolve().parents[2] / "intent.schema.json"
    export_intent_json_schema(schema_path)
    print(f"Exported JSON Schema to {schema_path}")
