"""Extract public menu fields from eval/menu/menu.json into apps/web/src/data/menu.json.

Excludes internal prompt aliases and private mappings.
Filters items by in_stock and operating hours status for UI display.
"""

from __future__ import annotations

import json
from pathlib import Path


def generate_public_menu() -> None:
    root = Path(__file__).resolve().parents[3]
    src_path = root / "eval" / "menu" / "menu.json"
    out_path = root / "apps" / "web" / "src" / "data" / "menu.json"

    with open(src_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    public_menu = {
        "version": raw.get("version", "1.0"),
        "currency": raw.get("currency", "IDR"),
        "operating_hours": raw.get("operating_hours", {}),
        "categories": [
            {"id": "combo", "name_id": "Paket Hemat", "name_en": "Combos & Meals"},
            {"id": "burger", "name_id": "Burger", "name_en": "Burgers"},
            {"id": "ayam", "name_id": "Ayam & Nasi", "name_en": "Chicken & Rice"},
            {"id": "side", "name_id": "Camilan & Sides", "name_en": "Sides & Snacks"},
            {"id": "minuman", "name_id": "Minuman", "name_en": "Beverages"},
            {"id": "sarapan", "name_id": "Menu Sarapan", "name_en": "Breakfast"},
            {"id": "dessert", "name_id": "Pencuci Mulut", "name_en": "Desserts"},
        ],
        "items": [],
        "combos": [],
        "modifiers": raw.get("modifiers", []),
    }

    for item in raw.get("items", []):
        public_menu["items"].append(
            {
                "id": item["id"],
                "category": item["category"],
                "name_id": item["name_id"],
                "name_en": item["name_en"],
                "price": item["price"],
                "sizes": item.get("sizes", []),
                "modifiers": item.get("modifiers", []),
                "available_hours": item.get("available_hours", "all_day"),
                "in_stock": item.get("in_stock", True),
            }
        )

    for combo in raw.get("combos", []):
        public_menu["combos"].append(
            {
                "id": combo["id"],
                "category": "combo",
                "name_id": combo["name_id"],
                "name_en": combo["name_en"],
                "base_price": combo["base_price"],
                "slots": combo.get("slots", []),
                "upsell_rules": combo.get("upsell_rules", []),
                "available_hours": combo.get("available_hours", "regular"),
                "in_stock": combo.get("in_stock", True),
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(public_menu, f, indent=2, ensure_ascii=False)

    num_items = len(public_menu["items"])
    num_combos = len(public_menu["combos"])
    print(f"Successfully generated {out_path}: {num_items} items, {num_combos} combos")


if __name__ == "__main__":
    generate_public_menu()
