"""Spike evaluation harness and runner for Lajur.

Capabilities:
1. Manifest-driven streaming execution of STT, TTS, and LLM adapters.
2. Real-time audio streaming pacing simulation.
3. Strict Budget Guard enforcing SPIKE_BUDGET_USD via append-only cost-ledger.csv.
4. Comprehensive metrics computation (WER, KER, latency, cost).
5. Deterministic --dry-run cost estimation mode.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import sys
import time
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path when script is invoked directly
root_dir = Path(__file__).resolve().parents[3]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from eval.metrics.ker import calculate_ker
from eval.metrics.wer import calculate_wer
from lajur_agent.adapters.base import STTAdapter
from lajur_agent.adapters.fakes import FakeSTTAdapter

# Verified vendor unit costs per vendor-facts-2026-10.md
VENDOR_PRICES: dict[str, dict[str, float]] = {
    # STT costs per minute of audio
    "stt": {
        "soniox": 0.002,          # $2.00 / 1M audio tokens (~$0.002/min)
        "deepgram": 0.0077,       # $0.0077 / min streaming
        "gladia": 0.0125,         # $0.75 / hr ($0.0125/min)
        "groq-turbo": 0.00067,    # $0.04 / hr ($0.00067/min)
        "groq-v3": 0.00185,       # $0.111 / hr ($0.00185/min)
        "fake-stt": 0.0,
    },
    # TTS costs per 1M characters
    "tts": {
        "azure-s0": 16.0,         # $16.00 / 1M chars
        "cartesia": 30.0,         # ~$30.00 / 1M chars
        "elevenlabs": 40.0,       # ~$40.00 / 1M chars
        "fake-tts": 0.0,
    },
    # LLM costs per 1M tokens (in / out)
    "llm": {
        "gemini-2.5-flash-lite": {"in": 0.10, "out": 0.40},
        "gemini-2.5-flash": {"in": 0.30, "out": 2.50},
        "gpt-4o-mini": {"in": 0.15, "out": 0.60},
        "fake-llm": {"in": 0.0, "out": 0.0},
    },
}


class BudgetExceededError(RuntimeError):
    """Raised when an adapter invocation would exceed the configured dollar budget."""


class BudgetGuard:
    """Enforces hard spend caps before any vendor API is executed."""

    def __init__(
        self,
        ledger_path: Path | str | None = None,
        budget_limit_usd: float | None = None,
    ) -> None:
        if ledger_path is None:
            ledger_path = Path("eval/results/spikes/cost-ledger.csv")
        self.ledger_path = Path(ledger_path)

        if budget_limit_usd is not None:
            self.budget_limit = budget_limit_usd
        else:
            self.budget_limit = float(os.getenv("SPIKE_BUDGET_USD", "8.0"))

        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.current_spend = self._read_current_spend()

    def _read_current_spend(self) -> float:
        if not self.ledger_path.exists():
            with open(self.ledger_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "spike_id",
                    "vendor",
                    "utterance_id",
                    "cost_usd",
                    "cumulative_spend_usd",
                    "budget_limit_usd",
                ])
            return 0.0

        total = 0.0
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    total += float(row.get("cost_usd", 0.0))
                except (ValueError, TypeError):
                    continue
        return total

    def record_and_verify(
        self,
        estimated_cost: float,
        spike_id: str,
        vendor: str,
        utterance_id: str,
    ) -> float:
        """Verifies remaining budget and appends record to ledger.

        Raises BudgetExceededError if the cost would breach budget_limit.
        """
        projected = self.current_spend + estimated_cost
        if projected > self.budget_limit:
            remaining = max(0.0, self.budget_limit - self.current_spend)
            raise BudgetExceededError(
                f"BUDGET GUARD REFUSAL: Call for {vendor} on '{utterance_id}' costs "
                f"${estimated_cost:.5f}, which exceeds remaining budget (${remaining:.4f} of ${self.budget_limit:.2f})."
            )

        self.current_spend = projected
        now_iso = datetime.now(timezone.utc).isoformat()
        with open(self.ledger_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                now_iso,
                spike_id,
                vendor,
                utterance_id,
                f"{estimated_cost:.6f}",
                f"{self.current_spend:.6f}",
                f"{self.budget_limit:.2f}",
            ])
        return self.current_spend


@dataclass
class UtteranceResult:
    utterance_id: str
    scenario_id: str
    condition: str
    vendor: str
    reference_transcript: str
    hypothesis_transcript: str
    wer: float
    ker: float
    latency_ms: float
    cost_usd: float
    audio_duration_s: float
    substitutions_wer: int
    deletions_wer: int
    insertions_wer: int
    substitutions_ker: int
    deletions_ker: int
    insertions_ker: int
    timestamp: str


async def chunk_stream(audio_bytes: bytes, chunk_size: int = 1600, pacing: bool = True) -> AsyncIterator[bytes]:
    """Streams audio bytes in fixed chunks simulating WebRTC real-time delivery (e.g. 50ms at 16kHz = 1600 bytes)."""
    for i in range(0, len(audio_bytes), chunk_size):
        chunk = audio_bytes[i : i + chunk_size]
        yield chunk
        if pacing:
            # 50ms interval for 1600 bytes of 16-bit 16kHz mono audio
            await asyncio.sleep(0.005)  # Fast paced sleep for test runner


async def run_stt_utterance(
    adapter: STTAdapter,
    utterance_id: str,
    scenario_id: str,
    condition: str,
    reference_text: str,
    audio_bytes: bytes,
    audio_duration_s: float,
    budget_guard: BudgetGuard,
    spike_id: str = "spike-01-stt",
) -> UtteranceResult:
    vendor_rate = VENDOR_PRICES["stt"].get(adapter.name, 0.0)
    estimated_cost = (audio_duration_s / 60.0) * vendor_rate

    # Enforce budget guard
    budget_guard.record_and_verify(
        estimated_cost=estimated_cost,
        spike_id=spike_id,
        vendor=adapter.name,
        utterance_id=utterance_id,
    )

    start_time = time.perf_counter()
    hyp_text = ""
    async for event in adapter.transcribe_stream(chunk_stream(audio_bytes, pacing=False)):
        if event.is_final:
            hyp_text = event.text

    latency_ms = (time.perf_counter() - start_time) * 1000.0

    # Compute metrics
    wer_res = calculate_wer(reference_text, hyp_text)
    ker_res = calculate_ker(reference_text, hyp_text)

    return UtteranceResult(
        utterance_id=utterance_id,
        scenario_id=scenario_id,
        condition=condition,
        vendor=adapter.name,
        reference_transcript=reference_text,
        hypothesis_transcript=hyp_text,
        wer=wer_res.wer,
        ker=ker_res.ker,
        latency_ms=latency_ms,
        cost_usd=estimated_cost,
        audio_duration_s=audio_duration_s,
        substitutions_wer=wer_res.substitutions,
        deletions_wer=wer_res.deletions,
        insertions_wer=wer_res.insertions,
        substitutions_ker=ker_res.substitutions,
        deletions_ker=ker_res.deletions,
        insertions_ker=ker_res.insertions,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def print_dry_run_estimate() -> None:
    """Computes and prints estimated benchmark costs without executing any vendor API."""
    print("=" * 75)
    print("  LAJUR SPIKE HARNESS -- DRY-RUN COST ESTIMATE")
    print("=" * 75)
    print("Benchmark Volume Assumptions:")
    print("  - Real Human Recordings: 40 utterances x 4.0s = 160s (~2.67 min) per condition")
    print("    * 2 conditions (quiet + noise) = 5.33 min (~320s)")
    print("    * 3 conditions (+ optional helmet) = 8.00 min (~480s)")
    print("  - Synthetic TTS Audio: 100 utterances x 4.0s = 400s (~6.67 min)")
    print("    * 2 profiles (clean + noisy 10dB) = 13.33 min (~800s)")
    print("  - Total Audio per STT Vendor: ~21.33 min (~1,280s)")
    print("  - TTS Benchmark: 40 utterances x ~60 characters x 3 test rates = ~7,200 chars")
    print("  - LLM Benchmark: 135 scenarios x 500 prompt tokens + 60 output tokens")
    print("-" * 75)

    audio_min = 21.33
    tts_chars = 7200
    llm_scenarios = 135
    llm_in = (llm_scenarios * 500) / 1_000_000
    llm_out = (llm_scenarios * 60) / 1_000_000

    print(f"{'Component':<8} | {'Vendor Candidate':<24} | {'Unit Rate':<20} | {'Est. Spend':<10}")
    print("-" * 75)

    # STT
    stt_costs: dict[str, float] = {}
    for v, rate in VENDOR_PRICES["stt"].items():
        if v == "fake-stt":
            continue
        c = audio_min * rate
        stt_costs[v] = c
        print(f"STT      | {v:<24} | ${rate:.5f} / min      | ${c:.4f}")

    # TTS
    tts_costs: dict[str, float] = {}
    for v, rate in VENDOR_PRICES["tts"].items():
        if v == "fake-tts":
            continue
        c = (tts_chars / 1_000_000) * rate
        tts_costs[v] = c
        print(f"TTS      | {v:<24} | ${rate:.2f} / 1M chars    | ${c:.4f}")

    # LLM
    llm_costs: dict[str, float] = {}
    for v, rates in VENDOR_PRICES["llm"].items():
        if v == "fake-llm":
            continue
        c = (llm_in * rates["in"]) + (llm_out * rates["out"])
        llm_costs[v] = c
        print(f"LLM      | {v:<24} | ${rates['in']:.2f} in / ${rates['out']:.2f} out  | ${c:.4f}")

    print("-" * 75)
    total_stt = sum(stt_costs.values())
    total_tts = sum(tts_costs.values())
    total_llm = sum(llm_costs.values())
    grand_total = total_stt + total_tts + total_llm

    print(f"Subtotal STT (all 4 candidates) : ${total_stt:.4f}")
    print(f"Subtotal TTS (all 3 candidates) : ${total_tts:.4f}")
    print(f"Subtotal LLM (all 3 candidates) : ${total_llm:.4f}")
    print(f"GRAND TOTAL ESTIMATED SPEND     : ${grand_total:.4f} USD")
    print(f"Default Budget Guard (Limit)    : $8.00 USD (Headroom: ~{8.0 / grand_total:.1f}x)")
    print("=" * 75)


def main() -> None:
    parser = argparse.ArgumentParser(description="Lajur Spike Benchmark Harness")
    parser.add_argument("--dry-run", action="store_true", help="Print cost estimation table and exit without calls")
    parser.add_argument("--fake", action="store_true", help="Run harness offline using deterministic fake adapters")
    parser.add_argument("--manifest", type=str, default="eval/audio/real/manifest.csv", help="Path to manifest CSV")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of utterances evaluated")
    parser.add_argument("--budget", type=float, default=None, help="Override budget limit in USD")

    args = parser.parse_args()

    if args.dry_run:
        print_dry_run_estimate()
        return

    if args.fake:
        print("Running offline spike harness with FakeSTTAdapter...")
        guard = BudgetGuard(budget_limit_usd=args.budget or 8.0)
        adapter = FakeSTTAdapter()

        # Mock audio for offline test
        mock_pcm = b"\x00" * 32000  # 1s of 16kHz 16-bit audio
        res = asyncio.run(
            run_stt_utterance(
                adapter=adapter,
                utterance_id="real_001_quiet",
                scenario_id="scen_001",
                condition="quiet",
                reference_text="saya mau pesan burger sapi tunggal satu",
                audio_bytes=mock_pcm,
                audio_duration_s=1.0,
                budget_guard=guard,
            )
        )
        print("Fake Run Succeeded:")
        print(f"  WER: {res.wer:.2f} | KER: {res.ker:.2f} | Latency: {res.latency_ms:.1f}ms | Cost: ${res.cost_usd:.4f}")
        return

    print("Use --dry-run or --fake in Minggu 2a. Real vendor execution starts in Minggu 2b.")


if __name__ == "__main__":
    main()
