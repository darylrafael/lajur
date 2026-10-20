"""Diagnostic script to inspect 10 turns:
Model output vs Gold Intent vs Old Scorer vs New Scorer.
"""
import json
import os

import dotenv
from lajur_cart.menu_service import MenuService
from openai import OpenAI

dotenv.load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")
client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
menu_service = MenuService("eval/menu/menu.json")

# Load gold intents and scenarios
with open("eval/datasets/v0/gold_intents.jsonl", "r", encoding="utf-8") as f:
    gold_map = {json.loads(line)["scenario_id"]: json.loads(line) for line in f if line.strip()}

with open("eval/datasets/v0/scenarios.jsonl", "r", encoding="utf-8") as f:
    scen_map = {json.loads(line)["id"]: json.loads(line) for line in f if line.strip()}

test_sids = [
    "scen_001", "scen_002", "scen_003", "scen_005", "scen_007",
    "scen_014", "scen_016", "scen_018", "scen_020", "scen_026"
]

print("=" * 80)
print("AUDIT OF 10 TURNS: OLD PROMPT & OLD SCORER VS GOLD INTENTS")
print("=" * 80)

for sid in test_sids:
    scen = scen_map[sid]
    gold = gold_map[sid]
    user_text = scen["utterances"][0]
    expected_cart = scen.get("expected_cart", {})
    gold_intents = gold.get("intents", [])

    # Call with the OLD prompt from benchmark_g1c.py
    resp = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {"role": "system", "content": "Kamu kasir AI. Balas JSON format: {\"reply\": \"...\", \"intents\": [{\"type\": \"add_item\", \"name\": \"...\"}]}"},
            {"role": "user", "content": user_text}
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    raw_content = resp.choices[0].message.content or ""

    # Old scorer logic from benchmark_g1c.py:
    # "accuracy": 1.0 if any(it.get("item_id") in full_text.lower() for it in expected_cart.get("items", [])) else 0.5
    expected_items = expected_cart.get("items", [])
    matched_ids = [it.get("item_id") for it in expected_items if it.get("item_id") in raw_content.lower()]
    old_score = 1.0 if matched_ids else 0.5

    print(f"\n--- Scenario: {sid} ---")
    print(f"User Utterance : \"{user_text}\"")
    print(f"Model Output   : {raw_content.strip()}")
    print(f"Gold Intents   : {json.dumps(gold_intents, ensure_ascii=False)}")
    print(f"Expected Cart  : {json.dumps(expected_cart, ensure_ascii=False)}")
    print("Old Scorer Match Check:")
    print(f"  Target item_ids to look for substring: {[it.get('item_id') for it in expected_items]}")
    print(f"  Matched item_ids in text: {matched_ids}")
    print(f"  Old Scorer Result: {old_score} ({old_score * 100:.1f}%)")
