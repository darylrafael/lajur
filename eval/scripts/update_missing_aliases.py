"""Script to add missing aliases identified in alias coverage report to menu.json."""

import json
from pathlib import Path

MENU_PATH = Path("eval/menu/menu.json")

MISSING_ALIASES = {
    "kopi_susu_aren": ["kopi susu gula aren"],
    "burger_sapi_tunggal": ["single beef burger", "single beef burgers"],
    "nugget_ayam_6": ["nugget ayam isi 6", "nugget ayam yang isi 6"],
    "soda_kola": ["colas"],
    "paket_hemat_ayam_2": ["paket hemat ayam dua potong", "paket ayam dua potong"],
    "paket_hemat_burger_ganda": ["paket hemat burger ganda"],
    "ayam_goreng_pedas": ["spicy fried chicken", "fried chicken spicy"],
    "kue_cokelat_lumer": ["molten chocolate cake"],
    "bubur_ayam_spesial": ["bubur ayam spesial"],
    "paket_hemat_ayam_1": [
        "paket ayam satu potong",
        "paket ayam spicy satu potong",
        "paket hemat ayam satu potong",
    ],
    "muffin_telur_keju": ["egg and cheese muffin"],
    "nugget_ayam_9": ["9 pcs chicken nuggets"],
    "es_krim_vanila": ["vanilla cone"],
    "paket_hemat_burger_tunggal": ["paket hemat burger tunggal"],
}


def update_menu():
    data = json.loads(MENU_PATH.read_text(encoding="utf-8"))

    added_count = 0
    # Update items
    for item in data.get("items", []):
        item_id = item["id"]
        if item_id in MISSING_ALIASES:
            for alias in MISSING_ALIASES[item_id]:
                if alias not in item["aliases"]:
                    item["aliases"].append(alias)
                    added_count += 1
                    print(f"Added alias '{alias}' to item '{item_id}'")

    # Update combos
    for combo in data.get("combos", []):
        combo_id = combo["id"]
        if combo_id in MISSING_ALIASES:
            for alias in MISSING_ALIASES[combo_id]:
                if alias not in combo["aliases"]:
                    combo["aliases"].append(alias)
                    added_count += 1
                    print(f"Added alias '{alias}' to combo '{combo_id}'")

    MENU_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Finished updating menu.json: {added_count} aliases added.")


if __name__ == "__main__":
    update_menu()
