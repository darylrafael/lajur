"""Unit tests for Cart State Machine (§6, §8, §13, ADR-0002)."""

from datetime import time

import pytest
from lajur_cart.intents import (
    AddItemIntent,
    AnswerChoiceIntent,
    ClearCartIntent,
    ConfirmIntent,
    DeclineMoreIntent,
    HandoffIntent,
    RemoveItemIntent,
    ReplaceItemIntent,
    UndoLastIntent,
)
from lajur_cart.menu_service import MenuService
from lajur_cart.models import Cart
from lajur_cart.state_machine import (
    CartSession,
    DialogState,
    apply_intent,
)


@pytest.fixture
def menu_service() -> MenuService:
    return MenuService("eval/menu/menu.json")


def test_add_simple_item(menu_service: MenuService):
    session = CartSession(menu_service)
    res = session.apply(AddItemIntent(item_id="burger_sapi_tunggal", quantity=2))

    assert res.new_state == "ordering"
    assert len(res.cart.items) == 1
    assert res.cart.items[0].quantity == 2
    assert res.cart.items[0].price == 44000
    assert res.cart.total_price == 44000
    assert len(res.rejections) == 0
    assert res.speech_facts.cart_item_count == 2


def test_out_of_stock_rejected(menu_service: MenuService):
    session = CartSession(menu_service)
    # burger_ikan_crispy is out of stock in menu.json
    res = session.apply(AddItemIntent(item_id="burger_ikan_crispy", quantity=1))

    assert res.new_state == "ordering"
    assert len(res.cart.items) == 0
    assert len(res.rejections) == 1
    assert res.rejections[0].code == "OUT_OF_STOCK"


def test_operating_hours_breakfast_vs_lunch(menu_service: MenuService):
    # Lunch time: 12:00
    session_lunch = CartSession(menu_service, clock=lambda: time(12, 0))
    res_lunch = session_lunch.apply(AddItemIntent(item_id="bubur_ayam_spesial", quantity=1))
    assert len(res_lunch.rejections) == 1
    assert res_lunch.rejections[0].code == "OUT_OF_HOURS"

    # Breakfast time: 08:00
    session_bf = CartSession(menu_service, clock=lambda: time(8, 0))
    res_bf = session_bf.apply(AddItemIntent(item_id="bubur_ayam_spesial", quantity=1))
    assert len(res_bf.rejections) == 0
    assert len(res_bf.cart.items) == 1


def test_hard_cap_20_items(menu_service: MenuService):
    session = CartSession(menu_service)
    res1 = session.apply(AddItemIntent(item_id="burger_sapi_tunggal", quantity=19))
    assert len(res1.rejections) == 0
    assert session.cart.total_item_count == 19

    # Try adding 2 more (total 21 > 20)
    res2 = session.apply(AddItemIntent(item_id="kentang_goreng", quantity=2))
    assert len(res2.rejections) == 1
    assert res2.rejections[0].code == "CAP_EXCEEDED"
    assert session.cart.total_item_count == 19  # Unchanged


def test_remove_item_by_item_id_and_line_id(menu_service: MenuService):
    session = CartSession(menu_service)
    session.apply(AddItemIntent(item_id="burger_sapi_tunggal", quantity=2))
    session.apply(AddItemIntent(item_id="kentang_goreng", quantity=1))

    # Remove partial quantity by item_id
    res_rem = session.apply(RemoveItemIntent(item_id="burger_sapi_tunggal", quantity=1))
    assert len(res_rem.rejections) == 0
    assert session.cart.total_item_count == 2
    assert session.cart.items[0].quantity == 1

    # Remove complete line
    line_id = session.cart.items[1].line_id
    res_rem2 = session.apply(RemoveItemIntent(line_id=line_id))
    assert len(res_rem2.rejections) == 0
    assert len(session.cart.items) == 1
    assert session.cart.items[0].item_id == "burger_sapi_tunggal"


def test_ambiguous_remove_transitions_to_awaiting_choice(menu_service: MenuService):
    session = CartSession(menu_service)
    # Add two different lines of same item (with valid modifiers)
    res1 = session.apply(
        AddItemIntent(item_id="burger_sapi_keju", quantity=1, modifiers=["extra_cheese"])
    )
    assert len(res1.rejections) == 0
    res2 = session.apply(AddItemIntent(item_id="burger_sapi_keju", quantity=1, modifiers=[]))
    assert len(res2.rejections) == 0
    assert len(session.cart.items) == 2

    res = session.apply(RemoveItemIntent(item_id="burger_sapi_keju"))
    assert res.new_state == "awaiting_choice"
    assert res.pending_choice is not None
    assert res.pending_choice.type == "ambiguity"


