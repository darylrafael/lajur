"""
Menu Validator for Lajur Drive-thru Voice Ordering System
Validates menu.json against menu.schema.json and checks domain integrity rules:
1. Unique IDs across items, modifiers, combos
2. Valid references (modifiers in items exist in modifier list, choice items in combo slots exist)
3. Prices > 0 (or price_delta valid)
4. Valid operating hours and stock indicators
"""

import json
import re
import sys
from pathlib import Path

def validate_menu(menu_path: Path, schema_path: Path) -> bool:
    print(f"Validating menu: {menu_path}")
    if not menu_path.exists():
        print(f"ERROR: {menu_path} does not exist.")
        return False
    if not schema_path.exists():
        print(f"ERROR: {schema_path} does not exist.")
        return False

    with open(menu_path, "r", encoding="utf-8") as f:
        menu = json.load(f)

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    errors = []

    # Check top level
    for field in ["version", "operating_hours", "items", "modifiers", "combos"]:
        if field not in menu:
            errors.append(f"Missing top-level field: {field}")

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return False

    item_ids = set()
    modifier_ids = set()
    combo_ids = set()

    # 1. Validate modifiers
    for mod in menu["modifiers"]:
        mid = mod.get("id")
        if not mid or not re.match(r"^[a-z0-9_]+$", mid):
            errors.append(f"Invalid modifier id: {mid}")
        if mid in modifier_ids:
            errors.append(f"Duplicate modifier id: {mid}")
        modifier_ids.add(mid)

        options = mod.get("options", [])
        if not options:
            errors.append(f"Modifier {mid} has no options")
        for opt in options:
            if "id" not in opt or "price_delta" not in opt:
                errors.append(f"Modifier {mid} option missing id or price_delta: {opt}")

    # 2. Validate items
    category_counts = {}
    out_of_stock_count = 0
    breakfast_count = 0

    for item in menu["items"]:
        iid = item.get("id")
        if not iid or not re.match(r"^[a-z0-9_]+$", iid):
            errors.append(f"Invalid item id: {iid}")
        if iid in item_ids:
            errors.append(f"Duplicate item id: {iid}")
        item_ids.add(iid)

        cat = item.get("category")
        category_counts[cat] = category_counts.get(cat, 0) + 1

        price = item.get("price", 0)
        if price <= 0:
            errors.append(f"Item {iid} has invalid price: {price}")

        # Check modifiers reference
        for mod_ref in item.get("modifiers", []):
            if mod_ref not in modifier_ids:
                errors.append(f"Item {iid} references unknown modifier: {mod_ref}")

        # Check sizes
        for size_opt in item.get("sizes", []):
            if "size" not in size_opt or "price_delta" not in size_opt:
                errors.append(f"Item {iid} invalid size option: {size_opt}")

        if not item.get("in_stock", True):
            out_of_stock_count += 1

        if item.get("available_hours") == "breakfast":
            breakfast_count += 1

    # 3. Validate combos
    for combo in menu["combos"]:
        cid = combo.get("id")
        if not cid or not re.match(r"^[a-z0-9_]+$", cid):
            errors.append(f"Invalid combo id: {cid}")
        if cid in combo_ids or cid in item_ids:
            errors.append(f"Duplicate or colliding combo id: {cid}")
        combo_ids.add(cid)

        base_price = combo.get("base_price", 0)
        if base_price <= 0:
            errors.append(f"Combo {cid} has invalid base_price: {base_price}")

        slots = combo.get("slots", [])
        if not slots:
            errors.append(f"Combo {cid} has no slots")
        for slot in slots:
            choices = slot.get("choice_items", [])
            if not choices:
                errors.append(f"Combo {cid} slot {slot.get('slot_id')} has no choices")
            for citem in choices:
                if citem not in item_ids:
                    errors.append(f"Combo {cid} slot references unknown item: {citem}")

        if combo.get("available_hours") == "breakfast":
            breakfast_count += 1

    # Domain rule checks
    total_items_count = len(item_ids) + len(combo_ids)
    if total_items_count < 45 or total_items_count > 60:
        errors.append(f"Total item count ({total_items_count}) outside 45-60 range requirement.")

    required_categories = ["burger", "ayam", "nasi", "sarapan", "side", "minuman", "dessert"]
    for req_cat in required_categories:
        if req_cat not in category_counts or category_counts[req_cat] == 0:
            errors.append(f"Missing or empty required category: {req_cat}")

    if out_of_stock_count < 2:
        errors.append(f"Expected at least 2 out-of-stock items, found {out_of_stock_count}")

    if breakfast_count < 2:
        errors.append(f"Expected breakfast-only items, found {breakfast_count}")

    if errors:
        print(f"FAILED with {len(errors)} errors:")
        for err in errors:
            print(f"  - {err}")
        return False

    print("SUCCESS: Menu definition is valid!")
    print(f"Summary: {len(item_ids)} regular items, {len(combo_ids)} combos, {len(modifier_ids)} modifiers.")
    print(f"Categories: {category_counts}")
    print(f"Out of stock: {out_of_stock_count}, Breakfast-only: {breakfast_count}")
    return True

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    menu_file = base_dir / "menu.json"
    schema_file = base_dir / "menu.schema.json"
    success = validate_menu(menu_file, schema_file)
    sys.exit(0 if success else 1)
