"""Generate the recording script manifest and table for human recordings."""

import json
from pathlib import Path

# Load all scenarios
scenarios_path = Path("eval/datasets/v0/scenarios.jsonl")
with open(scenarios_path, "r", encoding="utf-8") as f:
    scenarios = [json.loads(line) for line in f if line.strip()]

simple = [s for s in scenarios if "simple" in s.get("tags", []) and s.get("lang_mix") == "id"][:10]
mixed = [s for s in scenarios if s.get("lang_mix") in ("mixed", "en") and "correction" not in s.get("tags", [])][:15]
corrections = [s for s in scenarios if "correction" in s.get("tags", []) or "undo" in s.get("tags", [])][:5]
quantities = [s for s in scenarios if "quantity" in s.get("tags", []) and "correction" not in s.get("tags", [])][:5]
hesitations = [s for s in scenarios if "hesitation" in s.get("tags", [])][:5]

selected = simple + mixed + corrections + quantities + hesitations
assert len(selected) == 40, f"Expected 40, got {len(selected)}"

# Output manifest CSV: utterance_id,scenario_id,reference_transcript,condition,filename
manifest_lines = ["utterance_id,scenario_id,condition,reference_transcript,filename\n"]

for idx, s in enumerate(selected, 1):
    scen_id = s["id"]
    ref_text = " ".join(s["utterances"]).replace('"', '""')
    for cond in ("quiet", "noise", "helmet"):
        utt_id = f"real_{idx:03d}_{cond}"
        filename = f"{utt_id}.wav"
        manifest_lines.append(f'{utt_id},{scen_id},{cond},"{ref_text}",{filename}\n')

manifest_path = Path("eval/audio/real/manifest.csv")
with open(manifest_path, "w", encoding="utf-8") as f:
    f.writelines(manifest_lines)

print(f"Successfully generated {manifest_path} with {len(manifest_lines) - 1} entries.")

# Output markdown lines for docs/spikes/recording-script.md
md_lines = []
for idx, s in enumerate(selected, 1):
    category = "Simple Indonesian" if idx <= 10 else ("Mixed ID-EN" if idx <= 25 else ("Correction / Undo" if idx <= 30 else ("Quantities & Combos" if idx <= 35 else "Hesitations & Pauses")))
    utt_text = " ".join(s["utterances"])
    md_lines.append(f"| {idx:02d} | `{s['id']}` | **{category}** | {utt_text} | `real_{idx:03d}_quiet.wav`<br>`real_{idx:03d}_noise.wav`<br>`real_{idx:03d}_helmet.wav` |")

with open("eval/scripts/recording_table.tmp", "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))
