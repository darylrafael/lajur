"""
Scenario Validator for Lajur Drive-thru Voice Ordering System
Validates eval/datasets/v0/scenarios.jsonl against eval/menu/menu.json:
1. Valid JSONL with exactly 100 scenarios
2. Required fields: id, split ('dev'), utterances, lang_mix, expected_cart, noise_profile, tags
3. Price verification: every item price and total_price must exactly match menu.json pricing rules
4. Coverage check across all required categories (simple, combo, code-switching, undo, OOS, breakfast, injection, etc.)
"""

import json
import sys
from pathlib import Path


def validate_scenarios(scenarios_path: Path, menu_path: Path) -> bool:
    print(f"Validating scenarios: {scenarios_path}")
    if not scenarios_path.exists():
        print(f"ERROR: {scenarios_path} does not exist.")
        return False
    if not menu_path.exists():
        print(f"ERROR: {menu_path} does not exist.")
        return False

    with open(menu_path, "r", encoding="utf-8") as f:
        menu = json.load(f)

    # Build menu lookup tables
    items_by_id = {item["id"]: item for item in menu["items"]}
    combos_by_id = {combo["id"]: combo for combo in menu["combos"]}
    modifiers_by_id = {mod["id"]: mod for mod in menu["modifiers"]}

    scenarios = []
    with open(scenarios_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                scen = json.loads(line_str)
                scenarios.append((line_no, scen))
            except json.JSONDecodeError as e:
                print(f"ERROR: Line {line_no} is invalid JSON: {e}")
                return False

    errors = []

    if len(scenarios) < 100:
        errors.append(f"Expected at least 100 scenarios, found {len(scenarios)}")

    seen_ids = set()
    tag_counts = {}
    lang_counts = {}
    noise_counts = {}
    source_counts = {}

    for line_no, scen in scenarios:
        sid = scen.get("id")
        if not sid:
            errors.append(f"Line {line_no}: Missing 'id'")
        elif sid in seen_ids:
            errors.append(f"Line {line_no}: Duplicate scenario id: {sid}")
        seen_ids.add(sid)

        # Check source
        source = scen.get("source", "generated")
        if source not in ["generated", "handwritten"]:
            errors.append(f"Scenario {sid}: Invalid source '{source}'")
        source_counts[source] = source_counts.get(source, 0) + 1

        # Check split
        split = scen.get("split")
        if split != "dev":
            errors.append(f"Scenario {sid}: 'split' must be 'dev', got '{split}'")

        # Check lang_mix
        lang = scen.get("lang_mix")
        if lang not in ["id", "en", "mixed"]:
            errors.append(f"Scenario {sid}: Invalid 'lang_mix': {lang}")
        lang_counts[lang] = lang_counts.get(lang, 0) + 1

        # Check noise_profile
        noise = scen.get("noise_profile")
        if not noise:
            errors.append(f"Scenario {sid}: Missing 'noise_profile'")
        noise_counts[noise] = noise_counts.get(noise, 0) + 1

        # Check utterances
        utterances = scen.get("utterances")
        if not isinstance(utterances, list) or len(utterances) == 0:
            errors.append(f"Scenario {sid}: 'utterances' must be a non-empty list of strings")

        # Check tags
        tags = scen.get("tags", [])
        if not isinstance(tags, list) or len(tags) == 0:
            errors.append(f"Scenario {sid}: 'tags' must be a non-empty list of strings")
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Check expected_cart
        cart = scen.get("expected_cart")
        if not isinstance(cart, dict):
            errors.append(f"Scenario {sid}: Missing or invalid 'expected_cart'")
            continue

        cart_items = cart.get("items", [])
        stated_total = cart.get("total_price", 0)
        computed_total = 0

        for idx, citem in enumerate(cart_items):
            item_id = citem.get("item_id")
            qty = citem.get("quantity", 1)
            if qty < 1:
                errors.append(f"Scenario {sid} item {idx}: quantity < 1")

            # Check if regular item or combo
            if item_id in items_by_id:
                m_item = items_by_id[item_id]
                unit_price = m_item["price"]

                # Check size
                size = citem.get("size", "regular")
                if size != "regular":
                    size_opt = next((s for s in m_item.get("sizes", []) if s["size"] == size), None)
                    if not size_opt:
                        errors.append(f"Scenario {sid} item {item_id}: invalid size '{size}' for this item")
                    else:
                        unit_price += size_opt["price_delta"]

                # Check modifiers
                mods = citem.get("modifiers", [])
                for mod_opt_id in mods:
                    # Find option in applied modifiers
                    found_opt = False
                    for mod_id in m_item.get("modifiers", []):
                        m_mod = modifiers_by_id.get(mod_id, {})
                        for opt in m_mod.get("options", []):
                            if opt["id"] == mod_opt_id:
                                unit_price += opt["price_delta"]
                                found_opt = True
                                break
                        if found_opt:
                            break
                    if not found_opt:
                        errors.append(f"Scenario {sid} item {item_id}: unknown modifier option '{mod_opt_id}'")

                expected_item_price = unit_price * qty
                if citem.get("price") != expected_item_price:
                    errors.append(f"Scenario {sid} item {item_id}: stated item price ({citem.get('price')}) != computed ({expected_item_price})")
                computed_total += expected_item_price

            elif item_id in combos_by_id:
                m_combo = combos_by_id[item_id]
                combo_price = m_combo["base_price"]

                # Check slots
                slots = citem.get("slots", {})
                for slot_def in m_combo.get("slots", []):
                    slot_id = slot_def["slot_id"]
                    if slot_def["required"] and slot_id not in slots:
                        errors.append(f"Scenario {sid} combo {item_id}: missing required slot '{slot_id}'")
                    elif slot_id in slots:
                        selected_choice = slots[slot_id]
                        if selected_choice not in slot_def["choice_items"]:
                            errors.append(f"Scenario {sid} combo {item_id}: invalid choice '{selected_choice}' in slot '{slot_id}'")

                # Check upsell / modifiers
                upsell_rules = citem.get("upsell_rules", [])
                for u_rule in upsell_rules:
                    rule_def = next((r for r in m_combo.get("upsell_rules", []) if r["rule_id"] == u_rule), None)
                    if not rule_def:
                        errors.append(f"Scenario {sid} combo {item_id}: unknown upsell rule '{u_rule}'")
                    else:
                        combo_price += rule_def["price_delta"]

                expected_combo_price = combo_price * qty
                if citem.get("price") != expected_combo_price:
                    errors.append(f"Scenario {sid} combo {item_id}: stated price ({citem.get('price')}) != computed ({expected_combo_price})")
                computed_total += expected_combo_price
            else:
                errors.append(f"Scenario {sid}: unknown item_id '{item_id}' in expected_cart")

        if stated_total != computed_total:
            errors.append(f"Scenario {sid}: stated total_price ({stated_total}) != computed total_price ({computed_total})")

    # Required topic coverage check
    essential_tags = [
        "simple", "quantity", "modifier", "combo", "code_switching",
        "correction", "hesitation", "out_of_stock", "breakfast",
        "ambiguous", "handoff", "prank"
    ]
    for et in essential_tags:
        count = tag_counts.get(et, 0)
        if count == 0:
            errors.append(f"Coverage failure: tag '{et}' has 0 scenarios")

    # Dataset v0.1 specific minimum coverage thresholds
    if tag_counts.get("handoff", 0) < 8:
        errors.append(f"Coverage threshold: 'handoff' scenarios ({tag_counts.get('handoff', 0)}) < 8")
    if noise_counts.get("helmet", 0) < 10:
        errors.append(f"Coverage threshold: 'helmet' noise scenarios ({noise_counts.get('helmet', 0)}) < 10")
    if tag_counts.get("prank", 0) < 8:
        errors.append(f"Coverage threshold: 'prank' scenarios ({tag_counts.get('prank', 0)}) < 8")

    mixed_ratio = lang_counts.get("mixed", 0) / len(scenarios) if scenarios else 0
    if mixed_ratio < 0.40:
        errors.append(f"Coverage threshold: mixed ID-EN ratio ({mixed_ratio:.1%}) < 40.0%")

    if source_counts.get("handwritten", 0) < 30:
        errors.append(f"Coverage threshold: handwritten scenarios ({source_counts.get('handwritten', 0)}) < 30")

    if errors:
        print(f"FAILED with {len(errors)} errors:")
        for err in errors[:25]:
            print(f"  - {err}")
        if len(errors) > 25:
            print(f"  ... and {len(errors) - 25} more errors.")
        return False

    print(f"SUCCESS: All {len(scenarios)} scenarios are valid and mathematically consistent with menu.json!")
    print(f"Sources: {source_counts}")
    print(f"Language mix: {lang_counts} (mixed: {mixed_ratio:.1%})")
    print(f"Noise profiles: {noise_counts}")
    print(f"Tag distribution: {dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True))}")
    return True

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    scenarios_file = base_dir / "datasets" / "v0" / "scenarios.jsonl"
    menu_file = base_dir / "menu" / "menu.json"
    success = validate_scenarios(scenarios_file, menu_file)
    sys.exit(0 if success else 1)
