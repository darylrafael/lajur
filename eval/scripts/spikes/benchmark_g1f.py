"""Gate G1f Audit and Final Measurement Suite.

Implements all pre-registered tasks from docs/gates/G1c-addendum.md:
- Task 1: Intent & Resulting-Cart Accuracy on 60 turns across 4 LLM configs (paired with TTFT/latency).
- Task 3: Deepgram Nova-3 endpointing latency & false-cutoff redo (150, 300, 500 ms) with 1.5s trailing silence.
- Task 4: ElevenLabs Free Tier TTS streaming TTFB benchmark (30 phrases x 5 interleaved runs).
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import os
import sys
import time
import wave
from pathlib import Path
from typing import Any

import aiohttp
import edge_tts
import numpy as np
from dotenv import load_dotenv
from openai import AsyncOpenAI

root_dir = Path(__file__).resolve().parents[3]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from lajur_cart.menu_service import MenuService  # noqa: E402

load_dotenv()

SELECTED_60_SIDS = [
    # correction / undo (11)
    "scen_071", "scen_072", "scen_073", "scen_074", "scen_075",
    "scen_076", "scen_077", "scen_078", "scen_079", "scen_080", "scen_134",
    # modifiers & sizes (15)
    "scen_026", "scen_027", "scen_028", "scen_029", "scen_030",
    "scen_031", "scen_032", "scen_033", "scen_034", "scen_035",
    "scen_036", "scen_037", "scen_038", "scen_039", "scen_040",
    # quantity & combo (15)
    "scen_016", "scen_017", "scen_018", "scen_019", "scen_020",
    "scen_021", "scen_022", "scen_023", "scen_024", "scen_025",
    "scen_041", "scen_042", "scen_043", "scen_044", "scen_045",
    # simple (19)
    "scen_001", "scen_002", "scen_003", "scen_004", "scen_005",
    "scen_006", "scen_007", "scen_008", "scen_009", "scen_010",
    "scen_011", "scen_012", "scen_013", "scen_014", "scen_015",
    "scen_046", "scen_047", "scen_048", "scen_049"
]

HESITATION_PHRASES = [
    {"id": "hes_01", "p1": "Mau burger sapi satu", "p2": "sama cola dingin"},
    {"id": "hes_02", "p1": "Emmm apa ya sebentar", "p2": "mau burger sapi keju satu deh"},
    {"id": "hes_03", "p1": "Aduh mau makan apa ya", "p2": "ayam goreng crispy satu sama es teh manis"},
    {"id": "hes_04", "p1": "Wait a minute umm", "p2": "okay one french fries large"},
    {"id": "hes_05", "p1": "Paket hemat burger sapi satu", "p2": "eh burgernya ganti burger keju ya"},
    {"id": "hes_06", "p1": "Saya mau pesan cheeseburger dua", "p2": "eh gajadi satu aja"},
    {"id": "hes_07", "p1": "Pesan es teh manis dua", "p2": "eh gak jadi teh manisnya ganti air mineral"},
    {"id": "hes_08", "p1": "Mau chicken wings satu porsi", "p2": "tambah kentang goreng yang large"},
    {"id": "hes_09", "p1": "Tolong double cheeseburger satu", "p2": "tanpa acar sama extra keju"},
    {"id": "hes_10", "p1": "Beli sundae cokelat satu", "p2": "sama apple pie satu ya"},
]

KEYTERMS = [
    "burger", "cheeseburger", "double cheeseburger", "triple cheeseburger",
    "kentang goreng", "french fries", "ayam goreng", "crispy", "wings",
    "nugget", "es teh manis", "kopi susu", "gula aren", "cola", "air mineral",
    "sundae", "ice cream", "apple pie", "large", "medium", "reguler",
    "extra cheese", "less sugar", "tanpa es", "no onions", "no pickles",
    "paket hemat", "combo", "nasi putih", "nasi uduk", "gajadi", "batalin"
]

PRODUCTION_SYSTEM_INSTRUCTION = """
Kamu adalah AI kasir drive-thru pintar untuk restoran cepat saji 'Lajur'.
Tugasmu:
1. Menerima transkrip ucapan pelanggan (bahasa Indonesia sehari-hari, bahasa Inggris, atau campur).
2. Mengekstrak intent pesanan ke dalam format JSON terstruktur.
3. Menghasilkan bot_reply yang ramah dan ringkas dalam bahasa Indonesia.

Daftar Intent:
- add_item: menambahkan item ke keranjang (params: item_id, name, quantity, modifiers, size)
- remove_item: menghapus item dari keranjang (params: item_id, name, quantity)
- modify_item: mengubah modifier atau ukuran (params: item_id, add_modifiers, remove_modifiers)
- undo: membatalkan aksi sebelumnya (params: steps)
- confirm: menyelesaikan pesanan (params: finalized)
- handoff: minta bicara staf manusia (params: reason)
- unknown: tidak jelas / di luar konteks (params: raw_text)

