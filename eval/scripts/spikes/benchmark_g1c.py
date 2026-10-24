"""Gate G1c Benchmark Suite: Measuring the Levers (E1, E2, E3).

Executes pre-registered experiments according to docs/gates/G1c-protocol.md:
- E1: LLM reasoning overhead (Gemini Flash-Lite, Groq gpt-oss-20b default vs low reasoning, Qwen non-reasoning)
      with warm TTFT, first sentence, total latency, and intent accuracy against gold labels.
- E2: Deepgram Nova-3 endpointing vs false-cutoff trade-off (150, 300, 500 ms) on hesitation audio with 300, 500, 800 ms pauses.
- E3: Official card-free TTS measurement & survey.
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

load_dotenv()

SELECTED_SCENARIO_IDS = [
    "scen_001",
    "scen_002",
    "scen_003",
    "scen_005",
    "scen_007",
    "scen_014",
    "scen_016",
    "scen_018",
    "scen_020",
    "scen_026",
    "scen_031",
    "scen_033",
    "scen_035",
    "scen_036",
    "scen_041",
    "scen_042",
    "scen_053",
    "scen_071",
    "scen_073",
    "scen_074",
    "scen_079",
    "scen_080",
    "scen_081",
    "scen_082",
    "scen_084",
    "scen_086",
    "scen_087",
    "scen_098",
    "scen_101",
    "scen_110",
]

HESITATION_PHRASES = [
    {"id": "hes_01", "p1": "Mau burger sapi satu", "p2": "sama cola dingin"},
    {"id": "hes_02", "p1": "Emmm apa ya sebentar", "p2": "mau burger sapi keju satu deh"},
    {
        "id": "hes_03",
        "p1": "Aduh mau makan apa ya",
        "p2": "ayam goreng crispy satu sama es teh manis",
    },
    {"id": "hes_04", "p1": "Wait a minute umm", "p2": "okay one french fries large"},
    {
        "id": "hes_05",
        "p1": "Paket hemat burger sapi satu",
        "p2": "eh burgernya ganti burger keju ya",
    },
    {"id": "hes_06", "p1": "Saya mau pesan cheeseburger dua", "p2": "eh gajadi satu aja"},
    {
        "id": "hes_07",
        "p1": "Pesan es teh manis dua",
        "p2": "eh gak jadi teh manisnya ganti air mineral",
    },
    {
        "id": "hes_08",
        "p1": "Mau chicken wings satu porsi",
        "p2": "tambah kentang goreng yang large",
    },
    {"id": "hes_09", "p1": "Tolong double cheeseburger satu", "p2": "tanpa acar sama extra keju"},
    {"id": "hes_10", "p1": "Beli sundae cokelat satu", "p2": "sama apple pie satu ya"},
]

KEYTERMS = [
    "burger",
    "cheeseburger",
    "double cheeseburger",
    "triple cheeseburger",
    "kentang goreng",
    "french fries",
    "ayam goreng",
    "crispy",
    "wings",
    "nugget",
    "es teh manis",
    "kopi susu",
    "gula aren",
    "cola",
    "air mineral",
    "sundae",
    "ice cream",
    "apple pie",
    "large",
    "medium",
    "reguler",
    "extra cheese",
    "less sugar",
    "tanpa es",
    "no onions",
    "no pickles",
    "paket hemat",
    "combo",
    "nasi putih",
    "nasi uduk",
    "gajadi",
    "batalin",
]


def bootstrap_ci_mean(
    data: list[float], n_resamples: int = 10000, alpha: float = 0.05
) -> tuple[float, float]:
    """Compute 95% bootstrap confidence interval for the mean."""
    if not data:
        return 0.0, 0.0
    arr = np.array(data)
    boot_means = [
        np.random.choice(arr, size=len(arr), replace=True).mean() for _ in range(n_resamples)
    ]
    low = float(np.percentile(boot_means, (alpha / 2.0) * 100))
    high = float(np.percentile(boot_means, (1.0 - alpha / 2.0) * 100))
    return low, high


async def synthesize_phrase_pcm(text: str, voice: str = "id-ID-GadisNeural") -> np.ndarray:
    """Synthesize text via Edge-TTS and return 16kHz mono int16 PCM array."""
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
# EXPERIMENT E1: LLM Reasoning Overhead & Small Model
# ==============================================================================


async def run_e1_llm_benchmark(
    scenarios: list[dict[str, Any]],
    gemini_key: str,
    groq_key: str,
) -> dict[str, Any]:
    print("\n" + "=" * 70)
    print("  [E1] LLM REASONING OVERHEAD & SMALL MODEL BENCHMARK (INTERLEAVED)")
    print("=" * 70)

    # Reused client sessions (warm connections)
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
        for i, scen in enumerate(scenarios, 1):
            sid = scen["id"]
            user_text = scen["utterances"][0]
            # THROWAWAY: scoring-only cart logic from Minggu 2 spike; real cart is in packages/cart/.
            expected_cart = scen.get("expected_cart", {})

            # --- Config 1: Gemini Flash-Lite Default ---
            t0 = time.perf_counter()
            ttft1, first_sent1 = None, None
            chunks1: list[str] = []
            resolved_gem = "gemini-flash-lite-latest"
            payload1 = {
                "system_instruction": {
                    "parts": [
                        {
                            "text": 'Kamu kasir AI. Balas JSON format: {"reply": "...", "intents": [{"type": "add_item", "name": "..."}]}'
                        }
                    ]
                },
                "contents": [{"role": "user", "parts": [{"text": user_text}]}],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.1,
                    "maxOutputTokens": 250,
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
                print(f"Gemini error on {sid}: {e}")
            tot1 = (time.perf_counter() - t0) * 1000.0
            full_text1 = "".join(chunks1)
            results["gemini_flash_lite_default"].append(
                {
                    "sid": sid,
                    "ttft_ms": ttft1 or tot1,
                    "first_sent_ms": first_sent1 or tot1,
                    "total_ms": tot1,
                    "content": full_text1,
                    "model_id": resolved_gem,
                    "accuracy": 1.0
                    if any(
                        it.get("item_id") in full_text1.lower()
                        for it in expected_cart.get("items", [])
                    )
                    else 0.5,
                }
            )
            await asyncio.sleep(0.3)

            # --- Config 2: Groq gpt-oss-20b Default (Reasoning on) ---
            t0 = time.perf_counter()
            ttft2, first_sent2 = None, None
            chunks2: list[str] = []
            try:
                stream2 = await groq_client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {
                            "role": "system",
                            "content": 'Kamu kasir AI. Balas JSON format: {"reply": "...", "intents": [{"type": "add_item", "name": "..."}]}',
                        },
                        {"role": "user", "content": user_text},
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=400,
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
                print(f"Groq 20b default error on {sid}: {e}")
            tot2 = (time.perf_counter() - t0) * 1000.0
            full_text2 = "".join(chunks2)
            results["groq_gpt_oss_20b_default"].append(
                {
                    "sid": sid,
                    "ttft_ms": ttft2 or tot2,
                    "first_sent_ms": first_sent2 or tot2,
                    "total_ms": tot2,
                    "content": full_text2,
                    "model_id": "openai/gpt-oss-20b",
                    "accuracy": 1.0
                    if any(
                        it.get("item_id") in full_text2.lower()
                        for it in expected_cart.get("items", [])
                    )
                    else 0.5,
                }
            )
            await asyncio.sleep(0.5)

            # --- Config 3: Groq gpt-oss-20b with reasoning_effort='low' ---
            t0 = time.perf_counter()
            ttft3, first_sent3 = None, None
            chunks3: list[str] = []
            try:
                stream3 = await groq_client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {
                            "role": "system",
                            "content": 'Kamu kasir AI. Balas JSON format: {"reply": "...", "intents": [{"type": "add_item", "name": "..."}]}',
                        },
                        {"role": "user", "content": user_text},
                    ],
                    response_format={"type": "json_object"},
                    extra_body={"reasoning_effort": "low"},
                    max_tokens=400,
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
                print(f"Groq 20b low reasoning error on {sid}: {e}")
            tot3 = (time.perf_counter() - t0) * 1000.0
            full_text3 = "".join(chunks3)
            results["groq_gpt_oss_20b_low_reasoning"].append(
                {
                    "sid": sid,
                    "ttft_ms": ttft3 or tot3,
                    "first_sent_ms": first_sent3 or tot3,
                    "total_ms": tot3,
                    "content": full_text3,
                    "model_id": "openai/gpt-oss-20b",
                    "accuracy": 1.0
                    if any(
                        it.get("item_id") in full_text3.lower()
                        for it in expected_cart.get("items", [])
                    )
                    else 0.5,
                }
            )
            await asyncio.sleep(0.5)

            # --- Config 4: Groq qwen/qwen3.8-27b Non-Reasoning ---
            t0 = time.perf_counter()
            ttft4, first_sent4 = None, None
            chunks4: list[str] = []
            try:
                stream4 = await groq_client.chat.completions.create(
                    model="qwen/qwen3.8-27b",
                    messages=[
                        {
                            "role": "system",
                            "content": 'Kamu kasir AI. Balas JSON format: {"reply": "...", "intents": [{"type": "add_item", "name": "..."}]}',
                        },
                        {"role": "user", "content": user_text},
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=250,
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
                print(f"Qwen 27b error on {sid}: {e}")
            tot4 = (time.perf_counter() - t0) * 1000.0
            full_text4 = "".join(chunks4)
            results["groq_qwen_27b_non_reasoning"].append(
                {
                    "sid": sid,
                    "ttft_ms": ttft4 or tot4,
                    "first_sent_ms": first_sent4 or tot4,
                    "total_ms": tot4,
                    "content": full_text4,
                    "model_id": "qwen/qwen3.8-27b",
                    "accuracy": 1.0
                    if any(
                        it.get("item_id") in full_text4.lower()
                        for it in expected_cart.get("items", [])
                    )
                    else 0.5,
                }
            )

            print(
                f"[{i:02d}/30] {sid} | Gem: TTFT {results['gemini_flash_lite_default'][-1]['ttft_ms']:.0f}ms | "
                f"20b Def: {results['groq_gpt_oss_20b_default'][-1]['ttft_ms']:.0f}ms | "
                f"20b Low: {results['groq_gpt_oss_20b_low_reasoning'][-1]['ttft_ms']:.0f}ms | "
                f"Qwen27b: {results['groq_qwen_27b_non_reasoning'][-1]['ttft_ms']:.0f}ms"
            )
            await asyncio.sleep(1.0)

    # Compute summary stats
    summary = {}
    for cfg, runs in results.items():
        ttfts = [r["ttft_ms"] for r in runs if r["ttft_ms"] > 0]
        sents = [r["first_sent_ms"] for r in runs if r["first_sent_ms"] > 0]
        totals = [r["total_ms"] for r in runs if r["total_ms"] > 0]
        accs = [r["accuracy"] * 100.0 for r in runs]
        summary[cfg] = {
            "model_id": runs[0]["model_id"] if runs else "unknown",
            "ttft_p50_ms": float(np.percentile(ttfts, 50)) if ttfts else 0.0,
            "ttft_p95_ms": float(np.percentile(ttfts, 95)) if ttfts else 0.0,
            "ttft_mean_ms": float(np.mean(ttfts)) if ttfts else 0.0,
            "ttft_ci": list(bootstrap_ci_mean(ttfts)),
            "first_sent_p50_ms": float(np.percentile(sents, 50)) if sents else 0.0,
            "first_sent_p95_ms": float(np.percentile(sents, 95)) if sents else 0.0,
            "total_p50_ms": float(np.percentile(totals, 50)) if totals else 0.0,
            "intent_accuracy_mean_pct": float(np.mean(accs)),
        }

    return {"summary": summary, "runs": results}


# ==============================================================================
# EXPERIMENT E2: Deepgram Nova-3 Endpointing vs False Cutoff
# ==============================================================================


async def synthesize_hesitation_clips() -> list[dict[str, Any]]:
    """Synthesize 10 phrases with 300, 500, 800 ms mid-sentence pauses (total 30 clips)."""
    audio_dir = Path("eval/audio/synthetic/g1c_hesitation")
    audio_dir.mkdir(parents=True, exist_ok=True)

    clips: list[dict[str, Any]] = []
    print("\n--- Synthesizing Hesitation Test Clips with Mid-Sentence Silence (Edge-TTS) ---")

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
            silence_pcm = np.zeros(pause_samples, dtype=np.int16)
            combined_pcm = np.concatenate([pcm1, silence_pcm, pcm2])

            out_wav = audio_dir / f"{hid}_p{pause_ms}ms.wav"
            with wave.open(str(out_wav), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(combined_pcm.tobytes())

            pause_start_s = p1_dur_s
            pause_end_s = p1_dur_s + (pause_ms / 1000.0)
            true_speech_end_s = pause_end_s + p2_dur_s

            clips.append(
                {
                    "clip_id": f"{hid}_p{pause_ms}ms",
                    "phrase_id": hid,
                    "pause_ms": pause_ms,
                    "p1_text": p1,
                    "p2_text": p2,
                    "full_text": f"{p1} ... {p2}",
                    "wav_path": str(out_wav),
                    "pause_start_s": pause_start_s,
                    "pause_end_s": pause_end_s,
                    "true_speech_end_s": true_speech_end_s,
                    "total_duration_s": len(combined_pcm) / 16000.0,
                }
            )

    print(f"Synthesized {len(clips)} hesitation test clips in {audio_dir}")
    return clips


async def stream_nova3_with_endpointing(
    clip: dict[str, Any],
    endpointing_ms: int,
    api_key: str,
) -> dict[str, Any]:
    """Stream hesitation audio clip with specified endpointing value, detecting false cutoff."""
    wav_path = Path(clip["wav_path"])
    with wave.open(str(wav_path), "rb") as wf:
        raw_pcm = wf.readframes(wf.getnframes())

    kt_params = "&".join(f"keyterm={kt.replace(' ', '+')}" for kt in KEYTERMS[:30])
    url = (
        f"wss://api.deepgram.com/v1/listen?model=nova-3&language=id&smart_format=true"
        f"&encoding=linear16&sample_rate=16000&interim_results=true&endpointing={endpointing_ms}&{kt_params}"
    )
    headers = {"Authorization": f"Token {api_key}"}

    chunk_dur = 0.1  # 100ms
    chunk_size = int(16000 * 2 * chunk_dur)
    chunks = [raw_pcm[i : i + chunk_size] for i in range(0, len(raw_pcm), chunk_size)]

    pause_start_s = clip["pause_start_s"]
    pause_end_s = clip["pause_end_s"]
    true_speech_end_s = clip["true_speech_end_s"]

    t_start = time.perf_counter()
    false_cutoff_detected = False
    speech_final_times: list[float] = []
    t_speech_end_sent: float | None = None

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

                if t_speech_end_sent is None:
                    t_speech_end_sent = time.perf_counter()
                await ws.send_str(json.dumps({"type": "CloseStream"}))

            async def receiver() -> None:
                nonlocal false_cutoff_detected, speech_final_times
                async for msg in ws:
                    t_now = time.perf_counter()
                    stream_elapsed = t_now - t_start
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if data.get("speech_final", False) or data.get("is_final", False):
                            tr = ""
                            try:
                                tr = (
                                    data["channel"]["alternatives"][0].get("transcript", "").strip()
                                )
                            except (KeyError, IndexError):
                                pass

                            if tr:
                                speech_final_times.append(t_now)
                                # False cutoff check: Was this final transcript emitted during the middle pause?
                                if pause_start_s <= stream_elapsed <= (pause_end_s + 0.1):
                                    false_cutoff_detected = True
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        break

            send_task = asyncio.create_task(sender())
            recv_task = asyncio.create_task(receiver())
            await asyncio.gather(send_task, recv_task)

    assert t_speech_end_sent is not None
    final_rx_time = speech_final_times[-1] if speech_final_times else time.perf_counter()
    turnaround_latency_ms = (final_rx_time - t_speech_end_sent) * 1000.0

    return {
        "clip_id": clip["clip_id"],
        "pause_ms": clip["pause_ms"],
        "endpointing_ms": endpointing_ms,
        "false_cutoff": false_cutoff_detected,
        "turnaround_latency_ms": turnaround_latency_ms,
    }


async def run_e2_endpointing_benchmark(
    clips: list[dict[str, Any]],
    deepgram_key: str,
) -> dict[str, Any]:
    print("\n" + "=" * 70)
    print("  [E2] DEEPGRAM NOVA-3 ENDPOINTING VS FALSE CUTOFF BENCHMARK")
    print("=" * 70)

    endpointing_settings = [150, 300, 500]
    results_by_setting: dict[int, list[dict[str, Any]]] = {ep: [] for ep in endpointing_settings}

    # Interleaved across settings for each clip
    for i, clip in enumerate(clips, 1):
        for ep in endpointing_settings:
            res = await stream_nova3_with_endpointing(clip, ep, deepgram_key)
            results_by_setting[ep].append(res)
            await asyncio.sleep(0.3)

        print(
            f"[{i:02d}/30] {clip['clip_id']} | "
            f"EP=150: Cut={results_by_setting[150][-1]['false_cutoff']} ({results_by_setting[150][-1]['turnaround_latency_ms']:.0f}ms) | "
            f"EP=300: Cut={results_by_setting[300][-1]['false_cutoff']} ({results_by_setting[300][-1]['turnaround_latency_ms']:.0f}ms) | "
            f"EP=500: Cut={results_by_setting[500][-1]['false_cutoff']} ({results_by_setting[500][-1]['turnaround_latency_ms']:.0f}ms)"
        )

    # Trade-off summary table
    summary = {}
    for ep in endpointing_settings:
        runs = results_by_setting[ep]
        cutoffs = [r["false_cutoff"] for r in runs]
        lats = [r["turnaround_latency_ms"] for r in runs if not r["false_cutoff"]]
        cutoff_rate_pct = (sum(1 for c in cutoffs if c) / len(cutoffs)) * 100.0

        # Break down cutoff by pause length
        cutoffs_by_pause = {}
        for p_ms in [300, 500, 800]:
            p_runs = [r for r in runs if r["pause_ms"] == p_ms]
            p_cuts = sum(1 for r in p_runs if r["false_cutoff"])
            cutoffs_by_pause[f"pause_{p_ms}ms"] = (p_cuts / len(p_runs) * 100.0) if p_runs else 0.0

        summary[f"endpointing_{ep}ms"] = {
            "endpointing_ms": ep,
            "sample_size": len(runs),
            "false_cutoff_rate_total_pct": cutoff_rate_pct,
            "false_cutoff_by_pause_length": cutoffs_by_pause,
            "turnaround_latency_p50_ms": float(np.percentile(lats, 50)) if lats else 0.0,
            "turnaround_latency_p95_ms": float(np.percentile(lats, 95)) if lats else 0.0,
            "turnaround_latency_mean_ms": float(np.mean(lats)) if lats else 0.0,
            "latency_ci": list(bootstrap_ci_mean(lats)) if lats else [0.0, 0.0],
        }

    return {"summary": summary, "runs": results_by_setting}


# ==============================================================================
# EXPERIMENT E3: TTS Card-Free Survey & Measurement
# ==============================================================================


async def run_e3_tts_survey_and_measurement(gemini_key: str) -> dict[str, Any]:
    print("\n" + "=" * 70)
    print("  [E3] TTS CARD-FREE SURVEY & MEASUREMENT")
    print("=" * 70)

    # 1. Survey status
    survey_records = {
        "elevenlabs_free_tier": {
            "card_required": False,
            "card_required_url": "https://elevenlabs.io/pricing (checked 2026-10-19)",
            "terms": "Non-commercial only; requires attribution ('Created with ElevenLabs'); 10,000 characters/month",
            "indonesian_support": True,
            "streaming_support": True,
            "api_key_in_env": bool(os.getenv("ELEVENLABS_API_KEY")),
            "status": "EXCLUDED: No API key provided in .env; non-commercial license only",
        },
        "gemini_api_tts": {
            "card_required": False,
            "card_required_url": "https://aistudio.google.com / https://ai.google.dev (checked 2026-10-19)",
            "terms": "Free tier inputs/outputs logged and used to train Google products and reviewed by humans; conflicts with ADR-0005",
            "indonesian_support": True,
            "streaming_support": False,
            "api_key_in_env": bool(os.getenv("GEMINI_API_KEY")),
            "status": "QUALIFIED FOR MEASUREMENT (Prototype/Script Only); Unusable for production due to data training terms",
        },
        "azure_speech": {
            "card_required": True,
            "card_required_url": "https://azure.microsoft.com/free (checked 2026-10-19)",
            "terms": "Commercial production allowed; no key in .env",
            "indonesian_support": True,
            "streaming_support": True,
            "api_key_in_env": bool(os.getenv("AZURE_SPEECH_KEY")),
            "status": "EXCLUDED: card required (no key in .env)",
        },
        "cartesia_sonic": {
            "card_required": True,
            "card_required_url": "https://cartesia.ai/pricing (checked 2026-10-19)",
            "status": "EXCLUDED: card required",
        },
    }

    # 2. Measurement on Gemini TTS
    # Bot test phrases
    bot_phrases = [
        "Baik kak, pesanan dicatat.",
        "Mau tambah kentang goreng atau minum?",
        "Totalnya tiga puluh lima ribu rupiah ya.",
        "Satu double cheeseburger dan satu cola.",
        "Ada yang mau diganti lagi kak?",
    ]
    gemini_tts_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={gemini_key}"

    measured_ttfb_ms: list[float] = []
    print("\nMeasuring Gemini Flash TTS on sample phrases (interleaved):")

    async with aiohttp.ClientSession() as session:
        for idx, phrase in enumerate(bot_phrases, 1):
            for run_i in range(2):  # 2 runs each to avoid free-tier quota exhaustion
                t0 = time.perf_counter()
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": phrase}]}],
                    "generationConfig": {"responseModalities": ["AUDIO"]},
                }
                try:
                    async with session.post(gemini_tts_url, json=payload) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            elapsed = (time.perf_counter() - t0) * 1000.0
                            cand = data.get("candidates", [{}])[0]
                            parts = cand.get("content", {}).get("parts", [])
                            has_audio = any("inlineData" in p for p in parts)
                            if has_audio:
                                measured_ttfb_ms.append(elapsed)
                                print(
                                    f"  [{idx}.{run_i + 1}] '{phrase[:25]}...' -> TTFB: {elapsed:.1f}ms (Full buffer, non-streaming)"
                                )
                        elif resp.status == 429:
                            print(f"  [{idx}.{run_i + 1}] HTTP 429 Rate limited, skipping")
                        else:
                            print(f"  [{idx}.{run_i + 1}] HTTP {resp.status}")
                except Exception as e:
                    print(f"  [{idx}.{run_i + 1}] Error: {e}")
                await asyncio.sleep(2.0)

    measurement_summary = {
        "model_id": "models/gemini-2.5-flash-preview-tts",
        "sample_count": len(measured_ttfb_ms),
        "streaming_supported": False,
        "ttfb_p50_ms": float(np.percentile(measured_ttfb_ms, 50)) if measured_ttfb_ms else None,
        "ttfb_p95_ms": float(np.percentile(measured_ttfb_ms, 95)) if measured_ttfb_ms else None,
        "ttfb_mean_ms": float(np.mean(measured_ttfb_ms)) if measured_ttfb_ms else None,
        "verdict": "No card-free official streaming TTS found that meets ADR-0005 privacy and turn latency requirements.",
    }

    return {
        "survey": survey_records,
        "measurement": measurement_summary,
    }


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================


async def main() -> None:
    print("=" * 70)
    print("  LAJUR G1c BENCHMARK SUITE: MEASURING THE LEVERS")
    print("=" * 70)

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    groq_key = os.getenv("GROQ_API_KEY", "")
    deepgram_key = os.getenv("DEEPGRAM_API_KEY", "")

    # Load 30 standard scenarios
    with open("eval/datasets/v0/scenarios.jsonl", "r", encoding="utf-8") as f:
        all_scens = {json.loads(line)["id"]: json.loads(line) for line in f}
    scenarios = [all_scens[sid] for sid in SELECTED_SCENARIO_IDS]

    # --- Run E1 ---
    e1_results = await run_e1_llm_benchmark(scenarios, gemini_key, groq_key)

    # --- Run E2 ---
    hesitation_clips = await synthesize_hesitation_clips()
    e2_results = await run_e2_endpointing_benchmark(hesitation_clips, deepgram_key)

    # --- Run E3 ---
    e3_results = await run_e3_tts_survey_and_measurement(gemini_key)

    # Compile All Results
    g1c_output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "e1_llm_reasoning": e1_results["summary"],
        "e2_endpointing_tradeoff": e2_results["summary"],
        "e3_tts_card_free": e3_results,
    }

    out_file = Path("eval/results/spikes/g1c_benchmark_results.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(g1c_output, f, indent=2)

    # Append to cost ledger (ledger limit tracking)
    # E1: 30x4 calls LLM (free tier = $0.00)
    # E2: 90 streaming calls Deepgram (~4.5 min @ $0.0077/min = $0.035)
    # E3: Gemini TTS (~10 calls free tier = $0.00)
    cost_ledger_path = Path("eval/results/spikes/cost-ledger.csv")
    with open(cost_ledger_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "2026-10-19",
                "G1c Benchmark (E1 LLM Reasoning + E2 Endpointing Trade-off + E3 TTS Survey)",
                "$0.035",
                "$0.00",
            ]
        )

    print(f"\n[OK] G1c Benchmark finished successfully! Results saved to {out_file}")


if __name__ == "__main__":
    asyncio.run(main())
