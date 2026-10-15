"""Unit tests for MenuService and order validation rules."""

from datetime import time

import pytest
from lajur_cart.menu_service import MenuService, ValidationError
from lajur_cart.models import Cart, CartLine


@pytest.fixture
def menu_service() -> MenuService:
    return MenuService()


def test_alias_lookup_exact_and_normalized(menu_service: MenuService):
    # Indonesian alias
    res_id = menu_service.resolve_alias("kentang goreng")
    assert res_id is not None
    assert res_id.id == "kentang_goreng"

    # Colloquial / short alias
    res_short = menu_service.resolve_alias("kentang")
    assert res_short is not None
    assert res_short.id == "kentang_goreng"

    # English alias with upper case and punctuation
    res_en = menu_service.resolve_alias("  FRENCH FRIES!!  ")
    assert res_en is not None
    assert res_en.id == "kentang_goreng"

    # Combo alias
    res_combo = menu_service.resolve_alias("paket burger ganda")
    assert res_combo is not None
    assert res_combo.id == "paket_hemat_burger_ganda"

    # Unknown alias
    assert menu_service.resolve_alias("nasi goreng kambing") is None


def test_breakfast_hours_boundary_conditions(menu_service: MenuService):
    # Boundary 1: 04:59:59 -> Not breakfast yet
    assert menu_service.is_breakfast_time(time(4, 59, 59)) is False

    # Boundary 2: 05:00:00 -> Breakfast starts
    assert menu_service.is_breakfast_time(time(5, 0, 0)) is True

    # Mid breakfast: 08:30:00 -> Breakfast
    assert menu_service.is_breakfast_time(time(8, 30, 0)) is True

    # Boundary 3: 10:59:59 -> Breakfast ending
    assert menu_service.is_breakfast_time(time(10, 59, 59)) is True

    # Boundary 4: 11:00:00 -> Regular hours begin
    assert menu_service.is_breakfast_time(time(11, 0, 0)) is False

    # Evening: 19:00:00 -> Regular hours
    assert menu_service.is_breakfast_time(time(19, 0, 0)) is False


def test_injected_clock_determinism():
    # Injected clock set to 07:00 AM (breakfast)
    breakfast_service = MenuService(clock=lambda: time(7, 0))
    bubur = breakfast_service.get_item_or_combo("bubur_ayam")
    assert bubur is not None
    assert breakfast_service.is_item_available(bubur) is True

    burger = breakfast_service.get_item_or_combo("burger_sapi_keju")
    assert burger is not None
    assert breakfast_service.is_item_available(burger) is False

    # Injected clock set to 13:00 PM (regular lunch)
    lunch_service = MenuService(clock=lambda: time(13, 0))
    assert lunch_service.is_item_available(bubur) is False
    assert lunch_service.is_item_available(burger) is True


def test_out_of_stock_validation(menu_service: MenuService):
    cart = Cart(
        items=[
            CartLine(item_id="burger_ikan_crispy", quantity=1),  # Out of stock
        ]
    )
    errors = menu_service.validate_cart(cart, current_time=time(13, 0))
    assert any("out of stock" in err.lower() for err in errors)


def test_price_computation_from_menu(menu_service: MenuService):
    # Regular Single burger: 22000
    line_burger = CartLine(item_id="burger_sapi_tunggal", quantity=2)
    subtotal_burger = menu_service.calculate_line_price(line_burger)
    assert subtotal_burger == 44000

    # Large fries: base 16000 + 9000 (large delta) = 25000
    line_fries = CartLine(item_id="kentang_goreng", quantity=1, size="large")
    subtotal_fries = menu_service.calculate_line_price(line_fries)
    assert subtotal_fries == 25000

    # Burger with extra cheese: base 28000 + 5000 = 33000
    line_custom = CartLine(
        item_id="burger_sapi_keju",
        quantity=1,
        modifiers=["extra_cheese"],
    )
    subtotal_custom = menu_service.calculate_line_price(line_custom)
    assert subtotal_custom == 33000

    cart = Cart(items=[line_burger, line_fries, line_custom])
    total = menu_service.calculate_cart_total(cart)
    assert total == 44000 + 25000 + 33000
    assert cart.total_price == total


def test_modifier_validation_required_and_max(menu_service: MenuService):
    # Chicken flavor modifier is required for ayam_goreng_crispy
    chicken = menu_service.get_item_or_combo("ayam_goreng_crispy")
    assert chicken is not None

    cart_missing_flavor = Cart(
        items=[CartLine(item_id="ayam_goreng_crispy", quantity=1, modifiers=[])]
    )
    errors = menu_service.validate_cart(cart_missing_flavor, current_time=time(13, 0))
    assert any("required" in err.lower() for err in errors)

    # Exceeding max modifier
    cart_too_many_flavors = Cart(
        items=[
            CartLine(
                item_id="ayam_goreng_crispy",
                quantity=1,
                modifiers=["flavor_original", "flavor_spicy"],
            )
        ]
    )
    errors_max = menu_service.validate_cart(cart_too_many_flavors, current_time=time(13, 0))
    assert any("exceeds max" in err.lower() for err in errors_max)


def test_combo_slots_validation(menu_service: MenuService):
    # Missing required drink slot in combo
    cart_missing_slot = Cart(
        items=[
            CartLine(
                item_id="paket_hemat_burger_tunggal",
                quantity=1,
                slots={"main": "burger_sapi_tunggal", "side": "kentang_goreng"},
            )
        ]
    )
    errors = menu_service.validate_cart(cart_missing_slot, current_time=time(13, 0))
    assert any("missing selection for slot" in err.lower() for err in errors)

    # Invalid choice in slot
    cart_invalid_choice = Cart(
        items=[
            CartLine(
                item_id="paket_hemat_burger_tunggal",
                quantity=1,
                slots={
                    "main": "burger_sapi_tunggal",
                    "side": "kentang_goreng",
                    "drink": "kopi_hitam_panas",  # Not in drink slot choices for this burger combo
                },
            )
        ]
    )
    errors_invalid = menu_service.validate_cart(cart_invalid_choice, current_time=time(13, 0))
    assert any("not a valid choice for slot" in err.lower() for err in errors_invalid)


def test_item_cap_limit_20(menu_service: MenuService):
    # Order with 21 items total exceeds limit
    cart_over = Cart(
        items=[
            CartLine(item_id="burger_sapi_tunggal", quantity=10),
            CartLine(item_id="kentang_goreng", quantity=11),
        ]
    )
    errors = menu_service.validate_cart(cart_over, current_time=time(13, 0))
    assert any("exceeds maximum limit of 20 items" in err.lower() for err in errors)

    # Order with exactly 20 items passes cap check
    cart_exact = Cart(
        items=[
            CartLine(item_id="burger_sapi_tunggal", quantity=10),
            CartLine(item_id="kentang_goreng", quantity=10),
        ]
    )
    errors_exact = menu_service.validate_cart(cart_exact, current_time=time(13, 0))
    assert not any("exceeds maximum limit" in err.lower() for err in errors_exact)


def test_invalid_item_id_raises_validation_error(menu_service: MenuService):
    line = CartLine(item_id="non_existent_item", quantity=1)
    with pytest.raises(ValidationError):
        menu_service.calculate_line_price(line)
