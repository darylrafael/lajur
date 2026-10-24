"""Alias Coverage Report Script.

Scans all scenarios in eval/datasets/v0/scenarios.jsonl and checks whether
every item in expected_cart can be resolved from the scenario utterances
via MenuService.resolve_alias().
"""

import json
import re
from pathlib import Path

from lajur_cart.menu_service import MenuService


def generate_alias_coverage_report() -> tuple[list[dict], str]:
    ms = MenuService("eval/menu/menu.json")
    scenarios_path = Path("eval/datasets/v0/scenarios.jsonl")
    scenarios = [
        json.loads(line)
        for line in scenarios_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    findings = []

    for s in scenarios:
        exp_items = {it["item_id"]: it for it in s.get("expected_cart", {}).get("items", [])}
        if not exp_items:
            continue

        utterance_text = " ".join(s["utterances"])
        words = re.findall(r"\b\w+\b", utterance_text.lower())

        found_item_ids = {}
        for n in range(1, 7):
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i : i + n])
                resolved = ms.resolve_alias(phrase)
                if resolved:
                    found_item_ids[resolved.id] = phrase

        unresolved = set(exp_items.keys()) - set(found_item_ids.keys())
        if unresolved:
            findings.append(
                {
                    "scenario_id": s["id"],
                    "utterances": s["utterances"],
                    "unresolved_item_ids": sorted(list(unresolved)),
                    "expected_items": exp_items,
                }
            )

    # Generate markdown report
    md_lines = [
        "# Alias Coverage Report (Minggu 3)",
        "",
        f"**Total Scenarios Evaluated:** {len(scenarios)}",
        f"**Scenarios with Unresolved Item Mentions:** {len(findings)}",
        "",
        "## Unresolved Item Mentions per Scenario",
        "",
        "| Scenario ID | Utterance | Target Item ID | Missing Spoken Phrase Candidate |",
        "|---|---|---|---|",
    ]

    for f in findings:
        scen_id = f["scenario_id"]
        utt = " / ".join(f["utterances"])
        for target_id in f["unresolved_item_ids"]:
            target_obj = ms.get_item_or_combo(target_id)
            name = target_obj.name_id if target_obj else target_id
            md_lines.append(
                f'| `{scen_id}` | *"{utt}"* | `{target_id}` ({name}) | To be added to `aliases` |'
            )

    md_lines.append("")
    report_text = "\n".join(md_lines)
    return findings, report_text


if __name__ == "__main__":
    findings, report = generate_alias_coverage_report()
    out_file = Path("docs/eval/alias-coverage-report.md")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")
    print(f"Report generated: {len(findings)} unresolved scenarios found.")
    print(f"Saved to {out_file}")