def test_replace_item_atomic(menu_service: MenuService):
    session = CartSession(menu_service)
    session.apply(AddItemIntent(item_id="kentang_goreng", quantity=1))
    session.apply(AddItemIntent(item_id="es_teh_manis", quantity=1))

    # Swap kentang goreng with nasi putih
    res = session.apply(
        ReplaceItemIntent(
            target_item_id="kentang_goreng", replacement_item_id="nasi_putih", quantity=1
        )
    )
    assert res.new_state == "ordering"
    assert len(res.rejections) == 0
    items = {item.item_id: item.quantity for item in session.cart.items}
    assert "kentang_goreng" not in items
    assert items["nasi_putih"] == 1
    assert items["es_teh_manis"] == 1
    assert session.cart.total_price == 17000  # 9000 + 8000


def test_undo_last_semantics(menu_service: MenuService):
    session = CartSession(menu_service)
    # 1. Nothing to undo
    res0 = session.apply(UndoLastIntent())
    assert res0.rejections[0].code == "NOTHING_TO_UNDO"

    # 2. Add item then undo
    session.apply(AddItemIntent(item_id="burger_sapi_tunggal", quantity=1))
    assert session.cart.total_item_count == 1
    session.apply(AddItemIntent(item_id="kentang_goreng", quantity=1))
    assert session.cart.total_item_count == 2

    res_undo = session.apply(UndoLastIntent())
    assert res_undo.new_state == "ordering"
    assert session.cart.total_item_count == 1
    assert session.cart.items[0].item_id == "burger_sapi_tunggal"


def test_clear_cart(menu_service: MenuService):
    session = CartSession(menu_service)
    session.apply(AddItemIntent(item_id="burger_sapi_tunggal", quantity=2))
    assert session.cart.total_item_count == 2

    res = session.apply(ClearCartIntent())
    assert res.new_state == "ordering"
    assert session.cart.total_item_count == 0
    assert session.cart.total_price == 0


def test_combo_flow_with_awaiting_choice(menu_service: MenuService):
    session = CartSession(menu_service)
    # Add combo without required slot choices -> transitions to awaiting_choice
    res = session.apply(AddItemIntent(item_id="paket_hemat_ayam_1", quantity=1))
    assert res.new_state == "awaiting_choice"
    assert res.pending_choice is not None
    assert res.pending_choice.type == "combo_slot"
    assert res.pending_choice.slot_id == "main"

    # 1. Answer chicken slot
    res_choice1 = session.apply(AnswerChoiceIntent(choice_id="ayam_goreng_crispy", slot_id="main"))
    assert len(res_choice1.rejections) == 0
    # Next required slot is side or drink
    assert session.pending_choice is not None
    assert session.pending_choice.slot_id in ["side", "drink"]

    # 2. Answer side slot
    side_slot = session.pending_choice.slot_id
    res_choice2 = session.apply(
        AnswerChoiceIntent(choice_id=session.pending_choice.allowed_choices[0], slot_id=side_slot)
    )
    assert len(res_choice2.rejections) == 0

    # 3. Answer drink slot
    drink_slot = session.pending_choice.slot_id
    res_choice3 = session.apply(
        AnswerChoiceIntent(choice_id=session.pending_choice.allowed_choices[0], slot_id=drink_slot)
    )
    assert len(res_choice3.rejections) == 0
    assert session.state == "ordering"


def test_confirm_flow(menu_service: MenuService):
    session = CartSession(menu_service)
    # Confirm empty cart -> rejected
    res_empty = session.apply(ConfirmIntent())
    assert res_empty.rejections[0].code == "EMPTY_CART_CONFIRM"

    # Add item
    session.apply(AddItemIntent(item_id="burger_sapi_tunggal", quantity=1))

    # Decline more -> transitions to confirming
    res_decline = session.apply(DeclineMoreIntent())
    assert res_decline.new_state == "confirming"
    assert res_decline.speech_facts.requires_confirmation is True

    # Confirm in confirming state -> done
    res_done = session.apply(ConfirmIntent())
    assert res_done.new_state == "done"
    assert session.cart.status == "confirmed"

    # Further operations in done state rejected
    res_after = session.apply(AddItemIntent(item_id="es_teh_manis", quantity=1))
    assert res_after.rejections[0].code == "ORDER_ALREADY_COMPLETED"


def test_handoff_any_state(menu_service: MenuService):
    session = CartSession(menu_service)
    session.apply(AddItemIntent(item_id="burger_sapi_tunggal", quantity=1))
    res = session.apply(HandoffIntent(reason="customer_asked_manager"))

    assert res.new_state == "handoff"
    assert session.cart.status == "handoff"

    # Further operations rejected
    res_after = session.apply(ConfirmIntent())
    assert res_after.rejections[0].code == "SESSION_HANDED_OFF"


def test_pure_apply_intent_immutability(menu_service: MenuService):
    cart_orig = Cart()
    state_orig: DialogState = "ordering"
    res, hist, choice = apply_intent(
        current_state=state_orig,
        cart=cart_orig,
        intent=AddItemIntent(item_id="burger_sapi_tunggal", quantity=1),
        menu_service=menu_service,
    )
    # Original cart remains untouched
    assert len(cart_orig.items) == 0
    assert len(res.cart.items) == 1
