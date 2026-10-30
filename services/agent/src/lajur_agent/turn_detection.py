"""Adaptive endpointing and turn-detection heuristics for mid-thought hesitation.

Prevents false-cutoffs when the customer pauses mid-sentence (fillers, dangling
conjunctions, dangling quantities) while keeping base endpointing unchanged at 300ms.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from collections.abc import Awaitable, Callable

logger = logging.getLogger("lajur.agent.turn_detection")

# Indonesian hesitation fillers and thinking particles
HESITATION_FILLERS: frozenset[str] = frozenset({
    "eh",
    "anu",
    "sebentar",
    "bentar",
    "tunggu",
    "apa ya",
    "apa tuh",
    "hmm",
    "hmmm",
    "emmm",
    "em",
    "umm",
    "aduh",
    "wait",
    "uhh",
    "uhhh",
})

# Dangling conjunctions / prepositions indicating incomplete sentence
DANGLING_CONJUNCTIONS: frozenset[str] = frozenset({
    "sama",
    "dan",
    "terus",
    "lalu",
    "tapi",
    "dengan",
    "buat",
    "untuk",
    "tambah",
    "juga",
    "serta",
    "atau",
    "sama...",
})

# Dangling verbs / order starters without items
DANGLING_VERBS: frozenset[str] = frozenset({
    "mau",
    "ingin",
    "pesan",
    "order",
    "minta",
    "tambah",
    "tolong",
    "kasih",
})

# Quantities that are dangling ONLY when preceded by conjunctions or verbs
DANGLING_QUANTITIES: frozenset[str] = frozenset({
    "satu",
    "dua",
    "tiga",
    "empat",
    "lima",
    "enam",
    "tujuh",
    "delapan",
    "sembilan",
    "sepuluh",
    "sebelas",
    "dua belas",
    "one",
    "two",
    "three",
})


def is_mid_thought(text: str) -> bool:
    """Determine if an utterance or partial transcript ends mid-thought.

    Returns:
        True if the trailing token represents a filler, dangling conjunction,
        or dangling quantity/verb requiring bounded endpointing extension.
    """
    cleaned = text.strip().lower()
    cleaned = re.sub(r"[.,?!]+$", "", cleaned).strip()
    if not cleaned:
        return False

    words = cleaned.split()
    if not words:
        return False

    last_word = words[-1]

    # 1. Direct match on fillers, conjunctions, or trailing verbs
    if (
        last_word in HESITATION_FILLERS
        or last_word in DANGLING_CONJUNCTIONS
        or last_word in DANGLING_VERBS
    ):
        return True

    # 2. Check 2-word fillers (e.g. "apa ya", "tunggu sebentar")
    if len(words) >= 2:
        last_two = f"{words[-2]} {words[-1]}"
        if last_two in HESITATION_FILLERS:
            return True

        # Dangling quantity: preceded by conjunction/verb without item (e.g. "sama satu", "mau dua")
        if (
            words[-2] in DANGLING_CONJUNCTIONS or words[-2] in DANGLING_VERBS
        ) and last_word in DANGLING_QUANTITIES:
            return True

    return False


class AdaptiveEndpointingHandler:
    """Manages adaptive turn finalization with bounded hesitation window extension."""

    def __init__(
        self,
        on_finalize: Callable[[str, float], Awaitable[None]],
        base_endpointing_ms: float = 300.0,
        extension_ms: float | None = None,
    ) -> None:
        self.on_finalize = on_finalize
        self.base_endpointing_ms = base_endpointing_ms
        if extension_ms is None:
            self.extension_ms = float(os.getenv("HESITATION_EXTENSION_MS", "500.0"))
        else:
            self.extension_ms = extension_ms

        self._pending_task: asyncio.Task[None] | None = None
        self._latest_text: str = ""
        self._latest_speech_end: float = 0.0

    @property
    def has_pending_extension(self) -> bool:
        """True if an endpointing extension timer is currently running."""
        return self._pending_task is not None and not self._pending_task.done()

    def cancel_pending(self) -> None:
        """Cancel any running extension delay (e.g. when user resumes speaking)."""
        if self._pending_task and not self._pending_task.done():
            self._pending_task.cancel()
            self._pending_task = None

    def feed_partial(self, partial_text: str) -> None:
        """Inform handler of new incoming partial transcript."""
        if partial_text.strip():
            # If user spoke again while an extension timer was ticking, cancel it
            if self.has_pending_extension:
                logger.debug(
                    "[AdaptiveEndpointing] User resumed speech with '%s'; cancelling pending extension.",
                    partial_text,
                )
                self.cancel_pending()
            self._latest_text = partial_text

    async def _execute_finalize(self, text: str, speech_end: float, was_extended: bool) -> None:
        try:
            if was_extended:
                logger.info(
                    "[AdaptiveEndpointing] Extension elapsed (%.0f ms). Finalizing turn with '%s'.",
                    self.extension_ms,
                    text,
                )
            await self.on_finalize(text, speech_end)
        except Exception as e:
            logger.error("[AdaptiveEndpointing] Error executing on_finalize: %s", e)
        finally:
            self._pending_task = None

    def on_speech_final(self, final_text: str, timestamp: float) -> None:
        """Handle speech_final event emitted by base STT endpointing."""
        cleaned = final_text.strip()
        if not cleaned:
            return

        self._latest_text = cleaned
        self._latest_speech_end = timestamp

        # Cancel any previous pending task
        self.cancel_pending()

        if is_mid_thought(cleaned):
            # Mid-thought detected: extend endpointing window by extension_ms
            logger.info(
                "[AdaptiveEndpointing] Hesitation detected in '%s'. Extending endpointing window by %.0f ms.",
                cleaned,
                self.extension_ms,
            )

            async def _delay_task() -> None:
                try:
                    await asyncio.sleep(self.extension_ms / 1000.0)
                    # Use latest text if updated
                    target_text = self._latest_text or cleaned
                    target_ts = self._latest_speech_end or timestamp
                    await self._execute_finalize(target_text, target_ts, was_extended=True)
                except asyncio.CancelledError:
                    # Speech continued; cancelled gracefully
                    pass

            self._pending_task = asyncio.create_task(_delay_task())
        else:
            # Clean complete utterance: finalize immediately (0 ms added latency)
            logger.debug(
                "[AdaptiveEndpointing] Complete utterance confirmed: '%s'. Finalizing immediately (0ms added).",
                cleaned,
            )
            self._pending_task = asyncio.create_task(
                self._execute_finalize(cleaned, timestamp, was_extended=False)
            )
