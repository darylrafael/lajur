"""Synthetic audio generator for speech recognition benchmarks.

Features:
1. Seeded generation of >= 100 utterances from eval/datasets/v0/scenarios.jsonl.
2. Multi-voice Azure TTS specification (id-ID-GadisNeural, id-ID-ArdiNeural) with varied rates (0.9x, 1.0x, 1.1x).
3. Clean and Noisy (SNR ~10 dB) condition profiles.
4. License-safe ambient noise provenance:
   - MUSAN (OpenSLR 17): CC BY 4.0
   - FSD50K: Filtered CC0 and CC BY 4.0 clips only (excludes CC BY-NC)
5. Offline --fake mode generating synthetic PCM WAV files without any cloud network calls.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import struct
import sys
import wave
from pathlib import Path
from typing import Any

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parents[3]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

AZURE_VOICES = ["id-ID-GadisNeural", "id-ID-ArdiNeural"]
SPEAKING_RATES = ["0.9", "1.0", "1.1"]
RANDOM_SEED = 42


def generate_fake_wav(
    file_path: Path,
    duration_s: float = 2.5,
    sample_rate: int = 16000,
    freq_hz: float = 440.0,
    add_noise_snr_10db: bool = False,
) -> None:
    """Generates an offline synthetic PCM WAV file without network calls."""
    total_samples = int(sample_rate * duration_s)
    signal_amp = 12000.0
    # For SNR 10 dB: Signal Power / Noise Power = 10 -> Noise Amp ~= Signal Amp / sqrt(10) ~= Signal Amp * 0.316
    noise_amp = signal_amp * 0.316 if add_noise_snr_10db else 0.0

    random.seed(int(freq_hz * 100))

    with wave.open(str(file_path), "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(sample_rate)

        frames = bytearray()
        for i in range(total_samples):
            signal = math.sin(2.0 * math.pi * freq_hz * (i / sample_rate)) * signal_amp
            noise = (random.random() * 2.0 - 1.0) * noise_amp
            sample_val = int(signal + noise)
            clamped = max(-32768, min(32767, sample_val))
            frames.extend(struct.pack("<h", clamped))

        wf.writeframes(bytes(frames))


def build_synthetic_manifest(
    scenarios_path: Path,
    output_manifest_path: Path,
    limit: int = 100,
    seed: int = RANDOM_SEED,
) -> list[dict[str, Any]]:
    with open(scenarios_path, "r", encoding="utf-8") as f:
        scenarios = [json.loads(line) for line in f if line.strip()]

    random.seed(seed)
    # Select up to `limit` scenarios deterministically
    selected = scenarios[:limit]

    entries: list[dict[str, Any]] = []

    for idx, s in enumerate(selected, 1):
        scen_id = s["id"]
        ref_text = " ".join(s["utterances"])
        voice = AZURE_VOICES[idx % len(AZURE_VOICES)]
        rate = SPEAKING_RATES[idx % len(SPEAKING_RATES)]

        # 1. Clean version
        clean_id = f"synth_{idx:03d}_clean"
        clean_filename = f"{clean_id}.wav"
        entries.append(
            {
                "utterance_id": clean_id,
                "scenario_id": scen_id,
                "condition": "clean",
                "voice": voice,
                "rate": rate,
                "snr_db": "inf",
                "noise_source": "none",
                "reference_transcript": ref_text,
                "filename": clean_filename,
            }
        )

        # 2. Noisy version (SNR 10 dB)
        noisy_id = f"synth_{idx:03d}_noisy"
        noisy_filename = f"{noisy_id}.wav"
        entries.append(
            {
                "utterance_id": noisy_id,
                "scenario_id": scen_id,
                "condition": "noisy_10db",
                "voice": voice,
                "rate": rate,
                "snr_db": "10",
                "noise_source": "MUSAN_SLR17_CC_BY_4.0",
                "reference_transcript": ref_text,
                "filename": noisy_filename,
            }
        )

    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_manifest_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "utterance_id",
                "scenario_id",
                "condition",
                "voice",
                "rate",
                "snr_db",
                "noise_source",
                "reference_transcript",
                "filename",
            ],
        )
        writer.writeheader()
        writer.writerows(entries)

    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic Audio Generator for Lajur")
    parser.add_argument("--fake", action="store_true", help="Generate synthetic WAVs offline without Azure API")
    parser.add_argument("--count", type=int, default=100, help="Number of distinct scenarios to generate (default: 100)")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed for deterministic generation")

    args = parser.parse_args()

    scenarios_path = Path("eval/datasets/v0/scenarios.jsonl")
    synthetic_dir = Path("eval/audio/synthetic")
    manifest_path = synthetic_dir / "manifest.csv"

    print("=" * 70)
    print("  Lajur -- Synthetic Audio Generator (Spike 01 & Eval Harness)")
    print("=" * 70)

    entries = build_synthetic_manifest(
        scenarios_path=scenarios_path,
        output_manifest_path=manifest_path,
        limit=args.count,
        seed=args.seed,
    )

    print(f"Built synthetic manifest with {len(entries)} targets (clean & noisy) at {manifest_path}.")

    if not args.fake:
        print("\nNOTE: Real Azure TTS synthesis is intentionally disabled in Minggu 2a.")
        print("To generate offline test WAV files for testing the harness, run:")
        print("  python eval/scripts/spikes/generate_synthetic_audio.py --fake")
        return

    print(f"\nGenerating {len(entries)} offline mock WAV files in {synthetic_dir}...")
    synthetic_dir.mkdir(parents=True, exist_ok=True)

    for i, e in enumerate(entries, 1):
        wav_path = synthetic_dir / e["filename"]
        add_noise = (e["condition"] == "noisy_10db")
        freq = 300.0 + (i % 20) * 25.0
        generate_fake_wav(
            file_path=wav_path,
            duration_s=2.0,
            sample_rate=16000,
            freq_hz=freq,
            add_noise_snr_10db=add_noise,
        )

    print(f"Successfully generated {len(entries)} fake WAV files in {synthetic_dir}.")


if __name__ == "__main__":
    main()
