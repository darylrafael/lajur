"""Pure, deterministic Cart State Machine for Lajur (§6, §8, ADR-0002).

This module contains:
- DialogState enum / literal
- Rejection, PendingChoice, CartEvent, SpeechFacts domain models
- StateMachineResult
- Pure apply_intent() transition function
- Stateful CartSession wrapper for conversational sessions and testing
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from datetime import time
from typing import Any, Literal

from pydantic import BaseModel, Field

from lajur_cart.intents import (
    AddItemIntent,
    AnswerChoiceIntent,
    AskInfoIntent,
    ClearCartIntent,
    ConfirmIntent,
    DeclineMoreIntent,
    HandoffIntent,
    Intent,
    ModifyItemIntent,
    RemoveItemIntent,
    ReplaceItemIntent,
    UndoLastIntent,
    UnknownIntent,
)
from lajur_cart.menu_service import MenuService
from lajur_cart.models import Cart, CartLine, Combo, Item

DialogState = Literal["ordering", "awaiting_choice", "confirming", "done", "handoff"]


class Rejection(BaseModel):
    """Structured rejection details when an intent cannot be applied."""

    code: str = Field(description="Machine-readable rejection code")
    message: str = Field(description="Human-readable explanation in Indonesian")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional context payload")


class PendingChoice(BaseModel):
    """Represents a choice required from the customer before proceeding."""

    type: Literal["combo_slot", "required_modifier", "ambiguity"] = Field(
        description="Category of choice pending"
    )
    target_line_id: str | None = Field(
        default=None, description="Line ID being configured or clarified"
    )
    slot_id: str | None = Field(default=None, description="Slot ID if filling a combo slot")
    prompt: str = Field(description="Prompt describing the required choice")
    allowed_choices: list[str] = Field(default_factory=list, description="List of valid choice IDs")


class CartEvent(BaseModel):
    """Domain event recording what changed during state machine execution."""

    event_type: str
    details: dict[str, Any] = Field(default_factory=dict)


class SpeechFacts(BaseModel):
    """Structured facts generated for downstream reply / speech generation."""

    intent_handled: str
    items_added: list[dict[str, Any]] = Field(default_factory=list)
    items_removed: list[dict[str, Any]] = Field(default_factory=list)
    items_modified: list[dict[str, Any]] = Field(default_factory=list)
    items_replaced: list[dict[str, Any]] = Field(default_factory=list)
    pending_prompt: PendingChoice | None = None
    rejections: list[Rejection] = Field(default_factory=list)
    cart_item_count: int = 0
    cart_total_price: int = 0
    dialog_state: DialogState = "ordering"
    requires_confirmation: bool = False


class StateMachineResult(BaseModel):
    """Complete output of a single state transition."""

    new_state: DialogState
    cart: Cart
    events: list[CartEvent] = Field(default_factory=list)
    rejections: list[Rejection] = Field(default_factory=list)
    speech_facts: SpeechFacts
    pending_choice: PendingChoice | None = None


class StateContext:
    """Injected context for state machine evaluation."""

    def __init__(self, clock: Callable[[], time] | None = None):
        self._clock = clock if clock is not None else (lambda: time(12, 0))

    @property
    def current_time(self) -> time:
        return self._clock()


def _generate_line_id(cart: Cart) -> str:
    """Generates a stable sequential line ID not present in current cart."""
    existing_ids = {item.line_id for item in cart.items if item.line_id}
    counter = len(cart.items) + 1
    while f"line_{counter}" in existing_ids:
        counter += 1
    return f"line_{counter}"


def _find_matching_lines(cart: Cart, line_id: str | None, item_id: str | None) -> list[CartLine]:
    """Finds lines in cart matching line_id or item_id."""
    if line_id:
        return [line for line in cart.items if line.line_id == line_id]
    if item_id:
        return [line for line in cart.items if line.item_id == item_id]
    return []


def apply_intent(
    current_state: DialogState,
    cart: Cart,
    intent: Intent,
    menu_service: MenuService,
    context: StateContext | None = None,
    history: list[Cart] | None = None,
    pending_choice: PendingChoice | None = None,
) -> tuple[StateMachineResult, list[Cart], PendingChoice | None]:
    """Pure function executing a single deterministic state machine transition.

    Returns:
        tuple of (StateMachineResult, updated_history, updated_pending_choice)
    """
    ctx = context or StateContext()
    hist = list(history) if history is not None else []
    p_choice = copy.deepcopy(pending_choice)
    new_cart = copy.deepcopy(cart)
    events: list[CartEvent] = []
    rejections: list[Rejection] = []
    new_state: DialogState = current_state

    # 1. Terminal State Handling
    if current_state == "done":
        if isinstance(intent, ConfirmIntent):
            facts = SpeechFacts(
                intent_handled="confirm",
                cart_item_count=new_cart.total_item_count,
                cart_total_price=new_cart.total_price,
                dialog_state="done",
            )
            return (
                StateMachineResult(
                    new_state="done",
                    cart=new_cart,
                    events=events,
                    rejections=[],
                    speech_facts=facts,
                    pending_choice=None,
                ),
                hist,
                None,
            )
        rejections.append(
            Rejection(
                code="ORDER_ALREADY_COMPLETED",
                message="Pesanan sudah selesai dikonfirmasi.",
                details={"intent": intent.type},
            )
        )
        facts = SpeechFacts(
            intent_handled=intent.type,
            rejections=rejections,
            cart_item_count=new_cart.total_item_count,
            cart_total_price=new_cart.total_price,
            dialog_state="done",
        )
        return (
            StateMachineResult(
                new_state="done",
                cart=new_cart,
                events=events,
                rejections=rejections,
                speech_facts=facts,
                pending_choice=None,
            ),
            hist,
            None,
        )

    if current_state == "handoff":
        rejections.append(
            Rejection(
                code="SESSION_HANDED_OFF",
                message="Sesi telah dialihkan ke kasir manusia.",
                details={"intent": intent.type},
            )
        )
        facts = SpeechFacts(
            intent_handled=intent.type,
            rejections=rejections,
            cart_item_count=new_cart.total_item_count,
            cart_total_price=new_cart.total_price,
            dialog_state="handoff",
        )
        return (
            StateMachineResult(
                new_state="handoff",
                cart=new_cart,
                events=events,
                rejections=rejections,
                speech_facts=facts,
                pending_choice=None,
            ),
            hist,
            None,
        )

    # 2. Universal Handoff Intent
    if isinstance(intent, HandoffIntent):
        new_state = "handoff"
        new_cart.status = "handoff"
        events.append(CartEvent(event_type="HandoffTriggered", details={"reason": intent.reason}))
        facts = SpeechFacts(
            intent_handled="handoff",
            cart_item_count=new_cart.total_item_count,
            cart_total_price=new_cart.total_price,
            dialog_state="handoff",
        )
        return (
            StateMachineResult(
                new_state="handoff",
                cart=new_cart,
                events=events,
                rejections=rejections,
                speech_facts=facts,
                pending_choice=None,
            ),
            hist,
            None,
        )

    # 3. Universal Undo Last Intent
    if isinstance(intent, UndoLastIntent):
        if not hist:
            rejections.append(
                Rejection(
                    code="NOTHING_TO_UNDO",
                    message="Tidak ada tindakan sebelumnya untuk dibatalkan.",
                )
            )
            facts = SpeechFacts(
                intent_handled="undo_last",
                rejections=rejections,
                cart_item_count=new_cart.total_item_count,
                cart_total_price=new_cart.total_price,
                dialog_state=current_state,
            )
            return (
                StateMachineResult(
                    new_state=current_state,
                    cart=new_cart,
                    events=events,
                    rejections=rejections,
                    speech_facts=facts,
                    pending_choice=p_choice,
                ),
                hist,
                p_choice,
            )
        previous_cart = hist.pop()
        new_cart = copy.deepcopy(previous_cart)
        new_state = "ordering"
        p_choice = None
        events.append(
            CartEvent(
                event_type="StateRolledBack",
                details={
                    "total_items": new_cart.total_item_count,
                    "total_price": new_cart.total_price,
                },
            )
        )
        facts = SpeechFacts(
            intent_handled="undo_last",
            cart_item_count=new_cart.total_item_count,
            cart_total_price=new_cart.total_price,
            dialog_state=new_state,
        )
        return (
            StateMachineResult(
                new_state=new_state,
                cart=new_cart,
                events=events,
                rejections=rejections,
                speech_facts=facts,
                pending_choice=None,
            ),
            hist,
            None,
        )

    # 4. Universal Clear Cart Intent
    if isinstance(intent, ClearCartIntent):
        hist.append(copy.deepcopy(cart))
        new_cart.items = []
        new_cart.total_price = 0
        new_cart.status = "empty"
        new_state = "ordering"
        p_choice = None
        events.append(CartEvent(event_type="CartCleared"))
        facts = SpeechFacts(
            intent_handled="clear_cart",
            cart_item_count=0,
            cart_total_price=0,
            dialog_state="ordering",
        )
        return (
            StateMachineResult(
                new_state="ordering",
                cart=new_cart,
                events=events,
                rejections=rejections,
                speech_facts=facts,
                pending_choice=None,
            ),
            hist,
            None,
        )

    # 5. Informational Intent
    if isinstance(intent, AskInfoIntent):
        if new_cart.total_item_count == 0:
            new_cart.status = "empty"
        facts = SpeechFacts(
            intent_handled="ask_info",
            cart_item_count=new_cart.total_item_count,
            cart_total_price=new_cart.total_price,
            dialog_state=current_state,
        )
        return (
            StateMachineResult(
                new_state=current_state,
                cart=new_cart,
                events=events,
                rejections=rejections,
                speech_facts=facts,
                pending_choice=p_choice,
            ),
            hist,
            p_choice,
        )

    # 6. Unknown Intent
    if isinstance(intent, UnknownIntent):
        if intent.reason in ("adversarial_prompt_or_prank", "prompt_injection", "abusive_request"):
            rejections.append(
                Rejection(
                    code="ADVERSARIAL_PROMPT",
                    message="Permintaan tidak dapat diproses.",
                    details={"raw_text": intent.raw_text, "reason": intent.reason},
                )
            )
            if new_cart.total_item_count == 0:
                new_cart.status = "rejected"
        else:
            if new_cart.total_item_count == 0:
                new_cart.status = "empty"

        facts = SpeechFacts(
            intent_handled="unknown",
            rejections=rejections,
            cart_item_count=new_cart.total_item_count,
            cart_total_price=new_cart.total_price,
            dialog_state=current_state,
        )
        return (
            StateMachineResult(
                new_state=current_state,
                cart=new_cart,
                events=events,
                rejections=rejections,
                speech_facts=facts,
                pending_choice=p_choice,
            ),
            hist,
            p_choice,
        )

    # 7. State: awaiting_choice Guard
    if current_state == "awaiting_choice" and not isinstance(intent, AnswerChoiceIntent):
        rejections.append(
            Rejection(
                code="CHOICE_REQUIRED",
                message="Silakan selesaikan pilihan yang sedang ditunggu terlebih dahulu.",
                details={"pending_prompt": p_choice.model_dump() if p_choice else None},
            )
        )
        facts = SpeechFacts(
            intent_handled=intent.type,
            rejections=rejections,
            pending_prompt=p_choice,
            cart_item_count=new_cart.total_item_count,
            cart_total_price=new_cart.total_price,
            dialog_state="awaiting_choice",
        )
        return (
            StateMachineResult(
                new_state="awaiting_choice",
                cart=new_cart,
                events=events,
                rejections=rejections,
                speech_facts=facts,
                pending_choice=p_choice,
            ),
            hist,
            p_choice,
        )

    # 8. Handling AnswerChoiceIntent
    if isinstance(intent, AnswerChoiceIntent):
        if current_state != "awaiting_choice" or p_choice is None:
            rejections.append(
                Rejection(
                    code="UNEXPECTED_CHOICE",
                    message="Tidak ada pilihan yang sedang ditunggu saat ini.",
                )
            )
            facts = SpeechFacts(
                intent_handled="answer_choice",
                rejections=rejections,
                cart_item_count=new_cart.total_item_count,
                cart_total_price=new_cart.total_price,
                dialog_state=current_state,
            )
            return (
                StateMachineResult(
                    new_state=current_state,
                    cart=new_cart,
                    events=events,
                    rejections=rejections,
                    speech_facts=facts,
                    pending_choice=p_choice,
                ),
                hist,
                p_choice,
            )

        # Process choice for combo slot
        if p_choice.type == "combo_slot":
            line = next(
                (item for item in new_cart.items if item.line_id == p_choice.target_line_id), None
            )
            if not line:
                rejections.append(
                    Rejection(
                        code="ITEM_NOT_IN_CART",
                        message="Baris pesanan combo tidak ditemukan.",
                    )
                )
            elif intent.choice_id not in p_choice.allowed_choices:
                rejections.append(
                    Rejection(
                        code="INVALID_CHOICE",
                        message=f"Pilihan '{intent.choice_id}' tidak valid untuk slot ini.",
                        details={"allowed": p_choice.allowed_choices},
                    )
                )
            else:
                hist.append(copy.deepcopy(cart))
                slot_id: str | None = p_choice.slot_id or (
                    next(iter(line.slots.keys())) if line.slots else None
                )
                if slot_id:
                    line.slots[slot_id] = intent.choice_id

                # Check if combo still has required slots missing
                combo = menu_service.get_item_or_combo(line.item_id)
                next_missing_slot = None
                if isinstance(combo, Combo):
                    for s in combo.slots:
                        if s.required and not line.slots.get(s.slot_id):
                            next_missing_slot = s
                            break

                if next_missing_slot:
                    p_choice = PendingChoice(
                        type="combo_slot",
                        target_line_id=line.line_id,
                        slot_id=next_missing_slot.slot_id,
                        prompt=f"Pilihan untuk {next_missing_slot.name_id} apa kak?",
                        allowed_choices=next_missing_slot.choice_items,
                    )
                    new_state = "awaiting_choice"
                else:
                    p_choice = None
                    new_state = "ordering"

                menu_service.calculate_cart_total(new_cart)
                events.append(
                    CartEvent(
                        event_type="ChoiceAnswered",
                        details={"line_id": line.line_id, "choice": intent.choice_id},
                    )
                )

        # Process choice for disambiguation
        elif p_choice.type == "ambiguity":
            if intent.choice_id not in p_choice.allowed_choices:
                rejections.append(
                    Rejection(
                        code="INVALID_CHOICE",
                        message=f"Baris '{intent.choice_id}' tidak valid untuk dipilih.",
                        details={"allowed": p_choice.allowed_choices},
                    )
                )
            else:
                p_choice = None
                new_state = "ordering"

        facts = SpeechFacts(
            intent_handled="answer_choice",
            pending_prompt=p_choice,
            rejections=rejections,
            cart_item_count=new_cart.total_item_count,
            cart_total_price=new_cart.total_price,
            dialog_state=new_state,
        )
        return (
            StateMachineResult(
                new_state=new_state,
                cart=new_cart,
                events=events,
                rejections=rejections,
                speech_facts=facts,
                pending_choice=p_choice,
            ),
            hist,
            p_choice,
        )

    # 9. Handling Confirm & DeclineMore
    if isinstance(intent, ConfirmIntent):
        if new_cart.total_item_count == 0:
            rejections.append(
                Rejection(
                    code="EMPTY_CART_CONFIRM",
                    message="Keranjang belanja masih kosong, belum bisa konfirmasi.",
                )
            )
            facts = SpeechFacts(
                intent_handled="confirm",
                rejections=rejections,
                cart_item_count=0,
                cart_total_price=0,
                dialog_state=current_state,
            )
            return (
                StateMachineResult(
                    new_state=current_state,
                    cart=new_cart,
                    events=events,
                    rejections=rejections,
                    speech_facts=facts,
                    pending_choice=p_choice,
                ),
                hist,
                p_choice,
            )

        if current_state in ("ordering", "confirming"):
            new_state = "done"
            new_cart.status = "confirmed"
            events.append(CartEvent(event_type="OrderConfirmed"))
            facts = SpeechFacts(
                intent_handled="confirm",
                cart_item_count=new_cart.total_item_count,
                cart_total_price=new_cart.total_price,
                dialog_state="done",
            )
            return (
                StateMachineResult(
                    new_state="done",
                    cart=new_cart,
                    events=events,
                    rejections=rejections,
                    speech_facts=facts,
                    pending_choice=None,
                ),
                hist,
                None,
            )

    if isinstance(intent, DeclineMoreIntent):
        if new_cart.total_item_count == 0:
            facts = SpeechFacts(
                intent_handled="decline_more",
                cart_item_count=0,
                cart_total_price=0,
                dialog_state="ordering",
            )
            return (
                StateMachineResult(
                    new_state="ordering",
                    cart=new_cart,
                    events=events,
                    rejections=rejections,
                    speech_facts=facts,
                    pending_choice=None,
                ),
                hist,
                None,
            )
        new_state = "confirming"
        facts = SpeechFacts(
            intent_handled="decline_more",
            cart_item_count=new_cart.total_item_count,
            cart_total_price=new_cart.total_price,
            dialog_state="confirming",
            requires_confirmation=True,
        )
        return (
            StateMachineResult(
                new_state="confirming",
                cart=new_cart,
                events=events,
                rejections=rejections,
                speech_facts=facts,
                pending_choice=None,
            ),
            hist,
            None,
        )

    # 10. Handling AddItemIntent
    if isinstance(intent, AddItemIntent):
        target = menu_service.get_item_or_combo(intent.item_id)
        if not target:
            rejections.append(
                Rejection(
                    code="UNKNOWN_ITEM",
                    message=f"Menu dengan ID '{intent.item_id}' tidak ditemukan.",
                    details={"item_id": intent.item_id},
                )
            )
        elif not menu_service.is_in_stock(target):
            rejections.append(
                Rejection(
                    code="OUT_OF_STOCK",
                    message=f"Item '{target.name_id}' saat ini sedang habis.",
                    details={"item_id": intent.item_id},
                )
            )
        elif not menu_service.is_item_available(target, current_time=ctx.current_time):
            rejections.append(
                Rejection(
                    code="OUT_OF_HOURS",
                    message=f"Item '{target.name_id}' tidak tersedia pada jam operasional saat ini.",
                    details={"item_id": intent.item_id, "available_hours": target.available_hours},
                )
            )
        elif new_cart.total_item_count + intent.quantity > 20:
            rejections.append(
                Rejection(
                    code="CAP_EXCEEDED",
                    message=f"Pesanan melebihi batas maksimal 20 item (saat ini: {new_cart.total_item_count}, diminta: +{intent.quantity}).",
                    details={
                        "current_count": new_cart.total_item_count,
                        "attempted_add": intent.quantity,
                    },
                )
            )
        else:
            # Validate modifiers if regular Item
            valid_modifiers = list(intent.modifiers)
            if isinstance(target, Item):
                if intent.size != "regular":
                    valid_sizes = [s.size for s in target.sizes]
                    if intent.size not in valid_sizes:
                        rejections.append(
                            Rejection(
                                code="INVALID_SIZE",
                                message=f"Ukuran '{intent.size}' tidak tersedia untuk item '{target.name_id}'.",
                            )
                        )
                # Check modifier groups
                for mod_opt_id in intent.modifiers:
                    is_valid = any(
                        mod_opt_id in [o.id for o in menu_service.modifiers[m_id].options]
                        for m_id in target.modifiers
                        if m_id in menu_service.modifiers
                    )
                    if not is_valid:
                        rejections.append(
                            Rejection(
                                code="INVALID_MODIFIER",
                                message=f"Pilihan modifier '{mod_opt_id}' tidak berlaku untuk '{target.name_id}'.",
                            )
                        )

            if not rejections:
                hist.append(copy.deepcopy(cart))
                line_id = _generate_line_id(new_cart)
                new_line = CartLine(
                    line_id=line_id,
                    item_id=intent.item_id,
                    quantity=intent.quantity,
                    size=intent.size,
                    modifiers=valid_modifiers,
                    slots=dict(intent.slot_choices),
                    upsell_rules=list(intent.upsell_rules),
                )
                new_cart.items.append(new_line)

                # Check if combo has missing required slots
                if isinstance(target, Combo):
                    missing_slot = next(
                        (
                            s
                            for s in target.slots
                            if s.required and not new_line.slots.get(s.slot_id)
                        ),
                        None,
                    )
                    if missing_slot:
                        p_choice = PendingChoice(
                            type="combo_slot",
                            target_line_id=line_id,
                            slot_id=missing_slot.slot_id,
                            prompt=f"Pilihan untuk {missing_slot.name_id} apa kak?",
                            allowed_choices=missing_slot.choice_items,
                        )
                        new_state = "awaiting_choice"
                    else:
                        new_state = "ordering"
                else:
                    new_state = "ordering"

                menu_service.calculate_cart_total(new_cart)
                events.append(
                    CartEvent(
                        event_type="ItemAdded",
                        details={
                            "line_id": line_id,
                            "item_id": intent.item_id,
                            "quantity": intent.quantity,
                        },
                    )
                )

        if rejections and new_cart.total_item_count == 0:
            new_cart.status = "rejected"

        facts = SpeechFacts(
            intent_handled="add_item",
            items_added=[
                {
                    "item_id": intent.item_id,
                    "quantity": intent.quantity,
                    "size": intent.size,
                    "modifiers": intent.modifiers,
                }
            ]
            if not rejections
            else [],
            pending_prompt=p_choice,
            rejections=rejections,
            cart_item_count=new_cart.total_item_count,
            cart_total_price=new_cart.total_price,
            dialog_state=new_state,
        )
        return (
            StateMachineResult(
                new_state=new_state,
                cart=new_cart,
                events=events,
                rejections=rejections,
                speech_facts=facts,
                pending_choice=p_choice,
            ),
            hist,
            p_choice,
        )

    # 11. Handling RemoveItemIntent
    if isinstance(intent, RemoveItemIntent):
        matching = _find_matching_lines(new_cart, intent.line_id, intent.item_id)
        if len(matching) == 0:
            rejections.append(
                Rejection(
                    code="ITEM_NOT_IN_CART",
                    message="Item yang ingin dihapus tidak ada di dalam keranjang.",
                    details={"line_id": intent.line_id, "item_id": intent.item_id},
                )
            )
        elif len(matching) > 1 and not intent.line_id:
            # Ambiguous reference resolution
            p_choice = PendingChoice(
                type="ambiguity",
                prompt="Ada beberapa pilihan item serupa di keranjang. Yang mana yang ingin dihapus?",
                allowed_choices=[line.line_id for line in matching],
            )
            new_state = "awaiting_choice"
        else:
            target_line = matching[0]
            hist.append(copy.deepcopy(cart))
            rem_qty = intent.quantity
            removed_info: dict[str, Any] = {
                "line_id": target_line.line_id,
                "item_id": target_line.item_id,
            }

            if rem_qty is None or rem_qty >= target_line.quantity:
                new_cart.items = [
                    line for line in new_cart.items if line.line_id != target_line.line_id
                ]
                removed_info["quantity_removed"] = target_line.quantity
            else:
                target_line.quantity -= rem_qty
                removed_info["quantity_removed"] = rem_qty

            menu_service.calculate_cart_total(new_cart)
            events.append(CartEvent(event_type="ItemRemoved", details=removed_info))
            new_state = "ordering"

        facts = SpeechFacts(
            intent_handled="remove_item",
            items_removed=[{"line_id": intent.line_id or (matching[0].line_id if matching else "")}]
            if not rejections and not p_choice
            else [],
            pending_prompt=p_choice,
            rejections=rejections,
            cart_item_count=new_cart.total_item_count,
            cart_total_price=new_cart.total_price,
            dialog_state=new_state,
        )
        return (
            StateMachineResult(
                new_state=new_state,
                cart=new_cart,
                events=events,
                rejections=rejections,
                speech_facts=facts,
                pending_choice=p_choice,
            ),
            hist,
            p_choice,
        )

    # 12. Handling ModifyItemIntent
    if isinstance(intent, ModifyItemIntent):
        matching = _find_matching_lines(new_cart, intent.line_id, intent.item_id)
        if len(matching) == 0:
            rejections.append(
                Rejection(
                    code="ITEM_NOT_IN_CART",
                    message="Item yang ingin diubah tidak ditemukan di dalam keranjang.",
                    details={"line_id": intent.line_id, "item_id": intent.item_id},
                )
            )
        elif len(matching) > 1 and not intent.line_id:
            p_choice = PendingChoice(
                type="ambiguity",
                prompt="Ada beberapa baris item serupa di keranjang. Yang mana yang ingin diubah?",
                allowed_choices=[line.line_id for line in matching],
            )
            new_state = "awaiting_choice"
        else:
            target_line = matching[0]
            menu_target = menu_service.get_item_or_combo(target_line.item_id)
            if not menu_target:
                rejections.append(
                    Rejection(code="UNKNOWN_ITEM", message="Definisi menu tidak ditemukan.")
                )
            else:
                # Check quantity change cap
                if intent.quantity is not None:
                    delta = intent.quantity - target_line.quantity
                    if new_cart.total_item_count + delta > 20:
                        rejections.append(
                            Rejection(
                                code="CAP_EXCEEDED",
                                message="Perubahan kuantitas melebihi batas 20 item per pesanan.",
                            )
                        )

                # Check size
                if intent.size is not None and isinstance(menu_target, Item):
                    if intent.size not in [s.size for s in menu_target.sizes]:
                        rejections.append(
                            Rejection(
                                code="INVALID_SIZE",
                                message=f"Ukuran '{intent.size}' tidak valid untuk '{menu_target.name_id}'.",
                            )
                        )

                if not rejections:
                    hist.append(copy.deepcopy(cart))
                    if intent.quantity is not None:
                        target_line.quantity = intent.quantity
                    if intent.size is not None:
                        target_line.size = intent.size

                    # Modifiers
                    current_mods = set(target_line.modifiers)
                    for m_add in intent.add_modifiers:
                        current_mods.add(m_add)
                    for m_rem in intent.remove_modifiers:
                        current_mods.discard(m_rem)
                    target_line.modifiers = list(current_mods)

                    # Slots
                    if intent.slot_choices:
                        target_line.slots.update(intent.slot_choices)

                    # Upsell rules
                    current_upsells = list(target_line.upsell_rules)
                    for u_add in intent.add_upsell_rules:
                        if u_add not in current_upsells:
                            current_upsells.append(u_add)
                    for u_rem in intent.remove_upsell_rules:
                        if u_rem in current_upsells:
                            current_upsells.remove(u_rem)
                    target_line.upsell_rules = current_upsells

                    menu_service.calculate_cart_total(new_cart)
                    events.append(
                        CartEvent(
                            event_type="ItemModified",
                            details={"line_id": target_line.line_id},
                        )
                    )
                    new_state = "ordering"

        facts = SpeechFacts(
            intent_handled="modify_item",
            items_modified=[
                {"line_id": intent.line_id or (matching[0].line_id if matching else "")}
            ]
            if not rejections and not p_choice
            else [],
            pending_prompt=p_choice,
            rejections=rejections,
            cart_item_count=new_cart.total_item_count,
            cart_total_price=new_cart.total_price,
            dialog_state=new_state,
        )
        return (
            StateMachineResult(
                new_state=new_state,
                cart=new_cart,
                events=events,
                rejections=rejections,
                speech_facts=facts,
                pending_choice=p_choice,
            ),
            hist,
            p_choice,
        )

    # 13. Handling ReplaceItemIntent
    if isinstance(intent, ReplaceItemIntent):
        matching = _find_matching_lines(new_cart, intent.target_line_id, intent.target_item_id)
        replacement_target = menu_service.get_item_or_combo(intent.replacement_item_id)

        if len(matching) == 0:
            rejections.append(
                Rejection(
                    code="ITEM_NOT_IN_CART",
                    message="Item yang ingin diganti tidak ada di dalam keranjang.",
                    details={
                        "target_line_id": intent.target_line_id,
                        "target_item_id": intent.target_item_id,
                    },
                )
            )
        elif not replacement_target:
            rejections.append(
                Rejection(
                    code="UNKNOWN_ITEM",
                    message=f"Item pengganti '{intent.replacement_item_id}' tidak ditemukan di menu.",
                )
            )
        elif not menu_service.is_in_stock(replacement_target):
            rejections.append(
                Rejection(
                    code="OUT_OF_STOCK",
                    message=f"Item pengganti '{replacement_target.name_id}' sedang habis.",
                )
            )
        elif not menu_service.is_item_available(replacement_target, current_time=ctx.current_time):
            rejections.append(
                Rejection(
                    code="OUT_OF_HOURS",
                    message=f"Item pengganti '{replacement_target.name_id}' di luar jam operasional.",
                )
            )
        else:
            target_line = matching[0]
            qty_delta = intent.quantity - target_line.quantity
            if new_cart.total_item_count + qty_delta > 20:
                rejections.append(
                    Rejection(
                        code="CAP_EXCEEDED",
                        message="Penggantian item melebihi batas 20 item per pesanan.",
                    )
                )
            else:
                hist.append(copy.deepcopy(cart))
                # Remove target line
                new_cart.items = [
                    line for line in new_cart.items if line.line_id != target_line.line_id
                ]

                # Add replacement line
                new_line_id = _generate_line_id(new_cart)
                new_line = CartLine(
                    line_id=new_line_id,
                    item_id=intent.replacement_item_id,
                    quantity=intent.quantity,
                    size=intent.size,
                    modifiers=intent.modifiers,
                    slots=dict(intent.slot_choices),
                    upsell_rules=list(intent.upsell_rules),
                )
                new_cart.items.append(new_line)

                # Check if replacement combo has missing slots
                if isinstance(replacement_target, Combo):
                    missing_slot = next(
                        (
                            s
                            for s in replacement_target.slots
                            if s.required and not new_line.slots.get(s.slot_id)
                        ),
                        None,
                    )
                    if missing_slot:
                        p_choice = PendingChoice(
                            type="combo_slot",
                            target_line_id=new_line_id,
                            slot_id=missing_slot.slot_id,
                            prompt=f"Pilihan untuk {missing_slot.name_id} apa kak?",
                            allowed_choices=missing_slot.choice_items,
                        )
                        new_state = "awaiting_choice"
                    else:
                        new_state = "ordering"
                else:
                    new_state = "ordering"

                menu_service.calculate_cart_total(new_cart)
                events.append(
                    CartEvent(
                        event_type="ItemReplaced",
                        details={
                            "removed": target_line.item_id,
                            "added": intent.replacement_item_id,
                        },
                    )
                )

        if rejections and new_cart.total_item_count == 0:
            new_cart.status = "rejected"

        facts = SpeechFacts(
            intent_handled="replace_item",
            items_replaced=[
                {
                    "target": intent.target_item_id or (matching[0].item_id if matching else ""),
                    "replacement": intent.replacement_item_id,
                }
            ]
            if not rejections
            else [],
            pending_prompt=p_choice,
            rejections=rejections,
            cart_item_count=new_cart.total_item_count,
            cart_total_price=new_cart.total_price,
            dialog_state=new_state,
        )
        return (
            StateMachineResult(
                new_state=new_state,
                cart=new_cart,
                events=events,
                rejections=rejections,
                speech_facts=facts,
                pending_choice=p_choice,
            ),
            hist,
            p_choice,
        )

    # Fallback
    facts = SpeechFacts(
        intent_handled=intent.type,
        cart_item_count=new_cart.total_item_count,
        cart_total_price=new_cart.total_price,
        dialog_state=current_state,
    )
    return (
        StateMachineResult(
            new_state=current_state,
            cart=new_cart,
            events=events,
            rejections=rejections,
            speech_facts=facts,
            pending_choice=p_choice,
        ),
        hist,
        p_choice,
    )


class CartSession:
    """Stateful conversational session managing dialog state, cart, and history."""

    def __init__(
        self,
        menu_service: MenuService,
        clock: Callable[[], time] | None = None,
    ):
        self.menu_service = menu_service
        clock_fn = clock if clock is not None else getattr(menu_service, "_clock", None)
        self.context = StateContext(clock=clock_fn)
        self.state: DialogState = "ordering"
        self.cart = Cart()
        self.history: list[Cart] = []
        self.pending_choice: PendingChoice | None = None
        self.last_result: StateMachineResult | None = None

    def apply(self, intent: Intent) -> StateMachineResult:
        """Applies an intent and advances session state."""
        result, new_history, new_choice = apply_intent(
            current_state=self.state,
            cart=self.cart,
            intent=intent,
            menu_service=self.menu_service,
            context=self.context,
            history=self.history,
            pending_choice=self.pending_choice,
        )
        self.state = result.new_state
        self.cart = result.cart
        self.history = new_history
        self.pending_choice = new_choice
        self.last_result = result
        return result
