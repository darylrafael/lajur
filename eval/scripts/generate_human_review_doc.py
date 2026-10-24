"""Generate docs/spikes/week-03-human-review.md.

Produces a side-by-side comparison table of 20 scenarios:
11 correction/undo scenarios + 9 seeded random scenarios (seed=42).
Clearly labeled: "unverified: agent-authored for human review".
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_PATH = ROOT / "eval" / "datasets" / "v0" / "scenarios.jsonl"
GOLD_V2_PATH = ROOT / "eval" / "datasets" / "v0" / "gold_intents_v2.jsonl"
OUT_PATH = ROOT / "docs" / "spikes" / "week-03-human-review.md"

scenarios = {
    s["id"]: s for s in [json.loads(line) for line in open(SCENARIOS_PATH, encoding="utf-8")]
}
gold_v2 = {
    s["scenario_id"]: s for s in [json.loads(line) for line in open(GOLD_V2_PATH, encoding="utf-8")]
}

selected_20 = [
    "scen_071",
    "scen_072",
    "scen_073",
    "scen_074",
    "scen_075",
    "scen_076",
    "scen_077",
    "scen_078",
    "scen_079",
    "scen_080",
    "scen_134",
    "scen_004",
    "scen_014",
    "scen_015",
    "scen_018",
    "scen_029",
    "scen_032",
    "scen_036",
    "scen_092",
    "scen_105",
]


def generate():
    lines = [
        "# Week 03 Human Review: Sample 20 Scenarios",
        "",
        "> **Label:** unverified: agent-authored for human review",
        ">",
        "> Dokumen ini memuat 20 sampel skenario pesanan untuk verifikasi manusia.",
        "> Mencakup seluruh 11 skenario koreksi/pembatalan (correction/undo) plus 9 skenario acak terdistribusi (random seed: 42).",
        "",
        "---",
        "",
    ]

    for sid in selected_20:
        sc = scenarios[sid]
        gv = gold_v2[sid]
        lines.append(f"## Skenario `{sid}`")
        lines.append(f"**Tags:** `{sc.get('tags', [])}`")
        lines.append("")
        lines.append("### Transkrip Percakapan (Utterances)")
        for i, u in enumerate(sc["utterances"], 1):
            lines.append(f'{i}. *"{u}"*')
        lines.append("")
        lines.append("### Side-by-Side: Gold Intents vs Expected Cart")
        lines.append("")
        lines.append(
            "| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |"
        )
        lines.append("| :--- | :--- |")

        intents_parts = []
        for it in gv["intents"]:
            params = {k: v for k, v in it.items() if k != "type" and v not in (None, [], {})}
            param_str = f" `{json.dumps(params)}`" if params else ""
            intents_parts.append(f"• **`{it['type']}`**{param_str}")
        intents_str = "<br>".join(intents_parts)

        exp = sc["expected_cart"]
        item_parts = []
        for it in exp.get("items", []):
            detail = f"• `{it['item_id']}` x{it.get('quantity', 1)} ({it.get('size', 'regular')}) Rp {it.get('price', 0):,}"
            if it.get("modifiers"):
                detail += f"<br>&nbsp;&nbsp;*modifiers:* `{it['modifiers']}`"
            if it.get("slots"):
                detail += f"<br>&nbsp;&nbsp;*slots:* `{it['slots']}`"
            if it.get("upsell_rules"):
                detail += f"<br>&nbsp;&nbsp;*upsell:* `{it['upsell_rules']}`"
            item_parts.append(detail)

        items_desc = "<br>".join(item_parts) if item_parts else "*[Keranjang Kosong]*"
        cart_str = f"**Status:** `{exp.get('status')}`<br>**Total:** Rp {exp.get('total_price', 0):,}<br>**Items:**<br>{items_desc}"

        lines.append(f"| {intents_str} | {cart_str} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written review doc to {OUT_PATH}")


if __name__ == "__main__":
    generate()
