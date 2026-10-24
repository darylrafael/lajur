"""Domain models for Lajur Cart and Menu (§8).

All monetary values are stored as integer Indonesian Rupiah (IDR).
"""

from typing import Literal

from pydantic import BaseModel, Field


class ItemSize(BaseModel):
    """Size variant for an item."""

    size: Literal["regular", "medium", "large"]
    price_delta: int = Field(default=0, description="Additional price in IDR for this size")


class ModifierOption(BaseModel):
    """Specific option within a modifier group."""

    id: str
    name_id: str
    name_en: str
    price_delta: int = Field(default=0, description="Additional price in IDR")


class Modifier(BaseModel):
    """Modifier group that can be attached to items."""

    id: str
    name_id: str
    name_en: str
    applies_to: list[str] = Field(default_factory=list)
    options: list[ModifierOption] = Field(default_factory=list)
    required: bool = False
    max: int = 1


class ComboSlot(BaseModel):
    """Slot within a combo meal requiring a customer selection."""

    slot_id: str
    name_id: str
    name_en: str
    required: bool = True
    choice_items: list[str] = Field(default_factory=list)


class UpsellRule(BaseModel):
    """Contextual upsell offer linked to a combo."""

    rule_id: str
    prompt_id: str
    prompt_en: str
    target_item: str
    price_delta: int = Field(default=0, description="Upsell bundle price addition in IDR")


class Item(BaseModel):
    """Standard menu item definition."""

    id: str
    category: Literal["burger", "ayam", "nasi", "sarapan", "side", "minuman", "dessert", "combo"]
    name_id: str
    name_en: str
    aliases: list[str] = Field(default_factory=list)
    price: int = Field(gt=0, description="Base price in IDR")
    sizes: list[ItemSize] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list, description="IDs of applicable modifiers")
    available_hours: Literal["all_day", "breakfast", "regular"] = "all_day"
    in_stock: bool = True


class Combo(BaseModel):
    """Combo meal definition with nested choice slots."""

    id: str
    name_id: str
    name_en: str
    aliases: list[str] = Field(default_factory=list)
    base_price: int = Field(gt=0, description="Base combo bundle price in IDR")
    available_hours: Literal["all_day", "breakfast", "regular"] = "regular"
    in_stock: bool = True
    slots: list[ComboSlot] = Field(default_factory=list)
    upsell_rules: list[UpsellRule] = Field(default_factory=list)


class CartLine(BaseModel):
    """Single line item within a customer's shopping cart."""

    line_id: str = Field(default="", description="Unique identifier for line item in cart")
    item_id: str
    quantity: int = Field(default=1, ge=1, description="Quantity ordered")
    size: Literal["regular", "medium", "large"] = "regular"
    modifiers: list[str] = Field(
        default_factory=list, description="List of selected modifier option IDs"
    )
    slots: dict[str, str] = Field(
        default_factory=dict, description="Combo slot_id -> chosen item_id"
    )
    upsell_rules: list[str] = Field(
        default_factory=list, description="Applied combo upsell rule IDs"
    )
    price: int = Field(
        default=0, ge=0, description="Computed subtotal price in IDR (unit_price * quantity)"
    )


class Cart(BaseModel):
    """Complete customer shopping cart representation."""

    items: list[CartLine] = Field(default_factory=list)
    total_price: int = Field(default=0, ge=0, description="Total order price in IDR")
    status: Literal["in_progress", "confirmed", "rejected", "empty", "handoff"] = "in_progress"

    @property
    def total_item_count(self) -> int:
        """Sum of all item quantities in the cart."""
        return sum(item.quantity for item in self.items)
