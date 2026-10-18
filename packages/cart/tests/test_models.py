"""Unit tests for cart domain models."""

import pytest
from lajur_cart.models import (
    Cart,
    CartLine,
    Item,
    ItemSize,
)
from pydantic import ValidationError as PydanticValidationError


def test_item_size_and_pricing():
    size = ItemSize(size="large", price_delta=9000)
    assert size.size == "large"
    assert size.price_delta == 9000


def test_item_creation():
    item = Item(
        id="burger_test",
        category="burger",
        name_id="Burger Uji",
        name_en="Test Burger",
        aliases=["test burger"],
        price=25000,
        sizes=[ItemSize(size="regular", price_delta=0)],
        modifiers=[],
        available_hours="all_day",
        in_stock=True,
    )
    assert item.id == "burger_test"
    assert item.price == 25000
    assert item.in_stock is True


def test_item_negative_price_fails():
    with pytest.raises(PydanticValidationError):
        Item(
            id="bad_item",
            category="burger",
            name_id="Bad",
            name_en="Bad",
            price=-1000,
        )


def test_cart_line_quantity_validation():
    with pytest.raises(PydanticValidationError):
        CartLine(item_id="burger_sapi_tunggal", quantity=0)

    line = CartLine(item_id="burger_sapi_tunggal", quantity=3, price=66000)
    assert line.quantity == 3
    assert line.price == 66000


def test_cart_item_count():
    cart = Cart(
        items=[
            CartLine(item_id="item_a", quantity=2),
            CartLine(item_id="item_b", quantity=5),
        ]
    )
    assert cart.total_item_count == 7
