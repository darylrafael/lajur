"""Deterministic Menu Service for Lajur.

Pure business logic for:
- Loading menu data from menu.json
- Resolving Indonesian/English item aliases (exact and normalized only)
- Checking operating hours availability (breakfast vs regular) with an injected clock
- Checking stock levels (86'd items)
- Deterministically computing prices from the menu only
- Enforcing order validation rules (modifiers, sizes, combo slots, and item caps)
"""

import json
import re
from collections.abc import Callable
from datetime import time
from pathlib import Path
from typing import Any

from lajur_cart.models import (
    Cart,
    CartLine,
    Combo,
    Item,
    Modifier,
)


class ValidationError(Exception):
    """Raised when cart or item validation fails."""


class MenuService:
    """Provides deterministic query, pricing, and validation operations against the menu."""

    def __init__(
        self,
        menu_source: dict[str, Any] | Path | str | None = None,
        clock: Callable[[], time] | None = None,
    ):
        """Initialize MenuService.

        Args:
            menu_source: Dictionary with menu data, or Path/string pointing to menu.json.
                         If None, searches for eval/menu/menu.json.
            clock: Callable returning the current time of day for deterministic testing.
                   Defaults to 12:00 (regular lunch hours).
        """
        self._clock: Callable[[], time] = clock if clock is not None else (lambda: time(12, 0))

        if menu_source is None:
            # Default lookup relative to repo root
            candidate = Path("eval/menu/menu.json")
            if not candidate.exists():
                candidate = Path(__file__).resolve().parents[4] / "eval" / "menu" / "menu.json"
            menu_source = candidate

        if isinstance(menu_source, (str, Path)):
            with open(menu_source, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = menu_source

        self.version: str = data.get("version", "1.0")
        self.operating_hours: dict[str, Any] = data.get(
            "operating_hours",
            {
                "breakfast": {"start": "05:00", "end": "11:00"},
                "regular": {"start": "11:00", "end": "05:00"},
            },
        )

        # Parse models
        self.modifiers: dict[str, Modifier] = {
            m["id"]: Modifier(**m) for m in data.get("modifiers", [])
        }
        self.items: dict[str, Item] = {i["id"]: Item(**i) for i in data.get("items", [])}
        self.combos: dict[str, Combo] = {c["id"]: Combo(**c) for c in data.get("combos", [])}

        # Build alias lookup table: normalized_alias -> Item | Combo
        self._alias_map: dict[str, Item | Combo] = {}
        self._build_alias_index()

    def _build_alias_index(self) -> None:
        """Indexes all exact and normalized names and aliases."""
        # Index regular items
        for item in self.items.values():
            self._register_alias(item.id, item)
            self._register_alias(item.name_id, item)
            self._register_alias(item.name_en, item)
            for alias in item.aliases:
                self._register_alias(alias, item)

        # Index combos
        for combo in self.combos.values():
            self._register_alias(combo.id, combo)
            self._register_alias(combo.name_id, combo)
            self._register_alias(combo.name_en, combo)
            for alias in combo.aliases:
                self._register_alias(alias, combo)

    def _register_alias(self, text: str, target: Item | Combo) -> None:
        norm = self.normalize_text(text)
        if norm and norm not in self._alias_map:
            self._alias_map[norm] = target

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text by lowercasing, stripping punctuation, and collapsing whitespace."""
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return " ".join(cleaned.split())

    def resolve_alias(self, query: str) -> Item | Combo | None:
        """Resolve a spoken or typed phrase to an Item or Combo.

        Uses exact and normalized matching only (no fuzzy matching per Minggu 0/1 spec).
        """
        norm_query = self.normalize_text(query)
        return self._alias_map.get(norm_query)

    def get_item_or_combo(self, item_id: str) -> Item | Combo | None:
        """Fetch an item or combo by its canonical ID."""
        if item_id in self.items:
            return self.items[item_id]
        if item_id in self.combos:
            return self.combos[item_id]
        return None

    def is_breakfast_time(self, current_time: time | None = None) -> bool:
        """Determines if the given or injected clock time falls within breakfast hours (05:00 - 11:00)."""
        t = current_time if current_time is not None else self._clock()
        # Breakfast: [05:00, 11:00)
        return time(5, 0) <= t < time(11, 0)

    def is_item_available(self, target: Item | Combo, current_time: time | None = None) -> bool:
        """Checks if an item is available based on current operating hours."""
        if target.available_hours == "all_day":
            return True
        is_breakfast = self.is_breakfast_time(current_time)
        if target.available_hours == "breakfast":
            return is_breakfast
        if target.available_hours == "regular":
            return not is_breakfast
        return False

    def is_in_stock(self, target: Item | Combo) -> bool:
        """Checks if an item or combo is currently in stock."""
        return target.in_stock

    def calculate_line_price(self, line: CartLine) -> int:
        """Computes the total subtotal price for a single CartLine strictly from menu data."""
        target = self.get_item_or_combo(line.item_id)
        if not target:
            raise ValidationError(f"Unknown item or combo ID: '{line.item_id}'")

        unit_price = 0

        if isinstance(target, Item):
            unit_price = target.price

            # Apply size price delta
            if line.size != "regular":
                size_obj = next((s for s in target.sizes if s.size == line.size), None)
                if not size_obj:
                    raise ValidationError(f"Item '{target.id}' does not support size '{line.size}'")
                unit_price += size_obj.price_delta

            # Apply modifier option price deltas
            for mod_opt_id in line.modifiers:
                found = False
                for mod_group_id in target.modifiers:
                    group = self.modifiers.get(mod_group_id)
                    if not group:
                        continue
                    opt = next((o for o in group.options if o.id == mod_opt_id), None)
                    if opt:
                        unit_price += opt.price_delta
                        found = True
                        break
                if not found:
                    raise ValidationError(
                        f"Modifier option '{mod_opt_id}' is not valid for item '{target.id}'"
                    )

        elif isinstance(target, Combo):
            unit_price = target.base_price

            # Apply upsell rule deltas
            for upsell_id in line.upsell_rules:
                rule = next((r for r in target.upsell_rules if r.rule_id == upsell_id), None)
                if not rule:
                    raise ValidationError(
                        f"Upsell rule '{upsell_id}' is not valid for combo '{target.id}'"
                    )
                unit_price += rule.price_delta

        return unit_price * line.quantity

    def calculate_cart_total(self, cart: Cart) -> int:
        """Calculates and updates total price for all items in the cart."""
        total = 0
        for line in cart.items:
            line_subtotal = self.calculate_line_price(line)
            line.price = line_subtotal
            total += line_subtotal
        cart.total_price = total
        return total

    def validate_cart(self, cart: Cart, current_time: time | None = None) -> list[str]:
        """Validates all items and rules in the cart.

        Returns a list of human-readable error messages (empty list if completely valid).
        """
        errors: list[str] = []

        # 1. Total quantity cap (§11.2: 20 items per order max)
        total_qty = cart.total_item_count
        if total_qty > 20:
            errors.append(f"Order exceeds maximum limit of 20 items (current: {total_qty})")

        # 2. Per-line validations
        for idx, line in enumerate(cart.items):
            target = self.get_item_or_combo(line.item_id)
            if not target:
                errors.append(f"Line {idx + 1}: Unknown item '{line.item_id}'")
                continue

            # Quantity check
            if line.quantity < 1:
                errors.append(f"Line {idx + 1} ({line.item_id}): Quantity must be at least 1")

            # Stock check
            if not self.is_in_stock(target):
                errors.append(f"Line {idx + 1} ({target.name_id}): Item is currently out of stock")

            # Operating hours check
            if not self.is_item_available(target, current_time):
                errors.append(
                    f"Line {idx + 1} ({target.name_id}): Not available during current operating hours"
                )

            # Item-specific validations
            if isinstance(target, Item):
                # Size check
                if line.size != "regular":
                    valid_sizes = [s.size for s in target.sizes]
                    if line.size not in valid_sizes:
                        errors.append(
                            f"Line {idx + 1} ({target.name_id}): Size '{line.size}' not available"
                        )

                # Modifier checks
                selected_by_group: dict[str, list[str]] = {m_id: [] for m_id in target.modifiers}
                for mod_opt_id in line.modifiers:
                    found_group = None
                    for m_id in target.modifiers:
                        group = self.modifiers.get(m_id)
                        if group and any(o.id == mod_opt_id for o in group.options):
                            found_group = m_id
                            break
                    if not found_group:
                        errors.append(
                            f"Line {idx + 1} ({target.name_id}): Modifier '{mod_opt_id}' does not apply to this item"
                        )
                    else:
                        selected_by_group[found_group].append(mod_opt_id)

                for m_id, group in (
                    (m_id, self.modifiers[m_id])
                    for m_id in target.modifiers
                    if m_id in self.modifiers
                ):
                    count = len(selected_by_group[m_id])
                    if group.required and count == 0:
                        errors.append(
                            f"Line {idx + 1} ({target.name_id}): Modifier group '{group.name_id}' is required"
                        )
                    if count > group.max:
                        errors.append(
                            f"Line {idx + 1} ({target.name_id}): Modifier group '{group.name_id}' exceeds max of {group.max}"
                        )

            # Combo-specific validations
            elif isinstance(target, Combo):
                for slot in target.slots:
                    chosen = line.slots.get(slot.slot_id)
                    if slot.required and not chosen:
                        errors.append(
                            f"Line {idx + 1} ({target.name_id}): Missing selection for slot '{slot.name_id}'"
                        )
                    elif chosen:
                        if chosen not in slot.choice_items:
                            errors.append(
                                f"Line {idx + 1} ({target.name_id}): '{chosen}' is not a valid choice for slot '{slot.name_id}'"
                            )
                        else:
                            chosen_item = self.items.get(chosen)
                            if chosen_item and not self.is_in_stock(chosen_item):
                                errors.append(
                                    f"Line {idx + 1} ({target.name_id}): Slot choice '{chosen_item.name_id}' is out of stock"
                                )

        return errors