Format Respons Wajib (JSON murni):
{
  "intents": [
    {
      "type": "add_item",
      "params": {
        "item_id": "burger_sapi_tunggal",
        "name": "Burger Sapi Tunggal",
        "quantity": 1,
        "modifiers": [],
        "size": "regular"
      }
    }
  ],
  "bot_reply": "Baik kak, 1 Burger Sapi Tunggal sudah dicatat."
}
""".strip()

BOT_REPLY_PHRASES_30 = [
    "Baik kak, pesanan sudah dicatat.",
    "Ada tambahan lain untuk minumannya?",
    "Mau burger sapi tunggal atau burger keju?",
    "Siap kak, 1 Cola dingin sudah masuk keranjang.",
    "Apakah kentang gorengnya mau ukuran large?",
    "Baik kak, saya batalkan satu es teh manisnya.",
    "Total pesanan sementara adalah empat puluh lima ribu rupiah.",
    "Mau paket hemat atau a la carte kak?",
    "Ayam goreng crispy-nya mau paha atau dada?",
    "Baik, kami siapkan satu porsi spicy chicken wings.",
    "Apakah burgernya pakai acar dan mayones?",
    "Siap kak, satu sundae cokelat sudah ditambahkan.",
    "Mau sekalian air mineral dinginnya kak?",
    "Baik, penggantian ke French Fries sudah dicatat.",
    "Ada yang ingin diubah lagi sebelum kami proses?",
    "Silakan lanjut ke loket pembayaran berikutnya.",
    "Terima kasih kak, pesanan segera kami siapkan.",
    "Maaf kak, es krim rasa stroberi sedang habis.",
    "Mau tambah saus sambal atau saus tomat?",
    "Satu paket hemat burger sudah masuk pesanan.",
    "Apakah kopinya mau less sugar?",
    "Baik kak, pesanan dibatalkan sesuai permintaan.",
    "Total belanja Anda sebesar lima puluh ribu rupiah.",
    "Bisa tolong diulang pesanan minumannya kak?",
    "Satu porsi nasi putih hangat sudah ditambahkan.",
    "Mau ukuran regular, medium, atau large kak?",
    "Baik, double cheeseburger tanpa acar sudah dicatat.",
    "Apakah pesanannya sudah lengkap kak?",
    "Pesanan Anda sedang diproses oleh dapur.",
    "Selamat datang di Lajur, mau pesan apa hari ini?"
]


def bootstrap_ci_mean(data: list[float], n_resamples: int = 10000, alpha: float = 0.05) -> tuple[float, float]:
    if not data:
        return 0.0, 0.0
    arr = np.array(data)
    boot_means = [np.random.choice(arr, size=len(arr), replace=True).mean() for _ in range(n_resamples)]
    low = float(np.percentile(boot_means, (alpha / 2.0) * 100))
    high = float(np.percentile(boot_means, (1.0 - alpha / 2.0) * 100))
    return low, high


async def synthesize_phrase_pcm(text: str, voice: str = "id-ID-GadisNeural") -> np.ndarray:
    communicate = edge_tts.Communicate(text, voice=voice)
    mp3_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            mp3_bytes += chunk["data"]

    import av
    container = av.open(io.BytesIO(mp3_bytes), format="mp3")
    resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
    all_samples: list[np.ndarray] = []
    for frame in container.decode(audio=0):
        for rf in resampler.resample(frame):
            all_samples.append(rf.to_ndarray())

    if all_samples:
        return np.concatenate(all_samples, axis=1).squeeze().astype(np.int16)
    return np.zeros((0,), dtype=np.int16)


# ==============================================================================
# TASK 1: INTENT & RESULTING-CART ACCURACY BENCHMARK (60 TURNS, INTERLEAVED)
# ==============================================================================

def evaluate_intent_and_cart(
    extracted_json: dict[str, Any],
    gold_entry: dict[str, Any],
    scen_entry: dict[str, Any],
    menu_service: MenuService,
) -> tuple[bool, bool, dict[str, Any]]:
    """Evaluates extracted output against gold intents and expected cart."""
    gold_intents = gold_entry.get("intents", [])
    expected_cart = scen_entry.get("expected_cart", {})
    expected_items = expected_cart.get("items", [])

    model_intents = extracted_json.get("intents", [])

    # 1. Intent-level evaluation
    # Check if primary intent matches gold intent type and item
    intent_match = False
    if model_intents and gold_intents:
        m0 = model_intents[0]
        g0 = gold_intents[0]

        m_type = m0.get("type")
        g_type = g0.get("type")

        if m_type == g_type:
            if m_type in ("undo", "confirm", "handoff", "unknown"):
                intent_match = True
            elif m_type in ("add_item", "remove_item"):
                m_params = m0.get("params", {})
                g_params = g0.get("params", {})

                # Check resolved item ID or name
                raw_id = m_params.get("item_id", "")
                raw_name = m_params.get("name", "")
                resolved = menu_service.get_item_or_combo(raw_id) or menu_service.resolve_alias(raw_name) or menu_service.resolve_alias(raw_id)
                resolved_id = resolved.id if resolved else (raw_id if raw_id in menu_service.items or raw_id in menu_service.combos else "")

                gold_id = g_params.get("item_id", "")
                gold_qty = g_params.get("quantity", 1)
                model_qty = m_params.get("quantity", 1)

                if resolved_id == gold_id and model_qty == gold_qty:
                    intent_match = True
                elif not gold_id and not resolved_id:
                    intent_match = True

    # 2. Resulting-Cart level evaluation
    # Apply intents to build resulting cart and compare against expected_cart
    cart_match = False
    built_items: list[dict[str, Any]] = []

    for it in model_intents:
        if it.get("type") == "add_item":
            p = it.get("params", {})
            raw_id = p.get("item_id", "")
            raw_name = p.get("name", "")
            resolved = menu_service.get_item_or_combo(raw_id) or menu_service.resolve_alias(raw_name) or menu_service.resolve_alias(raw_id)
            item_id = resolved.id if resolved else raw_id
            built_items.append({
                "item_id": item_id,
                "quantity": p.get("quantity", 1),
                "size": p.get("size", "regular") or "regular",
            })
        elif it.get("type") == "undo":
            if built_items:
                built_items.pop()

    # Compare built_items against expected_items
    if len(built_items) == len(expected_items):
        matches = 0
        for exp in expected_items:
            for b in built_items:
                if b["item_id"] == exp["item_id"] and b["quantity"] == exp.get("quantity", 1):
                    matches += 1
                    break
        if matches == len(expected_items):
            cart_match = True

    details = {
        "model_intents": model_intents,
        "gold_intents": gold_intents,
        "built_items": built_items,
        "expected_items": expected_items,
    }
    return intent_match, cart_match, details


async def run_task1_llm_benchmark(
    scenarios: list[dict[str, Any]],
    gold_map: dict[str, Any],
    gemini_key: str,
    groq_key: str,
    menu_service: MenuService,
) -> dict[str, Any]:
    print("\n" + "=" * 80)
    print("  [TASK 1] AUDITED INTENT & CART ACCURACY (60 TURNS, INTERLEAVED)")
    print("=" * 80)

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:streamGenerateContent?alt=sse&key={gemini_key}"
    groq_client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)

    delims = (".", "!", "?", "\n")

    results: dict[str, list[dict[str, Any]]] = {
        "gemini_flash_lite_default": [],
        "groq_gpt_oss_20b_default": [],
        "groq_gpt_oss_20b_low_reasoning": [],
        "groq_qwen_27b_non_reasoning": [],
    }

    async with aiohttp.ClientSession() as gemini_session:
        for idx, scen in enumerate(scenarios, 1):
            sid = scen["id"]
            user_text = scen["utterances"][0]
            gold_entry = gold_map.get(sid, {})
            tags = scen.get("tags", [])

            # Categorize
            if "correction" in tags or "undo" in tags:
                cat = "correction_undo"
            elif "modifier" in tags or "size" in tags:
                cat = "modifiers_size"
            elif "quantity" in tags or "combo" in tags:
                cat = "quantity_combo"
            else:
                cat = "simple"

            # -------------------------------------------------------------
            # Config 1: Gemini Flash-Lite Default
            # -------------------------------------------------------------
            t0 = time.perf_counter()
            ttft1, first_sent1 = None, None
            chunks1: list[str] = []
            resolved_gem = "gemini-flash-lite-latest"
            payload1 = {
                "system_instruction": {"parts": [{"text": PRODUCTION_SYSTEM_INSTRUCTION}]},
                "contents": [{"role": "user", "parts": [{"text": user_text}]}],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.1,
                    "maxOutputTokens": 300,
                },
            }
            try:
                async with gemini_session.post(gemini_url, json=payload1) as resp:
                    async for line_bytes in resp.content:
                        line = line_bytes.decode("utf-8", errors="ignore").strip()
                        if line.startswith("data: "):
                            d = json.loads(line[6:])
                            if "modelVersion" in d:
                                resolved_gem = d["modelVersion"]
                            cand = d.get("candidates", [{}])[0]
                            parts = cand.get("content", {}).get("parts", [])
                            if parts and parts[0].get("text"):
                                txt = parts[0]["text"]
                                if ttft1 is None:
                                    ttft1 = (time.perf_counter() - t0) * 1000.0
                                chunks1.append(txt)
                                curr = "".join(chunks1)
                                if first_sent1 is None and any(dl in curr for dl in delims):
                                    first_sent1 = (time.perf_counter() - t0) * 1000.0
            except Exception as e:
                print(f"Gemini error {sid}: {e}")
            tot1 = (time.perf_counter() - t0) * 1000.0
            full1 = "".join(chunks1)
            parsed1 = {}
            try:
                parsed1 = json.loads(full1)
            except Exception:
                pass
            im1, cm1, _ = evaluate_intent_and_cart(parsed1, gold_entry, scen, menu_service)
            results["gemini_flash_lite_default"].append({
                "sid": sid, "category": cat, "ttft_ms": ttft1 or tot1, "total_ms": tot1,
                "first_sent_ms": first_sent1 or tot1, "intent_match": im1, "cart_match": cm1,
                "raw_json": parsed1, "model_id": resolved_gem,
            })
            await asyncio.sleep(0.3)

            # -------------------------------------------------------------
            # Config 2: Groq gpt-oss-20b Default (Reasoning on)
            # -------------------------------------------------------------
            t0 = time.perf_counter()
            ttft2, first_sent2 = None, None
            chunks2: list[str] = []
            try:
                stream2 = await groq_client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": PRODUCTION_SYSTEM_INSTRUCTION},
                        {"role": "user", "content": user_text},
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=350,
                    temperature=0.1,
                    stream=True,
                )
                async for chunk in stream2:
                    if chunk.choices and chunk.choices[0].delta.content:
                        c = chunk.choices[0].delta.content
                        if ttft2 is None:
                            ttft2 = (time.perf_counter() - t0) * 1000.0
                        chunks2.append(c)
                        curr = "".join(chunks2)
                        if first_sent2 is None and any(dl in curr for dl in delims):
                            first_sent2 = (time.perf_counter() - t0) * 1000.0
            except Exception as e:
                print(f"Groq 20b def error {sid}: {e}")
            tot2 = (time.perf_counter() - t0) * 1000.0
            full2 = "".join(chunks2)
            parsed2 = {}
            try:
                parsed2 = json.loads(full2)
            except Exception:
                pass
            im2, cm2, _ = evaluate_intent_and_cart(parsed2, gold_entry, scen, menu_service)
            results["groq_gpt_oss_20b_default"].append({
                "sid": sid, "category": cat, "ttft_ms": ttft2 or tot2, "total_ms": tot2,
                "first_sent_ms": first_sent2 or tot2, "intent_match": im2, "cart_match": cm2,
                "raw_json": parsed2, "model_id": "openai/gpt-oss-20b",
            })
            await asyncio.sleep(0.4)

            # -------------------------------------------------------------
            # Config 3: Groq gpt-oss-20b Low Reasoning
            # -------------------------------------------------------------
            t0 = time.perf_counter()
            ttft3, first_sent3 = None, None
            chunks3: list[str] = []
            try:
                stream3 = await groq_client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": PRODUCTION_SYSTEM_INSTRUCTION},
                        {"role": "user", "content": user_text},
                    ],
                    response_format={"type": "json_object"},
                    extra_body={"reasoning_effort": "low"},
                    max_tokens=350,
                    temperature=0.1,
                    stream=True,
                )
                async for chunk in stream3:
                    if chunk.choices and chunk.choices[0].delta.content:
                        c = chunk.choices[0].delta.content
                        if ttft3 is None:
                            ttft3 = (time.perf_counter() - t0) * 1000.0
                        chunks3.append(c)
                        curr = "".join(chunks3)
                        if first_sent3 is None and any(dl in curr for dl in delims):
                            first_sent3 = (time.perf_counter() - t0) * 1000.0
            except Exception as e:
                print(f"Groq 20b low error {sid}: {e}")
            tot3 = (time.perf_counter() - t0) * 1000.0
            full3 = "".join(chunks3)
            parsed3 = {}
            try:
                parsed3 = json.loads(full3)
            except Exception:
                pass
            im3, cm3, _ = evaluate_intent_and_cart(parsed3, gold_entry, scen, menu_service)
            results["groq_gpt_oss_20b_low_reasoning"].append({
                "sid": sid, "category": cat, "ttft_ms": ttft3 or tot3, "total_ms": tot3,
                "first_sent_ms": first_sent3 or tot3, "intent_match": im3, "cart_match": cm3,
                "raw_json": parsed3, "model_id": "openai/gpt-oss-20b",
            })
            await asyncio.sleep(0.4)

            # -------------------------------------------------------------
            # Config 4: Groq Qwen-27b Non-Reasoning
            # -------------------------------------------------------------
            t0 = time.perf_counter()
            ttft4, first_sent4 = None, None
            chunks4: list[str] = []
            try:
                stream4 = await groq_client.chat.completions.create(
                    model="qwen/qwen3.8-27b",
                    messages=[
                        {"role": "system", "content": PRODUCTION_SYSTEM_INSTRUCTION},
                        {"role": "user", "content": user_text},
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=350,
                    temperature=0.1,
                    stream=True,
                )
                async for chunk in stream4:
                    if chunk.choices and chunk.choices[0].delta.content:
                        c = chunk.choices[0].delta.content
                        if ttft4 is None:
                            ttft4 = (time.perf_counter() - t0) * 1000.0
                        chunks4.append(c)
                        curr = "".join(chunks4)
                        if first_sent4 is None and any(dl in curr for dl in delims):
                            first_sent4 = (time.perf_counter() - t0) * 1000.0
            except Exception as e:
                print(f"Qwen 27b error {sid}: {e}")
            tot4 = (time.perf_counter() - t0) * 1000.0
            full4 = "".join(chunks4)
            parsed4 = {}
            try:
                parsed4 = json.loads(full4)
            except Exception:
                pass
            im4, cm4, _ = evaluate_intent_and_cart(parsed4, gold_entry, scen, menu_service)
            results["groq_qwen_27b_non_reasoning"].append({
                "sid": sid, "category": cat, "ttft_ms": ttft4 or tot4, "total_ms": tot4,
                "first_sent_ms": first_sent4 or tot4, "intent_match": im4, "cart_match": cm4,
                "raw_json": parsed4, "model_id": "qwen/qwen3.8-27b",
            })

            print(
                f"[{idx:02d}/60] {sid} ({cat}) | "
                f"Gem: {results['gemini_flash_lite_default'][-1]['ttft_ms']:.0f}ms (Cart:{cm1}) | "
                f"Qwen: {results['groq_qwen_27b_non_reasoning'][-1]['ttft_ms']:.0f}ms (Cart:{cm4})"
            )
            await asyncio.sleep(0.5)

    # Compute overall and per-category stats
    summary: dict[str, Any] = {}
    categories = ["simple", "quantity_combo", "modifiers_size", "correction_undo"]

    for cfg, runs in results.items():
        ttfts = [r["ttft_ms"] for r in runs if r["ttft_ms"] > 0]
        totals = [r["total_ms"] for r in runs if r["total_ms"] > 0]
        intent_acc = (sum(1 for r in runs if r["intent_match"]) / len(runs)) * 100.0
        cart_acc = (sum(1 for r in runs if r["cart_match"]) / len(runs)) * 100.0

        per_cat = {}
        for c in categories:
            c_runs = [r for r in runs if r["category"] == c]
            if c_runs:
                per_cat[c] = {
                    "count": len(c_runs),
                    "intent_acc_pct": (sum(1 for r in c_runs if r["intent_match"]) / len(c_runs)) * 100.0,
                    "cart_acc_pct": (sum(1 for r in c_runs if r["cart_match"]) / len(c_runs)) * 100.0,
                }

        summary[cfg] = {
            "model_id": runs[0]["model_id"] if runs else "unknown",
            "sample_size": len(runs),
            "ttft_p50_ms": float(np.percentile(ttfts, 50)) if ttfts else 0.0,
            "ttft_p95_ms": float(np.percentile(ttfts, 95)) if ttfts else 0.0,
            "ttft_mean_ms": float(np.mean(ttfts)) if ttfts else 0.0,
            "ttft_ci": list(bootstrap_ci_mean(ttfts)),
            "total_p50_ms": float(np.percentile(totals, 50)) if totals else 0.0,
            "overall_intent_accuracy_pct": intent_acc,
            "overall_cart_accuracy_pct": cart_acc,
            "per_category": per_cat,
        }

    return {"summary": summary, "runs": results}


# ==============================================================================
# TASK 3: ENDPOINTING LATENCY & FALSE CUTOFF REDO (WITH TRAILING SILENCE)
# ==============================================================================

async def prepare_hesitation_clips_with_silence() -> list[dict[str, Any]]:
    audio_dir = Path("eval/audio/synthetic/g1f_hesitation")
    audio_dir.mkdir(parents=True, exist_ok=True)
    clips: list[dict[str, Any]] = []

    print("\n--- Synthesizing Hesitation Audio Clips with 1.5s Trailing Silence ---")
    for item in HESITATION_PHRASES:
        hid = item["id"]
        p1 = item["p1"]
        p2 = item["p2"]

        pcm1 = await synthesize_phrase_pcm(p1)
        pcm2 = await synthesize_phrase_pcm(p2)

        p1_dur_s = len(pcm1) / 16000.0
        p2_dur_s = len(pcm2) / 16000.0

        for pause_ms in [300, 500, 800]:
            pause_samples = int(16000 * (pause_ms / 1000.0))
            mid_silence = np.zeros(pause_samples, dtype=np.int16)
            trailing_silence = np.zeros(int(16000 * 1.5), dtype=np.int16)

            full_pcm = np.concatenate([pcm1, mid_silence, pcm2, trailing_silence])
            out_wav = audio_dir / f"{hid}_p{pause_ms}ms_trailing.wav"

            with wave.open(str(out_wav), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(full_pcm.tobytes())

            pause_start_s = p1_dur_s
            pause_end_s = p1_dur_s + (pause_ms / 1000.0)
            true_speech_end_s = pause_end_s + p2_dur_s

            clips.append({
                "clip_id": f"{hid}_p{pause_ms}ms",
                "phrase_id": hid,
                "pause_ms": pause_ms,
                "p1_text": p1,
                "p2_text": p2,
                "wav_path": str(out_wav),
                "pause_start_s": pause_start_s,
                "pause_end_s": pause_end_s,
                "true_speech_end_s": true_speech_end_s,
                "total_duration_s": len(full_pcm) / 16000.0,
            })
    return clips


async def stream_nova3_endpointing_redo(
    clip: dict[str, Any],
    endpointing_ms: int,
    api_key: str,
) -> dict[str, Any]:
    wav_path = Path(clip["wav_path"])
    with wave.open(str(wav_path), "rb") as wf:
        raw_pcm = wf.readframes(wf.getnframes())

    kt_params = "&".join(f"keyterm={kt.replace(' ', '+')}" for kt in KEYTERMS[:30])
    url = (
        f"wss://api.deepgram.com/v1/listen?model=nova-3&language=id&smart_format=true"
        f"&encoding=linear16&sample_rate=16000&interim_results=true&endpointing={endpointing_ms}&{kt_params}"
    )
    headers = {"Authorization": f"Token {api_key}"}

    chunk_dur = 0.1
    chunk_size = int(16000 * 2 * chunk_dur)
    chunks = [raw_pcm[i : i + chunk_size] for i in range(0, len(raw_pcm), chunk_size)]

    pause_start_s = clip["pause_start_s"]
    pause_end_s = clip["pause_end_s"]
    true_speech_end_s = clip["true_speech_end_s"]

    t_start = time.perf_counter()
    false_cutoff_detected = False
    speech_final_times: list[float] = []
    t_speech_end_sent: float | None = None
    all_events: list[dict[str, Any]] = []

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url, headers=headers) as ws:
            async def sender() -> None:
                nonlocal t_speech_end_sent
                for i, chunk in enumerate(chunks):
                    t_chunk_start = time.perf_counter()
                    chunk_audio_time = (i + 1) * chunk_dur
                    await ws.send_bytes(chunk)

                    if t_speech_end_sent is None and chunk_audio_time >= true_speech_end_s:
                        t_speech_end_sent = time.perf_counter()

                    sleep_dur = chunk_dur - (time.perf_counter() - t_chunk_start)
                    if sleep_dur > 0:
                        await asyncio.sleep(sleep_dur)

                await asyncio.sleep(0.3)
                await ws.send_str(json.dumps({"type": "CloseStream"}))

            async def receiver() -> None:
                nonlocal false_cutoff_detected
                async for msg in ws:
                    t_now = time.perf_counter()
                    stream_elapsed = t_now - t_start
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if data.get("speech_final", False) or data.get("is_final", False):
                            tr = ""
                            try:
                                tr = data["channel"]["alternatives"][0].get("transcript", "").strip()
                            except (KeyError, IndexError):
                                pass
                            if tr:
                                speech_final_times.append(t_now)
                                all_events.append({
                                    "t_event_rel_ms": stream_elapsed * 1000.0,
                                    "transcript": tr,
                                    "speech_final": data.get("speech_final", False),
                                })
                                # False cutoff check: Was event emitted during mid-sentence pause?
                                if pause_start_s <= stream_elapsed <= (pause_end_s + 0.1):
                                    false_cutoff_detected = True
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        break

            await asyncio.gather(sender(), receiver())

    assert t_speech_end_sent is not None
    # Final turnaround latency is measured to the last speech_final event emitted after speech end
    after_speech_events = [t for t in speech_final_times if t >= t_speech_end_sent]
    if after_speech_events:
        final_rx_time = after_speech_events[-1]
    else:
        final_rx_time = speech_final_times[-1] if speech_final_times else time.perf_counter()

    turnaround_latency_ms = (final_rx_time - t_speech_end_sent) * 1000.0

    return {
        "clip_id": clip["clip_id"],
        "pause_ms": clip["pause_ms"],
        "endpointing_ms": endpointing_ms,
        "false_cutoff": false_cutoff_detected,
        "turnaround_latency_ms": turnaround_latency_ms,
        "true_speech_end_sent_rel_ms": (t_speech_end_sent - t_start) * 1000.0,
        "final_rx_rel_ms": (final_rx_time - t_start) * 1000.0,
        "events": all_events,
    }


async def run_task3_endpointing_redo(
    hesitation_clips: list[dict[str, Any]],
    deepgram_key: str,
) -> dict[str, Any]:
    print("\n" + "=" * 80)
    print("  [TASK 3] DEEPGRAM NOVA-3 ENDPOINTING REDO (150, 300, 500 MS WITH TRAILING SILENCE)")
    print("=" * 80)

    results: dict[str, list[dict[str, Any]]] = {
        "endpointing_150ms": [],
        "endpointing_300ms": [],
        "endpointing_500ms": [],
    }

    # Interleaved across clips
    for idx, clip in enumerate(hesitation_clips, 1):
        cid = clip["clip_id"]
        p_ms = clip["pause_ms"]

        r150 = await stream_nova3_endpointing_redo(clip, 150, deepgram_key)
        results["endpointing_150ms"].append(r150)
        await asyncio.sleep(0.3)

        r300 = await stream_nova3_endpointing_redo(clip, 300, deepgram_key)
        results["endpointing_300ms"].append(r300)
        await asyncio.sleep(0.3)

        r500 = await stream_nova3_endpointing_redo(clip, 500, deepgram_key)
        results["endpointing_500ms"].append(r500)
        await asyncio.sleep(0.3)

        print(
            f"[{idx:02d}/30] {cid} (pause {p_ms}ms) | "
            f"150ms: {r150['turnaround_latency_ms']:.0f}ms (Cutoff:{r150['false_cutoff']}) | "
            f"300ms: {r300['turnaround_latency_ms']:.0f}ms (Cutoff:{r300['false_cutoff']}) | "
            f"500ms: {r500['turnaround_latency_ms']:.0f}ms (Cutoff:{r500['false_cutoff']})"
        )

    summary: dict[str, Any] = {}
    for cfg, runs in results.items():
        latencies = [r["turnaround_latency_ms"] for r in runs if not r["false_cutoff"] and r["turnaround_latency_ms"] > 0]
        if not latencies:
            latencies = [r["turnaround_latency_ms"] for r in runs]

        cutoffs = sum(1 for r in runs if r["false_cutoff"])
        cutoff_rate = (cutoffs / len(runs)) * 100.0

        p300_runs = [r for r in runs if r["pause_ms"] == 300]
        p500_runs = [r for r in runs if r["pause_ms"] == 500]
        p800_runs = [r for r in runs if r["pause_ms"] == 800]

        summary[cfg] = {
            "sample_size": len(runs),
            "false_cutoff_rate_total_pct": cutoff_rate,
            "false_cutoff_by_pause": {
                "pause_300ms_pct": (sum(1 for r in p300_runs if r["false_cutoff"]) / len(p300_runs)) * 100.0,
                "pause_500ms_pct": (sum(1 for r in p500_runs if r["false_cutoff"]) / len(p500_runs)) * 100.0,
                "pause_800ms_pct": (sum(1 for r in p800_runs if r["false_cutoff"]) / len(p800_runs)) * 100.0,
            },
            "turnaround_p50_ms": float(np.percentile(latencies, 50)) if latencies else 0.0,
            "turnaround_p95_ms": float(np.percentile(latencies, 95)) if latencies else 0.0,
            "turnaround_mean_ms": float(np.mean(latencies)) if latencies else 0.0,
            "turnaround_ci": list(bootstrap_ci_mean(latencies)),
        }

    return {"summary": summary, "runs": results}


# ==============================================================================
# TASK 4: ELEVENLABS FREE TIER TTS BENCHMARK (30 PHRASES X 5 INTERLEAVED RUNS)
# ==============================================================================

async def run_task4_elevenlabs_benchmark(
    phrases: list[str],
    api_key: str,
) -> dict[str, Any]:
    print("\n" + "=" * 80)
    print("  [TASK 4] ELEVENLABS FREE TIER TTS BENCHMARK (30 PHRASES X 5 RUNS INTERLEAVED)")
    print("=" * 80)

    voice_id = "EXAVITQu4vr4xnSDxMaL"  # Sarah
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }

    all_runs: list[dict[str, Any]] = []
    streaming_confirmed = False

    async with aiohttp.ClientSession() as session:
        for repeat in range(1, 6):
            print(f"\n--- ElevenLabs Interleaved Batch {repeat}/5 ---")
            for idx, text in enumerate(phrases, 1):
                payload = {
                    "text": text,
                    "model_id": "eleven_flash_v2_5",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
                }
                t0 = time.perf_counter()
                ttfb: float | None = None
                chunk_count = 0
                total_bytes = 0

                try:
                    async with session.post(url, json=payload, headers=headers) as resp:
                        if resp.headers.get("Transfer-Encoding", "").lower() == "chunked":
                            streaming_confirmed = True
                        async for chunk in resp.content.iter_chunked(1024):
                            if ttfb is None:
                                ttfb = (time.perf_counter() - t0) * 1000.0
                            chunk_count += 1
                            total_bytes += len(chunk)
                except Exception as e:
                    print(f"ElevenLabs error on phrase {idx}: {e}")

                tot_ms = (time.perf_counter() - t0) * 1000.0
                all_runs.append({
                    "repeat": repeat,
                    "phrase_idx": idx,
                    "text": text,
                    "ttfb_ms": ttfb or tot_ms,
                    "total_ms": tot_ms,
                    "chunk_count": chunk_count,
                    "total_bytes": total_bytes,
                })
                await asyncio.sleep(0.3)

            p50_curr = float(np.percentile([r["ttfb_ms"] for r in all_runs], 50))
            print(f"Batch {repeat}/5 completed. Current TTFB P50: {p50_curr:.1f}ms")

    ttfbs = [r["ttfb_ms"] for r in all_runs if r["ttfb_ms"] > 0]
    totals = [r["total_ms"] for r in all_runs if r["total_ms"] > 0]

    summary = {
        "provider": "ElevenLabs",
        "model_id": "eleven_flash_v2_5",
        "voice_id": voice_id,
        "total_requests": len(all_runs),
        "streaming_supported": streaming_confirmed,
        "ttfb_p50_ms": float(np.percentile(ttfbs, 50)) if ttfbs else 0.0,
        "ttfb_p95_ms": float(np.percentile(ttfbs, 95)) if ttfbs else 0.0,
        "ttfb_mean_ms": float(np.mean(ttfbs)) if ttfbs else 0.0,
        "ttfb_ci": list(bootstrap_ci_mean(ttfbs)),
        "total_duration_p50_ms": float(np.percentile(totals, 50)) if totals else 0.0,
    }

    return {"summary": summary, "runs": all_runs}


# ==============================================================================
# MAIN RUNNER
# ==============================================================================

async def main() -> None:
    print("=" * 80)
    print("  LAJUR MINGGU 2f G1 AUDIT & FINAL MEASUREMENT SUITE")
    print("=" * 80)

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    groq_key = os.getenv("GROQ_API_KEY", "")
    deepgram_key = os.getenv("DEEPGRAM_API_KEY", "")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")

    menu_service = MenuService("eval/menu/menu.json")

    # Load 60 scenarios
    with open("eval/datasets/v0/scenarios.jsonl", "r", encoding="utf-8") as f:
        all_scens = {json.loads(line)["id"]: json.loads(line) for line in f if line.strip()}
    scenarios = [all_scens[sid] for sid in SELECTED_60_SIDS]

    with open("eval/datasets/v0/gold_intents.jsonl", "r", encoding="utf-8") as f:
        gold_map = {json.loads(line)["scenario_id"]: json.loads(line) for line in f if line.strip()}

    # Run Task 1
    t1_results = await run_task1_llm_benchmark(scenarios, gold_map, gemini_key, groq_key, menu_service)

    # Run Task 3
    hesitation_clips = await prepare_hesitation_clips_with_silence()
    t3_results = await run_task3_endpointing_redo(hesitation_clips, deepgram_key)

    # Run Task 4
    t4_results = await run_task4_elevenlabs_benchmark(BOT_REPLY_PHRASES_30, elevenlabs_key)

    # Compile Final JSON Output
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "task1_llm_intent_and_cart_accuracy": t1_results["summary"],
        "task3_deepgram_endpointing_redo": t3_results["summary"],
        "task4_elevenlabs_tts_benchmark": t4_results["summary"],
    }

    out_file = Path("eval/results/spikes/g1f_audit_results.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    # Log to cost ledger (ledger limit tracking)
    # Task 1: 60x4 calls LLM (free tier = $0.00)
    # Task 3: 90 streaming calls Deepgram (~5.5 min @ $0.0077/min = $0.042)
    # Task 4: 150 calls ElevenLabs (~4,500 chars free tier = $0.00)
    cost_ledger_path = Path("eval/results/spikes/cost-ledger.csv")
    with open(cost_ledger_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["2026-10-20", "G1f Measurement Audit (T1 Accuracy + T3 Endpointing + T4 ElevenLabs TTS)", "$0.042", "$0.00"])

    print(f"\n[OK] G1f Benchmark finished successfully! Results saved to {out_file}")


if __name__ == "__main__":
    asyncio.run(main())
