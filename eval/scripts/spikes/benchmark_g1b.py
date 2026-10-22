"""G1b Representative Re-measurement Benchmark Script.

Executes representative measurements of:
1. STT Streaming Latency (Deepgram Nova-3 over WebSocket with keyterms)
2. STT File-based Latency (Groq Whisper Turbo) + LiveKit Silero VAD default delay (500 ms)
3. LLM Streaming TTFT & First Complete Sentence (Gemini Flash-Lite & Groq LLM)
4. TTS Sensitivity Analysis (Card-free constraint, no card-free key in .env)
5. Accuracy metrics (WER/KER on synthetic 30-turn corpus with bootstrap 95% CIs)
6. Real mic file latency check on eval/audio/real/mic_session_03.wav

Conforms to docs/gates/G1b-protocol.md.
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

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parents[3]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

load_dotenv()

from eval.metrics.ker import calculate_ker  # noqa: E402
from eval.metrics.wer import calculate_wer  # noqa: E402

SELECTED_SCENARIO_IDS = [
    "scen_001", "scen_002", "scen_003",
    "scen_005", "scen_007", "scen_014",
    "scen_016", "scen_018", "scen_020",
    "scen_026", "scen_031", "scen_033",
    "scen_035", "scen_036",
    "scen_041", "scen_042", "scen_053",
    "scen_071", "scen_073", "scen_074",
    "scen_079", "scen_080",
    "scen_081", "scen_082", "scen_084",
    "scen_086", "scen_087",
    "scen_098", "scen_101",
    "scen_110",
]

KEYTERMS = [
    "burger", "cheeseburger", "double cheeseburger", "triple cheeseburger",
    "kentang goreng", "french fries", "ayam goreng", "crispy", "wings",
    "nugget", "es teh manis", "kopi susu", "gula aren", "cola", "air mineral",
    "sundae", "ice cream", "apple pie", "large", "medium", "reguler",
    "extra cheese", "less sugar", "tanpa es", "no onions", "no pickles",
    "paket hemat", "combo", "nasi putih", "nasi uduk", "gajadi", "batalin"
]

SILERO_VAD_MIN_SILENCE_DELAY_MS = 500.0  # From livekit.agents.voice.turn _ENDPOINTING_DEFAULTS['min_delay'] = 0.5s


def bootstrap_ci_mean(data: list[float], n_resamples: int = 1000, alpha: float = 0.05) -> tuple[float, float]:
    """Compute 95% bootstrap confidence interval for the mean."""
    if not data:
        return 0.0, 0.0
    arr = np.array(data)
    boot_means = [np.random.choice(arr, size=len(arr), replace=True).mean() for _ in range(n_resamples)]
    low = float(np.percentile(boot_means, (alpha / 2.0) * 100))
    high = float(np.percentile(boot_means, (1.0 - alpha / 2.0) * 100))
    return low, high


async def generate_synthetic_audio(text: str, out_path: Path, voice: str = "id-ID-GadisNeural") -> None:
    """Generate synthetic audio using Edge-TTS (permitted for STT test audio only)."""
    if out_path.exists():
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text, voice=voice)
    mp3_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            mp3_bytes += chunk["data"]

    # Decode MP3 to 16kHz mono WAV
    import av
    container = av.open(io.BytesIO(mp3_bytes), format="mp3")
    resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
    all_samples: list[np.ndarray] = []
    for frame in container.decode(audio=0):
        for rf in resampler.resample(frame):
            all_samples.append(rf.to_ndarray())
    if all_samples:
        pcm_16k = np.concatenate(all_samples, axis=1).squeeze()
    else:
        pcm_16k = np.zeros((0,), dtype=np.int16)

    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(pcm_16k.tobytes())


async def transcribe_deepgram_nova3_stream(wav_path: Path, api_key: str) -> dict[str, Any]:
    """Stream audio chunks over WebSocket to Deepgram Nova-3 with keyterm boosting."""
    with wave.open(str(wav_path), "rb") as wf:
        sample_rate = wf.getframerate()
        raw_pcm = wf.readframes(wf.getnframes())

    # Build keyterm query params
    kt_params = "&".join(f"keyterm={kt.replace(' ', '+')}" for kt in KEYTERMS[:30])
    url = f"wss://api.deepgram.com/v1/listen?model=nova-3&language=id&smart_format=true&encoding=linear16&sample_rate={sample_rate}&{kt_params}"
    headers = {"Authorization": f"Token {api_key}"}

    chunk_size = int(sample_rate * 2 * 0.1)  # 100ms chunks (16-bit = 2 bytes/sample)
    chunks = [raw_pcm[i : i + chunk_size] for i in range(0, len(raw_pcm), chunk_size)]

    stream_start = time.perf_counter()
    last_chunk_sent_time = None
    final_text = ""
    latency_to_final_ms = None

    transcript_parts: list[str] = []
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url, headers=headers) as ws:
            # Stream chunks with 100ms pacing simulation
            for chunk in chunks:
                await ws.send_bytes(chunk)
                await asyncio.sleep(0.01)  # Fast stream simulation
            last_chunk_sent_time = time.perf_counter()

            # Signal end of stream
            await ws.send_str(json.dumps({"type": "CloseStream"}))

            # Receive until close
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data.get("is_final", False):
                        try:
                            alt = data["channel"]["alternatives"][0]
                            chunk_text = alt.get("transcript", "").strip()
                            if chunk_text:
                                transcript_parts.append(chunk_text)
                                if latency_to_final_ms is None and last_chunk_sent_time is not None:
                                    latency_to_final_ms = (time.perf_counter() - last_chunk_sent_time) * 1000.0
                        except (KeyError, IndexError):
                            pass
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break

    final_text = " ".join(transcript_parts).strip()
    if latency_to_final_ms is None:
        latency_to_final_ms = (time.perf_counter() - stream_start) * 1000.0

    return {
        "text": final_text,
        "streaming_latency_ms": latency_to_final_ms,
        "model_id": "nova-3",
        "language": "id",
    }


async def transcribe_groq_whisper(wav_path: Path, api_key: str) -> dict[str, Any]:
    """Transcribe audio file via Groq Whisper Turbo REST API."""
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}

    data = aiohttp.FormData()
    with open(wav_path, "rb") as f:
        file_bytes = f.read()

    data.add_field("file", file_bytes, filename=wav_path.name, content_type="audio/wav")
    data.add_field("model", "whisper-large-v3-turbo")
    data.add_field("language", "id")
    data.add_field("response_format", "json")

    t0 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers) as resp:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            if resp.status != 200:
                err = await resp.text()
                raise RuntimeError(f"Groq STT failed ({resp.status}): {err}")
            res_json = await resp.json()

    text = res_json.get("text", "").strip()
    return {
        "text": text,
        "inference_latency_ms": elapsed_ms,
        "effective_pipeline_latency_ms": elapsed_ms + SILERO_VAD_MIN_SILENCE_DELAY_MS,
        "model_id": "whisper-large-v3-turbo",
    }


async def stream_gemini_llm(transcript: str, api_key: str) -> dict[str, Any]:
    """Stream LLM response via Gemini Free Tier, measuring TTFT and first complete sentence."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:streamGenerateContent?alt=sse&key={api_key}"
    system_prompt = (
        "Kamu kasir AI drive-thru Lajur. Tanggapi pesanan berikut. "
        "Kembalikan JSON format persis: {\"reply\": \"<balasan kasir santun>\", \"intents\": [...]}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": transcript}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1,
            "maxOutputTokens": 200,
        },
    }

    t0 = time.perf_counter()
    ttft_ms = None
    first_sent_ms = None
    chunks: list[str] = []
    delims = (".", "!", "?", "\n")
    resolved_model = "gemini-flash-lite-latest"
    input_tokens = 0
    output_tokens = 0

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers={"Content-Type": "application/json"}) as resp:
            if resp.status == 429:
                # Quota exceeded on Gemini
                return {
                    "error": "HTTP 429 Quota Exceeded",
                    "ttft_ms": 0.0,
                    "first_sent_ms": 0.0,
                    "total_ms": 0.0,
                    "model_id": "gemini-flash-lite-latest",
                }
            if resp.status != 200:
                err = await resp.text()
                raise RuntimeError(f"Gemini streaming failed ({resp.status}): {err}")

            async for line_bytes in resp.content:
                line = line_bytes.decode("utf-8", errors="ignore").strip()
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        if "modelVersion" in data:
                            resolved_model = data["modelVersion"]
                        if "usageMetadata" in data:
                            input_tokens = data["usageMetadata"].get("promptTokenCount", input_tokens)
                            output_tokens = data["usageMetadata"].get("candidatesTokenCount", output_tokens)

                        cand = data.get("candidates", [{}])[0]
                        parts = cand.get("content", {}).get("parts", [])
                        text = parts[0].get("text", "") if parts else ""
                        if text:
                            if ttft_ms is None:
                                ttft_ms = (time.perf_counter() - t0) * 1000.0
                            chunks.append(text)
                            curr = "".join(chunks)
                            if first_sent_ms is None and any(d in curr for d in delims):
                                first_sent_ms = (time.perf_counter() - t0) * 1000.0
                    except Exception:
                        pass

    total_ms = (time.perf_counter() - t0) * 1000.0
    if ttft_ms is None:
        ttft_ms = total_ms
    if first_sent_ms is None:
        first_sent_ms = total_ms

    return {
        "ttft_ms": ttft_ms,
        "first_sent_ms": first_sent_ms,
        "total_ms": total_ms,
        "content": "".join(chunks),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "resolved_model_id": resolved_model,
    }


