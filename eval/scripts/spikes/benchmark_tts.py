"""TTS latency and streaming benchmark for Lajur.

Measures:
1. Time to First Audio Byte/Chunk (TTFB / TTFT) via streaming
2. Total synthesis latency
3. Audio duration and Real-Time Factor (RTF)
4. Streaming chunk distribution across short, medium, long, and code-switched cashier turns
5. Evaluates both id-ID-GadisNeural and id-ID-ArdiNeural voices
"""

from __future__ import annotations

import asyncio
import io
import json
import sys
import time
import wave
from pathlib import Path
from typing import Any

import av
import edge_tts
import numpy as np

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parents[3]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

CASHIER_TEST_UTTERANCES = [
    # Tier 1: Ultra-short turn acknowledgments (15–35 chars)
    {"tier": "tier1_short", "text": "Baik kak, satu burger sapi."},
    {"tier": "tier1_short", "text": "Siap kak, ada tambahan lagi?"},
    {"tier": "tier1_short", "text": "Baik, kentangnya ukuran large ya."},
    {"tier": "tier1_short", "text": "Pesanan dibatalkan semua ya kak."},
    {"tier": "tier1_short", "text": "Siap, minumannya tanpa es ya kak."},

    # Tier 2: Medium confirmations & upsells (50–95 chars)
    {"tier": "tier2_medium", "text": "Baik kak, 1 Paket Hemat Burger Sapi. Mau sekalian upgrade minumannya ke ukuran besar?"},
    {"tier": "tier2_medium", "text": "Satu paket cheeseburger dengan ekstra dipping sauce BBQ sudah dicatat ya kak."},
    {"tier": "tier2_medium", "text": "Baik, 2 potong ayam goreng crispy. Mau ditambah nasi putih atau minuman?"},
    {"tier": "tier2_medium", "text": "Siap kak, 1 es kopi susu gula aren ukuran medium dengan less sugar."},
    {"tier": "tier2_medium", "text": "Pesanannya 1 burger sapi keju ganda dan 1 sundae cokelat. Ada tambahan lain?"},

    # Tier 3: Long multi-item summary & total billing (110–190 chars)
    {
        "tier": "tier3_long",
        "text": "Baik kak, total pesanannya: 1 Double Cheeseburger, 1 Ice Cream Sundae, dan 1 Chicken Nuggets 6 pieces. Totalnya tiga puluh sembilan ribu rupiah.",
    },
    {
        "tier": "tier3_long",
        "text": "Baik kak, 2 Burger Sapi Tunggal. Untuk minumannya tadi jadi dibatalkan ya. Total belanjaannya empat puluh empat ribu rupiah, silakan ke jendela pembayaran berikutnya.",
    },
    {
        "tier": "tier3_long",
        "text": "Satu paket combo ayam krispi dengan french fries dan cola, plus satu ice cream sundae stroberi sudah masuk pesanan ya kak. Ada lagi yang mau ditambah?",
    },
    {
        "tier": "tier3_long",
        "text": "Baik kak, jadi kentang goreng diganti nasi putih, minumannya es teh manis reguler. Semuanya sudah pas ya kak?",
    },

    # Tier 4: Mixed Indonesian-English terms / Code-switching (60–140 chars)
    {"tier": "tier4_codeswitch", "text": "Baik kak, 1 triple cheeseburger no onions with french fries and iced lemon tea."},
    {"tier": "tier4_codeswitch", "text": "Satu hot caramel macchiato medium size and two chocolate sundaes ya kak."},
    {"tier": "tier4_codeswitch", "text": "Maaf kak, crispy chicken burger sedang out of stock untuk jam operasional saat ini."},
    {"tier": "tier4_codeswitch", "text": "Baik kak, chicken wings spicy six pieces dengan dipping sauce tartar ya."},
]

VOICES = [
    {"name": "GadisNeural (Female)", "voice_id": "id-ID-GadisNeural"},
    {"name": "ArdiNeural (Male)", "voice_id": "id-ID-ArdiNeural"},
]


