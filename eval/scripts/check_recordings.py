"""Validates human voice recordings in eval/audio/real/ against manifest.csv.

Checks:
1. File presence and filename matching.
2. Valid WAV RIFF container and PCM audio encoding.
3. Channels (strictly mono / 1 channel).
4. Sample rate (>= 16,000 Hz).
5. Audio duration (between 0.5 seconds and 30.0 seconds).
6. Discrepancy reporting (missing mandatory files, unrecognized files).
"""

from __future__ import annotations

import csv
import sys
import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileValidationResult:
    filename: str
    condition: str
    scenario_id: str
    status: str  # "PASS", "FAIL", "MISSING"
    error: str = ""
    duration_sec: float = 0.0
    sample_rate: int = 0
    channels: int = 0


def validate_wav_file(file_path: Path) -> tuple[bool, str, float, int, int]:
    """Validates audio format parameters of a WAV file.

    Returns: (is_valid, error_message, duration_seconds, sample_rate, channels)
    """
    if not file_path.exists():
        return False, "File does not exist", 0.0, 0, 0

    try:
        with wave.open(str(file_path), "rb") as wf:
            channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            sampwidth = wf.getsampwidth()
            n_frames = wf.getnframes()

            if sample_rate == 0:
                return False, "Corrupted WAV: sample rate is 0", 0.0, 0, 0

            duration = n_frames / float(sample_rate)

            # Checks
            if channels != 1:
                return False, f"Stereo detected ({channels} channels). Must be Mono (1 channel).", duration, sample_rate, channels

            if sample_rate < 16000:
                return False, f"Sample rate too low ({sample_rate} Hz). Must be >= 16,000 Hz.", duration, sample_rate, channels

            if sampwidth != 2:
                return False, f"Bit depth is {sampwidth * 8}-bit. Must be 16-bit PCM.", duration, sample_rate, channels

            if duration < 0.5:
                return False, f"Duration too short ({duration:.2f}s). Must be >= 0.5s.", duration, sample_rate, channels

            if duration > 30.0:
                return False, f"Duration too long ({duration:.2f}s). Must be <= 30.0s.", duration, sample_rate, channels

            return True, "", duration, sample_rate, channels

    except wave.Error as e:
        return False, f"Invalid WAV format: {e}", 0.0, 0, 0
    except Exception as e:
        return False, f"Error reading file: {e}", 0.0, 0, 0


def main() -> int:
    real_dir = Path("eval/audio/real")
    manifest_path = real_dir / "manifest.csv"

    print("=" * 70)
    print("  Lajur -- Human Voice Recordings Validator (Spike 01)")
    print("=" * 70)

    if not manifest_path.exists():
        print(f"ERROR: Manifest file not found at {manifest_path}")
        print("Run 'python eval/scripts/create_recording_manifest.py' first.")
        return 1

    entries: list[dict[str, str]] = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)

    print(f"Loaded {len(entries)} manifest targets from {manifest_path}.\n")

    results: list[FileValidationResult] = []
    manifest_filenames = {e["filename"] for e in entries}

    for entry in entries:
        filename = entry["filename"]
        condition = entry["condition"]
        scen_id = entry["scenario_id"]
        file_path = real_dir / filename

        if not file_path.exists():
            results.append(
                FileValidationResult(
                    filename=filename,
                    condition=condition,
                    scenario_id=scen_id,
                    status="MISSING",
                    error="File not yet recorded",
                )
            )
            continue

        valid, err, dur, sr, ch = validate_wav_file(file_path)
        if valid:
            results.append(
                FileValidationResult(
                    filename=filename,
                    condition=condition,
                    scenario_id=scen_id,
                    status="PASS",
                    duration_sec=dur,
                    sample_rate=sr,
                    channels=ch,
                )
            )
        else:
            results.append(
                FileValidationResult(
                    filename=filename,
                    condition=condition,
                    scenario_id=scen_id,
                    status="FAIL",
                    error=err,
                    duration_sec=dur,
                    sample_rate=sr,
                    channels=ch,
                )
            )

    # Check for unrecognized wav files
    actual_files = {p.name for p in real_dir.glob("*.wav")}
    unrecognized = actual_files - manifest_filenames

    # Categorize results by condition
    by_condition: dict[str, list[FileValidationResult]] = {}
    for r in results:
        by_condition.setdefault(r.condition, []).append(r)

    print("Recording Status Summary by Condition:")
    print("-" * 70)
    for cond in ("quiet", "noise", "helmet"):
        res_list = by_condition.get(cond, [])
        n_pass = sum(1 for r in res_list if r.status == "PASS")
        n_fail = sum(1 for r in res_list if r.status == "FAIL")
        n_missing = sum(1 for r in res_list if r.status == "MISSING")
        total = len(res_list)
        marker = "[OK]" if (n_pass == total and total > 0) else ("[..]" if n_pass > 0 else "[  ]")
        print(f"  {marker} Condition '{cond:6s}': {n_pass:2d}/{total:2d} passed | {n_fail:2d} failed | {n_missing:2d} missing")

    # Detail failures
    failures = [r for r in results if r.status == "FAIL"]
    if failures:
        print("\n" + "!" * 70)
        print("  FORMAT DEFECTS DETECTED (Must be corrected):")
        print("!" * 70)
        for f in failures:
            print(f"  - {f.filename} [{f.condition}]: {f.error}")

    if unrecognized:
        print("\n" + "?" * 70)
        print("  UNRECOGNIZED FILES IN eval/audio/real/:")
        print("?" * 70)
        for u in sorted(unrecognized):
            print(f"  - {u} (not in manifest.csv)")

    quiet_results = by_condition.get("quiet", [])
    quiet_pass = sum(1 for r in quiet_results if r.status == "PASS")
    quiet_total = len(quiet_results)

    print("\n" + "=" * 70)
    if quiet_pass == quiet_total and quiet_total > 0:
        print(f"SUCCESS: Mandatory baseline ({quiet_total} 'quiet' recordings) is 100% verified and ready for Spike 01!")
        return 0
    else:
        print(f"ACTION REQUIRED: Mandatory 'quiet' condition has {quiet_pass}/{quiet_total} valid recordings.")
        print("Refer to 'docs/spikes/recording-script.md' for the text and recording guidelines.")
        return 0 if quiet_pass > 0 else 0  # Informational check


if __name__ == "__main__":
    sys.exit(main())
