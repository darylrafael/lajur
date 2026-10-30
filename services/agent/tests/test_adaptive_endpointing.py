"""Unit tests for adaptive endpointing and hesitation detection."""

from __future__ import annotations

import asyncio

import pytest
from lajur_agent.turn_detection import (
    AdaptiveEndpointingHandler,
    is_mid_thought,
)


@pytest.mark.parametrize(
    ("utterance", "expected_mid_thought"),
    [
        # Clean / completed utterances -> False
        ("pesan burger rendang satu", False),
        ("kopi susu gula aren dua", False),
        ("paket hemat ayam 1 regular", False),
        ("sudah cukup itu aja", False),
        ("tolong dibungkus ya", False),
        ("kentang goreng satu large", False),
        # Hesitation fillers -> True
        ("ayam goreng crispy satu... anu", True),
        ("mau pesan... sebentar", True),
        ("burger rendang satu deh... eh", True),
        ("tunggu sebentar", True),
        ("aduh apa ya", True),
        ("hmm", True),
        ("let me think... wait", True),
        # Dangling conjunctions / prepositions -> True
        ("ayam crispy satu sama", True),
        ("burger rendang satu dan", True),
        ("kopi susu terus", True),
        ("nasi uduk dengan", True),
        ("paket hemat satu buat", True),
        ("tambah", True),
        # Dangling verbs / quantities -> True
        ("saya mau", True),
        ("aku pesan", True),
        ("sama satu", True),
        ("tambah dua", True),
        ("dan tiga", True),
    ],
)
def test_is_mid_thought_heuristics(utterance: str, expected_mid_thought: bool) -> None:
    assert is_mid_thought(utterance) == expected_mid_thought


@pytest.mark.asyncio
async def test_adaptive_endpointing_clean_turn_immediate_finalize() -> None:
    """Non-hesitation utterances must finalize immediately with 0ms added delay."""
    finalized_events: list[tuple[str, float]] = []

    async def mock_finalize(text: str, ts: float) -> None:
        finalized_events.append((text, ts))

    handler = AdaptiveEndpointingHandler(
        on_finalize=mock_finalize,
        base_endpointing_ms=300.0,
        extension_ms=500.0,
    )

    t0 = 1000.0
    handler.on_speech_final("pesan burger rendang satu", t0)
    # A small yield to event loop
    await asyncio.sleep(0.01)

    assert len(finalized_events) == 1
    assert finalized_events[0] == ("pesan burger rendang satu", 1000.0)
    assert not handler.has_pending_extension


@pytest.mark.asyncio
async def test_adaptive_endpointing_hesitation_extends_and_finalizes() -> None:
    """Hesitation utterances must trigger bounded extension before finalizing."""
    finalized_events: list[tuple[str, float]] = []

    async def mock_finalize(text: str, ts: float) -> None:
        finalized_events.append((text, ts))

    handler = AdaptiveEndpointingHandler(
        on_finalize=mock_finalize,
        base_endpointing_ms=300.0,
        extension_ms=100.0,  # 100ms for fast unit test
    )

    t0 = 2000.0
    handler.on_speech_final("ayam crispy satu sama", t0)

    # Immediately after: should NOT have finalized yet
    await asyncio.sleep(0.02)
    assert len(finalized_events) == 0
    assert handler.has_pending_extension

    # After extension expires: should finalize
    await asyncio.sleep(0.12)
    assert len(finalized_events) == 1
    assert finalized_events[0][0] == "ayam crispy satu sama"
    assert not handler.has_pending_extension


@pytest.mark.asyncio
async def test_adaptive_endpointing_resumed_speech_cancels_extension() -> None:
    """If user resumes speaking during extension, the pending timer is cancelled."""
    finalized_events: list[tuple[str, float]] = []

    async def mock_finalize(text: str, ts: float) -> None:
        finalized_events.append((text, ts))

    handler = AdaptiveEndpointingHandler(
        on_finalize=mock_finalize,
        base_endpointing_ms=300.0,
        extension_ms=200.0,
    )

    # Step 1: User says incomplete phrase
    handler.on_speech_final("mau pesan burger sama", 3000.0)
    await asyncio.sleep(0.05)
    assert handler.has_pending_extension

    # Step 2: User resumes speaking within extension window
    handler.feed_partial("mau pesan burger sama kentang goreng")
    assert not handler.has_pending_extension

    # Step 3: Complete utterance arrives
    handler.on_speech_final("mau pesan burger sama kentang goreng", 3200.0)
    await asyncio.sleep(0.01)

    # Finished immediately with full utterance
    assert len(finalized_events) == 1
    assert finalized_events[0][0] == "mau pesan burger sama kentang goreng"
