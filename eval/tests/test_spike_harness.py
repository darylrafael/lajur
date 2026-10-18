"""Offline unit tests for the spike benchmark harness, BudgetGuard, and fake adapters."""

import asyncio
import io
import sys
from pathlib import Path

import pytest
from eval.scripts.spikes.runner import (
    BudgetExceededError,
    BudgetGuard,
    print_dry_run_estimate,
    run_stt_utterance,
)
from lajur_agent.adapters.fakes import (
    FakeLLMIntentAdapter,
    FakeSTTAdapter,
    FakeTTSAdapter,
)


def test_budget_guard_creation_and_spend(tmp_path: Path):
    ledger_file = tmp_path / "test_ledger.csv"
    guard = BudgetGuard(ledger_path=ledger_file, budget_limit_usd=1.0)

    assert guard.current_spend == 0.0

    # Record spend 1
    guard.record_and_verify(
        estimated_cost=0.25,
        spike_id="spike-01",
        vendor="test-vendor",
        utterance_id="utt_001",
    )
    assert guard.current_spend == 0.25

    # Record spend 2
    guard.record_and_verify(
        estimated_cost=0.50,
        spike_id="spike-01",
        vendor="test-vendor",
        utterance_id="utt_002",
    )
    assert guard.current_spend == 0.75

    # Re-instantiate guard from existing ledger to verify persistence
    guard2 = BudgetGuard(ledger_path=ledger_file, budget_limit_usd=1.0)
    assert guard2.current_spend == 0.75


def test_budget_guard_rejection_on_limit_breach(tmp_path: Path):
    ledger_file = tmp_path / "test_ledger_breach.csv"
    guard = BudgetGuard(ledger_path=ledger_file, budget_limit_usd=0.50)

    guard.record_and_verify(
        estimated_cost=0.40,
        spike_id="spike-01",
        vendor="vendor-a",
        utterance_id="utt_001",
    )

    # Attempting to spend $0.15 more will breach $0.50 limit ($0.40 + $0.15 = $0.55)
    with pytest.raises(BudgetExceededError) as exc_info:
        guard.record_and_verify(
            estimated_cost=0.15,
            spike_id="spike-01",
            vendor="vendor-b",
            utterance_id="utt_002",
        )

    assert "BUDGET GUARD REFUSAL" in str(exc_info.value)
    assert guard.current_spend == 0.40  # Spend was not incremented


@pytest.mark.asyncio
async def test_fake_stt_adapter_streaming():
    adapter = FakeSTTAdapter(default_transcript="burger sapi satu", simulated_delay_ms=0.0)

    async def mock_audio():
        for _ in range(4):
            yield b"\x00" * 800

    events = []
    async for event in adapter.transcribe_stream(mock_audio()):
        events.append(event)

    assert len(events) >= 1
    final_event = events[-1]
    assert final_event.is_final is True
    assert final_event.text == "burger sapi satu"


@pytest.mark.asyncio
async def test_fake_tts_adapter_synthesis():
    adapter = FakeTTSAdapter(sample_rate=16000, simulated_ttft_ms=0.0)

    # Batch test
    audio_bytes = await adapter.synthesize_text("halo selamat datang")
    assert len(audio_bytes) > 0
    assert len(audio_bytes) % 2 == 0  # 16-bit PCM

    # Stream test
    async def text_stream():
        yield "halo "
        yield "kak"

    chunks = []
    async for chunk in adapter.synthesize_stream(text_stream()):
        chunks.append(chunk)

    assert len(chunks) >= 2
    assert chunks[-1].is_final is True


@pytest.mark.asyncio
async def test_fake_llm_intent_adapter():
    adapter = FakeLLMIntentAdapter(simulated_ttft_ms=0.0)
    result = await adapter.parse_intent("mau pesan kentang goreng satu")

    assert len(result.intents) == 1
    assert result.intents[0]["type"] == "add_item"
    assert result.intents[0]["params"]["item_id"] == "kentang_goreng"
    assert result.tokens_in > 0
    assert result.tokens_out > 0


@pytest.mark.asyncio
async def test_run_stt_utterance_end_to_end(tmp_path: Path):
    ledger_file = tmp_path / "test_e2e_ledger.csv"
    guard = BudgetGuard(ledger_path=ledger_file, budget_limit_usd=5.0)
    adapter = FakeSTTAdapter(default_transcript="burger sapi tunggal satu", simulated_delay_ms=0.0)

    mock_pcm = b"\x00" * 32000  # 1s
    res = await run_stt_utterance(
        adapter=adapter,
        utterance_id="utt_001",
        scenario_id="scen_001",
        condition="quiet",
        reference_text="burger sapi tunggal satu",
        audio_bytes=mock_pcm,
        audio_duration_s=1.0,
        budget_guard=guard,
    )

    assert res.wer == 0.0
    assert res.ker == 0.0
    assert res.vendor == "fake-stt"
    assert res.hypothesis_transcript == "burger sapi tunggal satu"
    assert res.cost_usd == 0.0


def test_dry_run_output():
    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        print_dry_run_estimate()
    finally:
        sys.stdout = old_stdout

    output = captured.getvalue()
    assert "DRY-RUN COST ESTIMATE" in output
    assert "soniox" in output
    assert "deepgram" in output
    assert "gladia" in output
    assert "azure-s0" in output
    assert "gemini-2.5-flash-lite" in output
    assert "GRAND TOTAL ESTIMATED SPEND" in output
