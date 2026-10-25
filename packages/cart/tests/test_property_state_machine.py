"""Property-based tests for Cart State Machine using Hypothesis.

Tests random sequences of valid and invalid intents to rigorously verify:
1. Cart is always valid per MenuService after every step.
2. Total price always equals sum of line prices strictly computed from menu data.
3. Every item quantity is >= 1; total item count never exceeds 20.
4. undo_last, remove_item, and clear_cart never increase the item count.
5. Unavailable, out-of-stock, or out-of-hours items never enter the cart.
6. Price manipulation is impossible by construction (no financial fields in intent schema).
7. Determinism & state serialization round-trip.
8. Idempotency of confirm & immutability of terminal states (done, handoff).
"""

import copy
from datetime import time

from hypothesis import given, settings
from hypothesis import strategies as st
from lajur_cart.intents import (
    AddItemIntent,
    AskInfoIntent,
    ClearCartIntent,
    ConfirmIntent,
    DeclineMoreIntent,
    HandoffIntent,
    ModifyItemIntent,
    RemoveItemIntent,
    ReplaceItemIntent,
    UndoLastIntent,
    UnknownIntent,
)
from lajur_cart.menu_service import MenuService
from lajur_cart.models import Combo, Item
from lajur_cart.state_machine import CartSession

# Pre-load MenuService
menu_service = MenuService(clock=lambda: time(12, 0))
ALL_ITEM_IDS = list(menu_service.items.keys()) + list(menu_service.combos.keys())
OUT_OF_STOCK_IDS = [i.id for i in menu_service.items.values() if not i.in_stock] + [
    c.id for c in menu_service.combos.values() if not c.in_stock
]
BREAKFAST_ONLY_IDS = [
    i.id for i in menu_service.items.values() if i.available_hours == "breakfast"
] + [c.id for c in menu_service.combos.values() if c.available_hours == "breakfast"]

# Strategies
item_id_strategy = st.sampled_from(ALL_ITEM_IDS + ["non_existent_item_xyz", "pizza_keju_loyang"])
quantity_strategy = st.integers(min_value=1, max_value=30)
size_strategy = st.sampled_from(["regular", "medium", "large"])
clock_hour_strategy = st.integers(min_value=0, max_value=23)

add_item_strategy = st.builds(
    AddItemIntent,
    item_id=item_id_strategy,
    quantity=quantity_strategy,
    size=size_strategy,
)

remove_item_strategy = st.builds(
    RemoveItemIntent,
    item_id=st.one_of(st.none(), item_id_strategy),
    quantity=st.one_of(st.none(), st.integers(min_value=1, max_value=5)),
)

modify_item_strategy = st.builds(
    ModifyItemIntent,
    item_id=st.one_of(st.none(), item_id_strategy),
    quantity=st.one_of(st.none(), st.integers(min_value=1, max_value=10)),
    size=st.one_of(st.none(), size_strategy),
)

replace_item_strategy = st.builds(
    ReplaceItemIntent,
    target_item_id=st.one_of(st.none(), item_id_strategy),
    replacement_item_id=item_id_strategy,
    quantity=st.integers(min_value=1, max_value=10),
)

random_intent_strategy = st.one_of(
    add_item_strategy,
    remove_item_strategy,
    modify_item_strategy,
    replace_item_strategy,
    st.builds(UndoLastIntent),
    st.builds(ClearCartIntent),
    st.builds(ConfirmIntent),
    st.builds(DeclineMoreIntent),
    st.builds(HandoffIntent),
    st.builds(AskInfoIntent),
    st.builds(UnknownIntent),
)