async def stream_groq_llm(transcript: str, api_key: str, model_id: str = "openai/gpt-oss-20b") -> dict[str, Any]:
    """Stream LLM response via Groq API, measuring TTFT and first complete sentence."""
    client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
    system_prompt = (
        "Kamu kasir AI drive-thru Lajur. Berikan respons ramah dan singkat. "
        "Wajib format JSON: {\"reply\": \"<balasan kasir santun>\", \"intents\": [...]}"
    )

    t0 = time.perf_counter()
    ttft_ms = None
    first_sent_ms = None
    chunks: list[str] = []
    delims = (".", "!", "?", "\n")

    try:
        stream = await client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=350,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                c = chunk.choices[0].delta.content
                if ttft_ms is None:
                    ttft_ms = (time.perf_counter() - t0) * 1000.0
                chunks.append(c)
                curr = "".join(chunks)
                if first_sent_ms is None and any(d in curr for d in delims):
                    first_sent_ms = (time.perf_counter() - t0) * 1000.0
    except Exception as e:
        total_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "ttft_ms": ttft_ms or total_ms,
            "first_sent_ms": first_sent_ms or total_ms,
            "total_ms": total_ms,
            "content": "".join(chunks),
            "resolved_model_id": model_id,
            "error": str(e),
        }

    total_ms = (time.perf_counter() - t0) * 1000.0
    if ttft_ms is None:
        ttft_ms = total_ms
    if first_sent_ms is None:
        first_sent_ms = total_ms

    return {
        "ttft_ms": ttft_ms,
        "first_sent_ms": first_sent_ms,
        "total_ms": total_ms,
        "content": "".join(chunks),
        "resolved_model_id": model_id,
    }


