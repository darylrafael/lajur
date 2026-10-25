"""Targeted tests to exercise edge cases and error paths for >=95% code coverage."""

from datetime import time
from pathlib import Path

import pytest
from lajur_cart.intents import (
    AddItemIntent,
    AnswerChoiceIntent,
    ConfirmIntent,
    ModifyItemIntent,
    ReplaceItemIntent,
    export_intent_json_schema,
)
from lajur_cart.menu_service import MenuService, ValidationError
from lajur_cart.models import Cart, CartLine
from lajur_cart.state_machine import CartSession


def test_awaiting_choice_guards():
    ms = MenuService()
    sess = CartSession(ms)

    # 1. Answer choice when not awaiting choice -> UNEXPECTED_CHOICE
    r1 = sess.apply(AnswerChoiceIntent(choice_id="es_teh_manis"))
    assert any(rej.code == "UNEXPECTED_CHOICE" for rej in r1.rejections)

    # 2. Add combo with missing slot -> enters awaiting_choice
    sess.apply(AddItemIntent(item_id="paket_hemat_ayam_1"))
    assert sess.state == "awaiting_choice"
    assert sess.pending_choice is not None

    # 3. Sending another intent while awaiting choice -> CHOICE_REQUIRED
    r3 = sess.apply(AddItemIntent(item_id="kentang_goreng"))
    assert any(rej.code == "CHOICE_REQUIRED" for rej in r3.rejections)
    assert sess.state == "awaiting_choice"

    # 4. Sending invalid choice for the slot -> INVALID_CHOICE
    r4 = sess.apply(AnswerChoiceIntent(choice_id="es_teh_manis", slot_id="main"))
    assert any(rej.code == "INVALID_CHOICE" for rej in r4.rejections)


def test_confirm_empty_cart():
    ms = MenuService()
    sess = CartSession(ms)

    # Confirming empty cart -> EMPTY_CART_CONFIRM
    r = sess.apply(ConfirmIntent())
    assert any(rej.code == "EMPTY_CART_CONFIRM" for rej in r.rejections)
    assert sess.state == "ordering"


def test_modify_item_edge_cases():
    ms = MenuService()
    sess = CartSession(ms)

    # 1. Modify item not in cart -> ITEM_NOT_IN_CART
    r1 = sess.apply(ModifyItemIntent(item_id="burger_sapi_tunggal", quantity=2))
    assert any(rej.code == "ITEM_NOT_IN_CART" for rej in r1.rejections)

    # 2. Add two identical items to test ambiguity
    sess.apply(AddItemIntent(item_id="kentang_goreng", size="regular"))
    sess.apply(AddItemIntent(item_id="kentang_goreng", size="large"))
    assert len(sess.cart.items) == 2

    # Modify without line_id when ambiguous -> enters awaiting_choice
    sess.apply(ModifyItemIntent(item_id="kentang_goreng", size="medium"))
    assert sess.state == "awaiting_choice"
    assert sess.pending_choice is not None and sess.pending_choice.type == "ambiguity"

    # Resolve ambiguity with answer_choice
    sess.apply(AnswerChoiceIntent(choice_id="line_1", line_id="line_1"))
    assert sess.state == "ordering"

    # 3. Modify with invalid size for item -> INVALID_SIZE
    sess.apply(AddItemIntent(item_id="burger_sapi_tunggal", quantity=1))
    r4 = sess.apply(ModifyItemIntent(item_id="burger_sapi_tunggal", size="large"))
    assert any(rej.code == "INVALID_SIZE" for rej in r4.rejections)

    # 4. Modify quantity exceeding 20 item cap -> CAP_EXCEEDED
    r5 = sess.apply(ModifyItemIntent(item_id="burger_sapi_tunggal", quantity=25))
    assert any(rej.code == "CAP_EXCEEDED" for rej in r5.rejections)


def test_replace_item_edge_cases():
    ms = MenuService(clock=lambda: time(12, 0))
    sess = CartSession(ms)
    sess.apply(AddItemIntent(item_id="burger_sapi_tunggal", quantity=1))

    # 1. Target not in cart
    r1 = sess.apply(
        ReplaceItemIntent(target_item_id="nasi_putih", replacement_item_id="kentang_goreng")
    )
    assert any(rej.code == "ITEM_NOT_IN_CART" for rej in r1.rejections)

    # 2. Unknown replacement item
    r2 = sess.apply(
        ReplaceItemIntent(target_item_id="burger_sapi_tunggal", replacement_item_id="pizza_super")
    )
    assert any(rej.code == "UNKNOWN_ITEM" for rej in r2.rejections)

    # 3. Out of stock replacement
    r3 = sess.apply(
        ReplaceItemIntent(
            target_item_id="burger_sapi_tunggal", replacement_item_id="burger_ikan_crispy"
        )
    )
    assert any(rej.code == "OUT_OF_STOCK" for rej in r3.rejections)

    # 4. Out of hours replacement (breakfast item at 12:00)
    r4 = sess.apply(
        ReplaceItemIntent(target_item_id="burger_sapi_tunggal", replacement_item_id="bubur_ayam")
    )
    assert any(rej.code == "OUT_OF_HOURS" for rej in r4.rejections)

    # 5. Quantity exceeding 20 cap
    r5 = sess.apply(
        ReplaceItemIntent(
            target_item_id="burger_sapi_tunggal", replacement_item_id="kentang_goreng", quantity=25
        )
    )
    assert any(rej.code == "CAP_EXCEEDED" for rej in r5.rejections)

    # 6. Replace with combo that has missing slots -> enters awaiting_choice
    sess.apply(
        ReplaceItemIntent(
            target_item_id="burger_sapi_tunggal", replacement_item_id="paket_hemat_ayam_1"
        )
    )
    assert sess.state == "awaiting_choice"
    assert sess.pending_choice is not None and sess.pending_choice.type == "combo_slot"