def decode_mp3_to_wav(mp3_bytes: bytes, target_sr: int = 16000) -> tuple[bytes, float]:
    """Convert MP3 bytes to 16kHz mono WAV and calculate audio duration in seconds."""
    container: Any = av.open(io.BytesIO(mp3_bytes), format="mp3")
    resampler = av.AudioResampler(format="s16", layout="mono", rate=target_sr)
    wav_io = io.BytesIO()
    total_samples = 0
    with wave.open(wav_io, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(target_sr)
        for frame in container.decode(audio=0):
            for rf in resampler.resample(frame):
                data = rf.to_ndarray().tobytes()
                total_samples += len(data) // 2
                wf.writeframes(data)
    dur_s = total_samples / float(target_sr)
    return wav_io.getvalue(), dur_s


async def benchmark_single(text: str, voice_id: str) -> dict[str, Any]:
    """Stream audio chunks and measure TTFB, total latency, and chunk timings."""
    comm = edge_tts.Communicate(text, voice_id)
    t0 = time.perf_counter()
    first_chunk_ms: float | None = None
    chunks: list[bytes] = []
    chunk_timestamps_ms: list[float] = []

    async for chunk in comm.stream():
        now = time.perf_counter()
        if chunk.get("type") == "audio" and "data" in chunk:
            data = chunk["data"]
            if isinstance(data, bytes) and len(data) > 0:
                elapsed_ms = (now - t0) * 1000.0
                if first_chunk_ms is None:
                    first_chunk_ms = elapsed_ms
                chunks.append(data)
                chunk_timestamps_ms.append(elapsed_ms)

    total_latency_ms = (time.perf_counter() - t0) * 1000.0
    all_mp3_bytes = b"".join(chunks)
    _, dur_s = decode_mp3_to_wav(all_mp3_bytes) if all_mp3_bytes else (b"", 0.0)

    # Calculate Real-Time Factor (RTF) = Total Latency / Audio Duration
    rtf = (total_latency_ms / (dur_s * 1000.0)) if dur_s > 0 else 0.0

    return {
        "text": text,
        "char_count": len(text),
        "voice_id": voice_id,
        "ttfb_ms": round(first_chunk_ms or total_latency_ms, 1),
        "total_latency_ms": round(total_latency_ms, 1),
        "audio_dur_s": round(dur_s, 2),
        "rtf": round(rtf, 3),
        "chunk_count": len(chunks),
        "total_audio_bytes": len(all_mp3_bytes),
    }


async def run_tts_benchmark() -> None:
    print("=" * 80)
    print("  LAJUR SPIKE 02 -- TTS STREAMING & LATENCY BENCHMARK (Edge-TTS Azure Neural)")
    print("=" * 80)
    print(f"Test Corpus : {len(CASHIER_TEST_UTTERANCES)} realistic drive-thru cashier responses")
    print(f"Voices      : {len(VOICES)} voices (id-ID-GadisNeural, id-ID-ArdiNeural)")
    print(f"Total Tests : {len(CASHIER_TEST_UTTERANCES) * len(VOICES)} streaming synthesis runs")
    print("-" * 80)

    results: list[dict[str, Any]] = []

    for v in VOICES:
        v_name = v["name"]
        v_id = v["voice_id"]
        print(f"\n>>> Benchmarking Voice: {v_name} ({v_id})")

        for idx, item in enumerate(CASHIER_TEST_UTTERANCES, 1):
            tier = item["tier"]
            text = item["text"]
            res = await benchmark_single(text, v_id)
            res["tier"] = tier
            results.append(res)

            print(
                f"  [{idx:02d}/{len(CASHIER_TEST_UTTERANCES):02d} - {tier:15s}] "
                f"TTFB: {res['ttfb_ms']:5.1f} ms | Total: {res['total_latency_ms']:5.1f} ms | "
                f"Audio Dur: {res['audio_dur_s']:.2f}s | RTF: {res['rtf']:.2f} | Chunks: {res['chunk_count']:2d}"
            )
            # Gentle pacing
            await asyncio.sleep(0.3)

    # Aggregate Analysis
    print("\n" + "=" * 80)
    print("  AGGREGATE TTS BENCHMARK RESULTS")
    print("=" * 80)

    for v in VOICES:
        v_id = v["voice_id"]
        v_name = v["name"]
        v_records = [r for r in results if r["voice_id"] == v_id]

        mean_ttfb = float(np.mean([r["ttfb_ms"] for r in v_records]))
        p50_ttfb = float(np.percentile([r["ttfb_ms"] for r in v_records], 50))
        p95_ttfb = float(np.percentile([r["ttfb_ms"] for r in v_records], 95))
        mean_total_ms = float(np.mean([r["total_latency_ms"] for r in v_records]))
        mean_rtf = float(np.mean([r["rtf"] for r in v_records]))

        print(f"\nVoice: {v_name}")
        print(f"  • Mean TTFB (First Chunk) : {mean_ttfb:.1f} ms")
        print(f"  • P50 TTFB (Median)       : {p50_ttfb:.1f} ms")
        print(f"  • P95 TTFB                : {p95_ttfb:.1f} ms")
        print(f"  • Mean Total Latency      : {mean_total_ms:.1f} ms")
        print(f"  • Mean Real-Time Factor   : {mean_rtf:.2f}x (Lower is faster; < 1.0 means faster than speech)")

    # Tier Breakdown Analysis
    print("\n" + "-" * 80)
    print("Performance by Cashier Response Tier (GadisNeural):")
    print("-" * 80)
    gadis_records = [r for r in results if r["voice_id"] == "id-ID-GadisNeural"]
    tiers = ["tier1_short", "tier2_medium", "tier3_long", "tier4_codeswitch"]

    tier_labels = {
        "tier1_short": "Tier 1: Short Acknowledgment (1-5 words)",
        "tier2_medium": "Tier 2: Medium Confirmation & Upsell",
        "tier3_long": "Tier 3: Long Multi-item & Total Bill",
        "tier4_codeswitch": "Tier 4: Bilingual / Code-switching Terms",
    }

    tier_summaries = {}
    for t in tiers:
        t_recs = [r for r in gadis_records if r["tier"] == t]
        t_ttfb = float(np.mean([r["ttfb_ms"] for r in t_recs]))
        t_tot = float(np.mean([r["total_latency_ms"] for r in t_recs]))
        t_dur = float(np.mean([r["audio_dur_s"] for r in t_recs]))
        t_rtf = float(np.mean([r["rtf"] for r in t_recs]))

        tier_summaries[t] = {
            "label": tier_labels[t],
            "mean_ttfb_ms": round(t_ttfb, 1),
            "mean_total_ms": round(t_tot, 1),
            "mean_audio_dur_s": round(t_dur, 2),
            "mean_rtf": round(t_rtf, 2),
        }

        print(
            f"  {tier_labels[t]:40s} | TTFB: {t_ttfb:5.1f} ms | "
            f"Total: {t_tot:6.1f} ms | Audio: {t_dur:.2f}s | RTF: {t_rtf:.2f}"
        )

    # Save to JSON
    output_path = Path("eval/results/spikes/tts_benchmark_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_test_samples": len(results),
        "voices_evaluated": [v["name"] for v in VOICES],
        "tier_summaries_gadis": tier_summaries,
        "raw_samples": results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] TTS Benchmark results saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(run_tts_benchmark())