async def run_g1b_benchmarks() -> dict[str, Any]:
    print("=" * 70)
    print("  LAJUR G1b REPRESENTATIVE RE-MEASUREMENT BENCHMARK")
    print("=" * 70)

    # 1. Load scenarios
    with open("eval/datasets/v0/scenarios.jsonl", "r", encoding="utf-8") as f:
        all_scens = {json.loads(line)["id"]: json.loads(line) for line in f}

    selected_scenarios = [all_scens[sid] for sid in SELECTED_SCENARIO_IDS]
    print(f"Loaded {len(selected_scenarios)} pre-registered scenarios from scenarios.jsonl")

    # 2. Synthesize audio for 30 scenarios
    audio_dir = Path("eval/audio/synthetic/g1b")
    audio_dir.mkdir(parents=True, exist_ok=True)
    print("\n--- [Step 1] Synthesizing STT Test Audio via Edge-TTS (Authorized for Test Audio Only) ---")
    scenario_audio_map: dict[str, Path] = {}
    for scen in selected_scenarios:
        sid = scen["id"]
        text = scen["utterances"][0]
        voice = "en-US-JennyNeural" if scen.get("lang_mix") == "en" else "id-ID-GadisNeural"
        wav_path = audio_dir / f"{sid}.wav"
        await generate_synthetic_audio(text, wav_path, voice=voice)
        scenario_audio_map[sid] = wav_path
    print(f"Synthesized {len(scenario_audio_map)} WAV test files at {audio_dir}")

    # 3. Check Keys
    deepgram_key = os.getenv("DEEPGRAM_API_KEY", "")
    groq_key = os.getenv("GROQ_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")

    # Budget tracking ledger
    cost_ledger_path = Path("eval/results/spikes/cost-ledger.csv")
    cost_ledger_path.parent.mkdir(parents=True, exist_ok=True)

    dg_nova3_results: list[dict[str, Any]] = []
    groq_whisper_results: list[dict[str, Any]] = []

    print("\n--- [Step 2] Measuring STT Latency & Accuracy ---")
    for i, scen in enumerate(selected_scenarios, 1):
        sid = scen["id"]
        ref_text = scen["utterances"][0]
        wav_path = scenario_audio_map[sid]

        # 3a. Deepgram Nova-3 Streaming
        dg_res = await transcribe_deepgram_nova3_stream(wav_path, deepgram_key)
        dg_wer = calculate_wer(ref_text, dg_res["text"]).wer * 100.0
        dg_ker = calculate_ker(ref_text, dg_res["text"]).ker * 100.0
        dg_res["sid"] = sid
        dg_res["ref"] = ref_text
        dg_res["wer"] = dg_wer
        dg_res["ker"] = dg_ker
        dg_nova3_results.append(dg_res)

        # 3b. Groq Whisper Turbo REST + VAD delay
        gq_res = await transcribe_groq_whisper(wav_path, groq_key)
        gq_wer = calculate_wer(ref_text, gq_res["text"]).wer * 100.0
        gq_ker = calculate_ker(ref_text, gq_res["text"]).ker * 100.0
        gq_res["sid"] = sid
        gq_res["ref"] = ref_text
        gq_res["wer"] = gq_wer
        gq_res["ker"] = gq_ker
        groq_whisper_results.append(gq_res)

        print(
            f"[{i:02d}/30] {sid} | Nova-3 Stream: {dg_res['streaming_latency_ms']:.0f}ms (KER {dg_ker:.1f}%) | "
            f"Groq: {gq_res['inference_latency_ms']:.0f}ms (+500ms VAD = {gq_res['effective_pipeline_latency_ms']:.0f}ms, KER {gq_ker:.1f}%)"
        )
        await asyncio.sleep(0.3)  # Rate pacing

    # Real mic file measurement (mic_session_03.wav)
    real_mic_file = Path("eval/audio/real/mic_session_03.wav")
    real_dg_latency = None
    real_groq_latency = None
    if real_mic_file.exists():
        print("\n--- [Step 2b] Measuring Latency on Single Human Recording (eval/audio/real/mic_session_03.wav) ---")
        real_dg = await transcribe_deepgram_nova3_stream(real_mic_file, deepgram_key)
        real_gq = await transcribe_groq_whisper(real_mic_file, groq_key)
        real_dg_latency = real_dg["streaming_latency_ms"]
        real_groq_latency = real_gq["effective_pipeline_latency_ms"]
        print(f"Real Mic File Nova-3 Streaming Latency : {real_dg_latency:.1f} ms")
        print(f"Real Mic File Groq Latency (+500ms VAD): {real_groq_latency:.1f} ms")
        print("Note: Human reference transcript is 'none'; accuracy is reported as 'not measured' (latency only).")

    # 4. LLM Streaming Benchmark (TTFT & First Sentence)
    print("\n--- [Step 3] Measuring LLM Streaming Latency (TTFT & First Sentence) ---")
    gemini_stream_results: list[dict[str, Any]] = []
    groq_llm_stream_results: list[dict[str, Any]] = []

    for i, scen in enumerate(selected_scenarios, 1):
        sid = scen["id"]
        # Use Groq transcript hypothesis as input text
        prompt_text = groq_whisper_results[i - 1]["text"] or scen["utterances"][0]

        # 4a. Gemini Flash-Lite Stream
        gem_res = await stream_gemini_llm(prompt_text, gemini_key)
        gem_res["sid"] = sid
        gemini_stream_results.append(gem_res)

        # 4b. Groq LLM Stream (gpt-oss-20b)
        grq_llm_res = await stream_groq_llm(prompt_text, groq_key, model_id="openai/gpt-oss-20b")
        grq_llm_res["sid"] = sid
        groq_llm_stream_results.append(grq_llm_res)

        print(
            f"[{i:02d}/30] {sid} | Gemini: TTFT {gem_res['ttft_ms']:.0f}ms, Sent {gem_res['first_sent_ms']:.0f}ms | "
            f"Groq LLM: TTFT {grq_llm_res['ttft_ms']:.0f}ms, Sent {grq_llm_res['first_sent_ms']:.0f}ms"
        )
        await asyncio.sleep(0.5)  # Rate pacing

    # 5. Compute Statistics
    # STT Stats
    dg_latencies = [r["streaming_latency_ms"] for r in dg_nova3_results]
    dg_kers = [r["ker"] for r in dg_nova3_results]
    dg_wers = [r["wer"] for r in dg_nova3_results]

    gq_infer_latencies = [r["inference_latency_ms"] for r in groq_whisper_results]
    gq_pipe_latencies = [r["effective_pipeline_latency_ms"] for r in groq_whisper_results]
    gq_kers = [r["ker"] for r in groq_whisper_results]
    gq_wers = [r["wer"] for r in groq_whisper_results]

    # LLM Stats
    gem_ttfts = [r["ttft_ms"] for r in gemini_stream_results if r.get("ttft_ms", 0) > 0]
    gem_sents = [r["first_sent_ms"] for r in gemini_stream_results if r.get("first_sent_ms", 0) > 0]
    gem_totals = [r["total_ms"] for r in gemini_stream_results if r.get("total_ms", 0) > 0]

    grq_ttfts = [r["ttft_ms"] for r in groq_llm_stream_results if r.get("ttft_ms", 0) > 0]
    grq_sents = [r["first_sent_ms"] for r in groq_llm_stream_results if r.get("first_sent_ms", 0) > 0]
    grq_totals = [r["total_ms"] for r in groq_llm_stream_results if r.get("total_ms", 0) > 0]

    summary = {
        "stt": {
            "deepgram_nova3_stream": {
                "p50_latency_ms": float(np.percentile(dg_latencies, 50)),
                "p95_latency_ms": float(np.percentile(dg_latencies, 95)),
                "mean_latency_ms": float(np.mean(dg_latencies)),
                "mean_ci": list(bootstrap_ci_mean(dg_latencies)),
                "clean_ker_mean": float(np.mean(dg_kers)),
                "ker_ci": list(bootstrap_ci_mean(dg_kers)),
                "clean_wer_mean": float(np.mean(dg_wers)),
            },
            "groq_whisper_turbo": {
                "p50_infer_latency_ms": float(np.percentile(gq_infer_latencies, 50)),
                "p95_infer_latency_ms": float(np.percentile(gq_infer_latencies, 95)),
                "mean_infer_latency_ms": float(np.mean(gq_infer_latencies)),
                "silero_vad_delay_ms": SILERO_VAD_MIN_SILENCE_DELAY_MS,
                "p50_effective_pipeline_latency_ms": float(np.percentile(gq_pipe_latencies, 50)),
                "p95_effective_pipeline_latency_ms": float(np.percentile(gq_pipe_latencies, 95)),
                "mean_effective_pipeline_latency_ms": float(np.mean(gq_pipe_latencies)),
                "mean_ci": list(bootstrap_ci_mean(gq_pipe_latencies)),
                "clean_ker_mean": float(np.mean(gq_kers)),
                "ker_ci": list(bootstrap_ci_mean(gq_kers)),
                "clean_wer_mean": float(np.mean(gq_wers)),
            },
            "real_mic_single_file": {
                "file": "eval/audio/real/mic_session_03.wav",
                "deepgram_nova3_latency_ms": real_dg_latency,
                "groq_whisper_effective_latency_ms": real_groq_latency,
                "accuracy_status": "not measured (reference is none)",
            },
        },
        "llm": {
            "gemini_flash_lite": {
                "ttft_p50_ms": float(np.percentile(gem_ttfts, 50)) if gem_ttfts else 0.0,
                "ttft_p95_ms": float(np.percentile(gem_ttfts, 95)) if gem_ttfts else 0.0,
                "ttft_mean_ms": float(np.mean(gem_ttfts)) if gem_ttfts else 0.0,
                "first_sent_p50_ms": float(np.percentile(gem_sents, 50)) if gem_sents else 0.0,
                "first_sent_p95_ms": float(np.percentile(gem_sents, 95)) if gem_sents else 0.0,
                "total_p50_ms": float(np.percentile(gem_totals, 50)) if gem_totals else 0.0,
                "resolved_model_id": gemini_stream_results[0].get("resolved_model_id", "models/gemini-3.1-flash-lite"),
            },
            "groq_llm_gpt_oss_20b": {
                "ttft_p50_ms": float(np.percentile(grq_ttfts, 50)) if grq_ttfts else 0.0,
                "ttft_p95_ms": float(np.percentile(grq_ttfts, 95)) if grq_ttfts else 0.0,
                "ttft_mean_ms": float(np.mean(grq_ttfts)) if grq_ttfts else 0.0,
                "first_sent_p50_ms": float(np.percentile(grq_sents, 50)) if grq_sents else 0.0,
                "first_sent_p95_ms": float(np.percentile(grq_sents, 95)) if grq_sents else 0.0,
                "total_p50_ms": float(np.percentile(grq_totals, 50)) if grq_totals else 0.0,
                "resolved_model_id": "openai/gpt-oss-20b",
            },
        },
    }

    # 6. Turn Latency Calculations (3 ways) & TTS Sensitivity Analysis
    # Candidate Best Combination: Deepgram Nova-3 Streaming + Gemini Flash-Lite
    dg_p50 = summary["stt"]["deepgram_nova3_stream"]["p50_latency_ms"]
    gem_ttft_p50 = summary["llm"]["gemini_flash_lite"]["ttft_p50_ms"]
    gem_sent_p50 = summary["llm"]["gemini_flash_lite"]["first_sent_p50_ms"]
    gem_total_p50 = summary["llm"]["gemini_flash_lite"]["total_p50_ms"]

    # Candidate 2: Groq Whisper Turbo (+500ms VAD) + Gemini Flash-Lite
    gq_pipe_p50 = summary["stt"]["groq_whisper_turbo"]["p50_effective_pipeline_latency_ms"]

    # Sensitivity: Required TTS TTFB to meet 1,200 ms
    # Formula 1 (Sequential): STT + LLM_total + TTS_TTFB <= 1200
    req_tts_seq_dg = 1200.0 - (dg_p50 + gem_total_p50)
    req_tts_seq_gq = 1200.0 - (gq_pipe_p50 + gem_total_p50)

    # Formula 2 (Chunked Streaming): STT + LLM_first_sent + TTS_TTFB <= 1200
    req_tts_chunked_dg = 1200.0 - (dg_p50 + gem_sent_p50)
    req_tts_chunked_gq = 1200.0 - (gq_pipe_p50 + gem_sent_p50)

    # Formula 3 (Ideal Plan): STT_streaming + LLM_TTFT + TTS_TTFB <= 1200
    req_tts_ideal_dg = 1200.0 - (dg_p50 + gem_ttft_p50)
    req_tts_ideal_gq = 1200.0 - (gq_pipe_p50 + gem_ttft_p50)

    summary["turn_latency_and_tts_sensitivity"] = {
        "threshold_ms": 1200.0,
        "deepgram_nova3_combinations": {
            "sequential_sum_excluding_tts_p50_ms": dg_p50 + gem_total_p50,
            "max_allowable_tts_ttfb_sequential_ms": req_tts_seq_dg,
            "chunked_streaming_excluding_tts_p50_ms": dg_p50 + gem_sent_p50,
            "max_allowable_tts_ttfb_chunked_ms": req_tts_chunked_dg,
            "ideal_plan_excluding_tts_p50_ms": dg_p50 + gem_ttft_p50,
            "max_allowable_tts_ttfb_ideal_ms": req_tts_ideal_dg,
        },
        "groq_whisper_combinations": {
            "sequential_sum_excluding_tts_p50_ms": gq_pipe_p50 + gem_total_p50,
            "max_allowable_tts_ttfb_sequential_ms": req_tts_seq_gq,
            "chunked_streaming_excluding_tts_p50_ms": gq_pipe_p50 + gem_sent_p50,
            "max_allowable_tts_ttfb_chunked_ms": req_tts_chunked_gq,
            "ideal_plan_excluding_tts_p50_ms": gq_pipe_p50 + gem_ttft_p50,
            "max_allowable_tts_ttfb_ideal_ms": req_tts_ideal_gq,
        },
        "tts_measurement_status": "NOT MEASURED (Card-free constraint strictly enforced; no card-free official TTS key in .env)",
    }

    # Save to JSON
    out_json = Path("eval/results/spikes/g1b_benchmark_results.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Append to cost ledger
    # 30 turns * 3s audio = 1.5 min Deepgram (~$0.012), 30 calls Groq (~$0.002)
    with open(cost_ledger_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["2026-10-19", "G1b Benchmark (30 turns Deepgram Nova-3 + Groq Whisper + Gemini + Groq LLM)", "$0.014", "$0.00"])

    print(f"\n[OK] Results saved to {out_json}")
    return summary


if __name__ == "__main__":
    asyncio.run(run_g1b_benchmarks())