def test_menu_service_calculation_exceptions():
    ms = MenuService()

    # 1. Invalid size on Item
    invalid_size_line = CartLine(item_id="burger_sapi_tunggal", quantity=1, size="large")
    with pytest.raises(ValidationError, match="does not support size"):
        ms.calculate_line_price(invalid_size_line)

    # 2. Invalid modifier option on Item
    invalid_mod_line = CartLine(
        item_id="burger_sapi_tunggal", quantity=1, modifiers=["non_existent_modifier"]
    )
    with pytest.raises(ValidationError, match="not valid for item"):
        ms.calculate_line_price(invalid_mod_line)

    # 3. Invalid upsell rule on Combo
    invalid_upsell_line = CartLine(
        item_id="paket_hemat_burger_tunggal", quantity=1, upsell_rules=["non_existent_upsell"]
    )
    with pytest.raises(ValidationError, match="Upsell rule .* is not valid"):
        ms.calculate_line_price(invalid_upsell_line)


def test_schema_export_direct(tmp_path: Path):
    out = tmp_path / "test_schema.json"
    schema = export_intent_json_schema(out)
    assert out.exists()
    assert "properties" in schema


def test_menu_service_validation_rules_extended():
    ms = MenuService()

    # normalize_text empty
    assert ms.normalize_text("") == ""

    # Unknown item in validate_cart
    c1 = Cart(items=[CartLine(item_id="non_existent", quantity=1)])
    errs1 = ms.validate_cart(c1)
    assert any("Unknown item" in e for e in errs1)

    # Quantity < 1 in validate_cart
    c2 = Cart(items=[CartLine(item_id="kentang_goreng", quantity=1)])
    c2.items[0].quantity = 0
    errs2 = ms.validate_cart(c2)
    assert any("Quantity must be at least 1" in e for e in errs2)

    # Invalid size in validate_cart
    c3 = Cart(items=[CartLine(item_id="burger_sapi_tunggal", quantity=1, size="large")])
    errs3 = ms.validate_cart(c3)
    assert any("not available" in e for e in errs3)

    # Invalid modifier in validate_cart
    c4 = Cart(items=[CartLine(item_id="kentang_goreng", quantity=1, modifiers=["mod_unknown_opt"])])
    errs4 = ms.validate_cart(c4)
    assert any("does not apply to this item" in e for e in errs4)


def test_repl_parser_and_display():
    from lajur_cart.intents import (
        AddItemIntent,
        AnswerChoiceIntent,
        AskInfoIntent,
        ClearCartIntent,
        ConfirmIntent,
        DeclineMoreIntent,
        HandoffIntent,
        ModifyItemIntent,
        RemoveItemIntent,
        ReplaceItemIntent,
        UndoLastIntent,
    )
    from lajur_cart.repl import parse_input_to_intent, print_session_state

    # 1. Empty and invalid
    assert parse_input_to_intent("") is None
    assert parse_input_to_intent("   ") is None
    assert parse_input_to_intent("foobar_unknown") is None

    # 2. JSON input
    it_json = parse_input_to_intent('{"type": "confirm"}')
    assert isinstance(it_json, ConfirmIntent)

    # 3. Add command
    assert parse_input_to_intent("add") is None
    it_add = parse_input_to_intent("add burger_sapi_tunggal 2 medium")
    assert isinstance(it_add, AddItemIntent)
    assert (
        it_add.item_id == "burger_sapi_tunggal" and it_add.quantity == 2 and it_add.size == "medium"
    )

    # 4. Remove command
    assert parse_input_to_intent("remove") is None
    it_rem = parse_input_to_intent("remove burger_sapi_tunggal 1")
    assert isinstance(it_rem, RemoveItemIntent) and it_rem.quantity == 1

    # 5. Replace command
    assert parse_input_to_intent("replace") is None
    assert parse_input_to_intent("replace burger_sapi_tunggal") is None
    it_rep = parse_input_to_intent("replace burger_sapi_tunggal kentang_goreng 2")
    assert isinstance(it_rep, ReplaceItemIntent) and it_rep.quantity == 2

    # 6. Modify command
    assert parse_input_to_intent("modify") is None
    it_mod = parse_input_to_intent("modify kentang_goreng size=large qty=3")
    assert isinstance(it_mod, ModifyItemIntent) and it_mod.size == "large" and it_mod.quantity == 3

    # 7. Answer command
    assert parse_input_to_intent("answer") is None
    it_ans = parse_input_to_intent("answer coca_cola drink")
    assert (
        isinstance(it_ans, AnswerChoiceIntent)
        and it_ans.choice_id == "coca_cola"
        and it_ans.slot_id == "drink"
    )

    # 8. Shorthand commands
    assert isinstance(parse_input_to_intent("undo"), UndoLastIntent)
    assert isinstance(parse_input_to_intent("clear"), ClearCartIntent)
    assert isinstance(parse_input_to_intent("confirm"), ConfirmIntent)
    assert isinstance(parse_input_to_intent("decline"), DeclineMoreIntent)
    it_ho = parse_input_to_intent("handoff needs manager")
    assert isinstance(it_ho, HandoffIntent) and it_ho.reason == "needs manager"
    it_inf = parse_input_to_intent("info operating_hours")
    assert isinstance(it_inf, AskInfoIntent) and it_inf.query_type == "operating_hours"

    # 9. Test print_session_state
    ms = MenuService()
    sess = CartSession(ms)
    print_session_state(sess)

    sess.apply(AddItemIntent(item_id="paket_hemat_ayam_1"))
    print_session_state(sess)