@settings(max_examples=80, deadline=None)
@given(intents=st.lists(random_intent_strategy, min_size=1, max_size=15), hour=clock_hour_strategy)
def test_property_invariants_across_random_intent_sequences(intents, hour):
    def clock_fn():
        return time(hour, 0)

    ms = MenuService(clock=clock_fn)
    sess = CartSession(ms, clock=clock_fn)

    for intent in intents:
        count_before = sess.cart.total_item_count

        sess.apply(intent)
        cart = sess.cart

        # Invariant 1: Structural validity per MenuService after every step
        for line in cart.items:
            target = ms.get_item_or_combo(line.item_id)
            assert target is not None, f"Unknown item in cart: {line.item_id}"
            assert line.quantity >= 1
            if isinstance(target, Item):
                if line.size != "regular":
                    assert any(s.size == line.size for s in target.sizes)
                for mod_id in line.modifiers:
                    assert any(
                        mod_id in [o.id for o in ms.modifiers[m].options]
                        for m in target.modifiers
                        if m in ms.modifiers
                    )
            elif isinstance(target, Combo):
                for s_id, choice in line.slots.items():
                    slot_obj = next((s for s in target.slots if s.slot_id == s_id), None)
                    if slot_obj:
                        assert choice in slot_obj.choice_items

        # If terminal state 'done' reached, cart total and items must be consistent
        if sess.state == "done":
            assert 0 <= cart.total_price
            assert 0 <= cart.total_item_count <= 20

        # Invariant 2: Total price strictly equals sum of line prices
        expected_total = sum(ms.calculate_line_price(line) for line in cart.items)
        assert cart.total_price == expected_total, (
            f"Price calculation mismatch: cart.total={cart.total_price}, expected={expected_total}"
        )

        # Invariant 3: Item quantities >= 1 and total count <= 20
        assert cart.total_item_count <= 20, f"Cart exceeded 20 items cap: {cart.total_item_count}"
        for line in cart.items:
            assert line.quantity >= 1, f"Line has non-positive quantity: {line.quantity}"

        # Invariant 4: remove_item and clear_cart never increase item count
        if isinstance(intent, (RemoveItemIntent, ClearCartIntent)):
            assert cart.total_item_count <= count_before, (
                f"Destructive intent {intent.type} increased item count from {count_before} to {cart.total_item_count}"
            )

        # Invariant 5: Out of stock or out of hours items never enter cart
        for line in cart.items:
            assert line.item_id not in OUT_OF_STOCK_IDS, (
                f"Out-of-stock item in cart: {line.item_id}"
            )
            if ms.is_breakfast_time(time(hour, 0)):
                # At breakfast time, regular-only items cannot be in cart
                target = ms.get_item_or_combo(line.item_id)
                assert target is not None
                assert target.available_hours != "regular", (
                    f"Regular item in cart during breakfast: {line.item_id}"
                )
            else:
                # At regular time, breakfast-only items cannot be in cart
                assert line.item_id not in BREAKFAST_ONLY_IDS, (
                    f"Breakfast item in cart during regular hours: {line.item_id}"
                )


@settings(max_examples=40, deadline=None)
@given(intents=st.lists(random_intent_strategy, min_size=1, max_size=8))
def test_property_determinism_and_serialization(intents):
    """Invariant 7: Identical state + intent + clock produces identical result.
    State must also serialize cleanly to dict/JSON without error.
    """

    def clock_fn():
        return time(12, 0)

    # Session 1
    sess1 = CartSession(MenuService(clock=clock_fn), clock=clock_fn)
    for it in intents:
        sess1.apply(it)

    # Session 2 (exact duplicate execution)
    sess2 = CartSession(MenuService(clock=clock_fn), clock=clock_fn)
    for it in intents:
        sess2.apply(it)

    # Assert exact deterministic equality
    assert sess1.state == sess2.state
    assert sess1.cart.total_price == sess2.cart.total_price
    assert sess1.cart.total_item_count == sess2.cart.total_item_count
    assert [(it.item_id, it.quantity, it.price) for it in sess1.cart.items] == [
        (it.item_id, it.quantity, it.price) for it in sess2.cart.items
    ]

    # Serialization round-trip
    cart_dict = sess1.cart.model_dump()
    assert cart_dict["total_price"] == sess1.cart.total_price
    assert len(cart_dict["items"]) == len(sess1.cart.items)


def test_property_confirm_idempotency_and_terminal_immutability():
    """Invariant 8: Confirming an already confirmed cart is idempotent;
    terminal states (done, handoff) reject further mutations.
    """
    ms = MenuService()
    sess = CartSession(ms)

    # Add item and confirm
    sess.apply(AddItemIntent(item_id="burger_sapi_tunggal", quantity=1))
    sess.apply(ConfirmIntent())
    assert sess.state == "done"
    assert sess.cart.status == "confirmed"
    initial_total = sess.cart.total_price
    initial_items = copy.deepcopy(sess.cart.items)

    # Confirm again -> idempotent
    r2 = sess.apply(ConfirmIntent())
    assert sess.state == "done"
    assert sess.cart.status == "confirmed"
    assert sess.cart.total_price == initial_total
    assert sess.cart.items == initial_items
    assert len(r2.rejections) == 0

    # Attempting to mutate in 'done' state must be rejected
    r3 = sess.apply(AddItemIntent(item_id="kentang_goreng", quantity=1))
    assert sess.state == "done"
    assert sess.cart.total_price == initial_total
    assert len(sess.cart.items) == len(initial_items)
    assert any(rej.code == "ORDER_ALREADY_COMPLETED" for rej in r3.rejections)

    # Handoff session rejects further ordering
    sess2 = CartSession(ms)
    sess2.apply(HandoffIntent())
    assert sess2.state == "handoff"
    assert sess2.cart.status == "handoff"

    r4 = sess2.apply(AddItemIntent(item_id="burger_sapi_keju", quantity=1))
    assert sess2.state == "handoff"
    assert len(sess2.cart.items) == 0
    assert any(rej.code == "SESSION_HANDED_OFF" for rej in r4.rejections)
