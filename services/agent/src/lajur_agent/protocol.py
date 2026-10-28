"""Lajur Web Protocol v1 Message Serialization and Helper Functions.

Implements the data-channel contract defined in docs/design/web-protocol.md
and packages/cart/web-protocol.schema.json.
"""

from __future__ import annotations

import time
from typing import Any

from lajur_cart.menu_service import MenuService
from lajur_cart.models import Cart
from lajur_cart.state_machine import DialogState, PendingChoice, SpeechFacts

PROTOCOL_VERSION = "v1"


def create_partial_transcript_event(text: str, timestamp_ms: float | None = None) -> dict[str, Any]:
    """Emit streaming interim transcript as user speaks."""
    return {
        "version": PROTOCOL_VERSION,
        "type": "partial_transcript",
        "text": text,
        "is_final": False,
        "timestamp_ms": timestamp_ms
        if timestamp_ms is not None
        else round(time.time() * 1000.0, 1),
    }


def create_final_transcript_event(text: str, timestamp_ms: float | None = None) -> dict[str, Any]:
    """Emit confirmed transcript once speech_final endpointing triggers."""
    return {
        "version": PROTOCOL_VERSION,
        "type": "final_transcript",
        "text": text,
        "is_final": True,
        "timestamp_ms": timestamp_ms
        if timestamp_ms is not None
        else round(time.time() * 1000.0, 1),
    }


def create_intent_applied_event(
    state: DialogState,
    cart: Cart,
    speech_facts: SpeechFacts,
    menu_service: MenuService | None = None,
    state_from: DialogState | None = None,
    timestamp_ms: float | None = None,
) -> dict[str, Any]:
    """Emit validated cart snapshot with line ids, item details, and speech facts."""
    items_list = []
    for line in cart.items:
        name_id = line.item_id
        name_en = line.item_id
        unit_price = line.price // line.quantity if line.quantity > 0 else line.price

        if menu_service:
            if line.item_id in menu_service.items:
                mi = menu_service.items[line.item_id]
                name_id = mi.name_id
                name_en = mi.name_en
            elif line.item_id in menu_service.combos:
                mc = menu_service.combos[line.item_id]
                name_id = mc.name_id
                name_en = mc.name_en

        items_list.append(
            {
                "line_id": line.line_id,
                "item_id": line.item_id,
                "name_id": name_id,
                "name_en": name_en,
                "quantity": line.quantity,
                "size": line.size,
                "unit_price": unit_price,
                "price": line.price,
                "modifiers": line.modifiers,
                "slots": line.slots,
                "upsell_rules": line.upsell_rules,
            }
        )

    cart_dict = {
        "items": items_list,
        "total_price": cart.total_price,
        "total_item_count": cart.total_item_count,
        "status": cart.status,
    }

    event: dict[str, Any] = {
        "version": PROTOCOL_VERSION,
        "type": "intent_applied",
        "state": state,
        "cart": cart_dict,
        "speech_facts": speech_facts.model_dump(),
        "timestamp_ms": timestamp_ms
        if timestamp_ms is not None
        else round(time.time() * 1000.0, 1),
    }
    if state_from:
        event["state_from"] = state_from

    return event


def create_bot_reply_text_event(text: str, timestamp_ms: float | None = None) -> dict[str, Any]:
    """Emit the spoken reply text alongside the audio."""
    return {
        "version": PROTOCOL_VERSION,
        "type": "bot_reply_text",
        "text": text,
        "timestamp_ms": timestamp_ms
        if timestamp_ms is not None
        else round(time.time() * 1000.0, 1),
    }


def create_bot_speaking_start_event(timestamp_ms: float | None = None) -> dict[str, Any]:
    """Emit when bot begins playing audio."""
    return {
        "version": PROTOCOL_VERSION,
        "type": "bot_speaking_start",
        "timestamp_ms": timestamp_ms
        if timestamp_ms is not None
        else round(time.time() * 1000.0, 1),
    }


def create_bot_speaking_end_event(timestamp_ms: float | None = None) -> dict[str, Any]:
    """Emit when bot finishes playing audio."""
    return {
        "version": PROTOCOL_VERSION,
        "type": "bot_speaking_end",
        "timestamp_ms": timestamp_ms
        if timestamp_ms is not None
        else round(time.time() * 1000.0, 1),
    }


def create_pending_question_event(
    pending_choice: PendingChoice,
    menu_service: MenuService | None = None,
    timestamp_ms: float | None = None,
) -> dict[str, Any]:
    """Emit when dialog transitions to awaiting_choice."""
    choices_meta = []
    if menu_service:
        for cid in pending_choice.allowed_choices:
            if cid in menu_service.items:
                item = menu_service.items[cid]
                choices_meta.append(
                    {
                        "id": cid,
                        "name_id": item.name_id,
                        "name_en": item.name_en,
                        "price_delta": 0,
                    }
                )
            else:
                choices_meta.append(
                    {
                        "id": cid,
                        "name_id": cid.replace("_", " ").title(),
                        "name_en": cid.replace("_", " ").title(),
                        "price_delta": 0,
                    }
                )

    return {
        "version": PROTOCOL_VERSION,
        "type": "pending_question",
        "kind": pending_choice.type,
        "prompt": pending_choice.prompt,
        "target_line_id": pending_choice.target_line_id,
        "slot_id": pending_choice.slot_id,
        "allowed_choices": pending_choice.allowed_choices,
        "choices": choices_meta if choices_meta else None,
        "timestamp_ms": timestamp_ms
        if timestamp_ms is not None
        else round(time.time() * 1000.0, 1),
    }


def create_handoff_event(
    reason: str,
    crew_message: str = "Mohon tunggu sebentar ya kak, kasir manusia kami akan segera melayani Anda.",
    timestamp_ms: float | None = None,
) -> dict[str, Any]:
    """Emit when handoff to human crew occurs."""
    return {
        "version": PROTOCOL_VERSION,
        "type": "handoff",
        "reason": reason,
        "crew_message": crew_message,
        "timestamp_ms": timestamp_ms
        if timestamp_ms is not None
        else round(time.time() * 1000.0, 1),
    }


def create_error_event(
    code: str,
    message: str,
    recoverable: bool = True,
    timestamp_ms: float | None = None,
) -> dict[str, Any]:
    """Emit structured error message."""
    return {
        "version": PROTOCOL_VERSION,
        "type": "error",
        "code": code,
        "message": message,
        "recoverable": recoverable,
        "timestamp_ms": timestamp_ms
        if timestamp_ms is not None
        else round(time.time() * 1000.0, 1),
    }


def create_session_limits_event(
    turns_used: int,
    max_turns: int = 12,
    time_elapsed_seconds: float = 0.0,
    time_limit_seconds: float = 180.0,
    timestamp_ms: float | None = None,
) -> dict[str, Any]:
    """Emit session limits telemetry (turns and duration)."""
    return {
        "version": PROTOCOL_VERSION,
        "type": "session_limits",
        "turns_used": turns_used,
        "max_turns": max_turns,
        "time_elapsed_seconds": round(time_elapsed_seconds, 1),
        "time_limit_seconds": round(time_limit_seconds, 1),
        "timestamp_ms": timestamp_ms
        if timestamp_ms is not None
        else round(time.time() * 1000.0, 1),
    }
