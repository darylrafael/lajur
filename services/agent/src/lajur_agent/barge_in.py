"""Barge-in detection and echo-bleed guard for full-duplex voice dialog.

Handles:
- Immediate audio output cancellation when user interrupts the bot.
- Cancellation of in-flight LLM/TTS generation tasks.
- Acoustic echo bleed guard (R15): filtering transient noise/echo spikes (<150ms).
- Cart state consistency preservation.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import Awaitable, Callable

logger = logging.getLogger("lajur.agent.barge_in")


class BargeInController:
    """Manages audio playback interruption and in-flight cancellation with echo-bleed guard."""

    def __init__(
        self,
        min_speech_duration_ms: float | None = None,
        on_barge_in_triggered: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        if min_speech_duration_ms is None:
            self.min_speech_duration_ms = float(
                os.getenv("BARGE_IN_MIN_SPEECH_DURATION_MS", "150.0")
            )
        else:
            self.min_speech_duration_ms = min_speech_duration_ms

        self.on_barge_in_triggered = on_barge_in_triggered

        self._is_bot_speaking = False
        self._is_generation_in_flight = False
        self._playback_cancel_event = asyncio.Event()
        self._in_flight_tasks: set[asyncio.Task[object]] = set()

        self._speech_start_ts: float | None = None
        self._last_barge_in_ts: float | None = None
        self._last_stop_latency_ms: float = 0.0

    @property
    def is_bot_speaking(self) -> bool:
        return self._is_bot_speaking

    @property
    def is_generation_in_flight(self) -> bool:
        return self._is_generation_in_flight

    @property
    def playback_cancelled(self) -> bool:
        return self._playback_cancel_event.is_set()

    @property
    def last_stop_latency_ms(self) -> float:
        return self._last_stop_latency_ms

    def start_bot_speaking(self) -> asyncio.Event:
        """Mark that bot audio playback has started and reset cancellation event."""
        self._is_bot_speaking = True
        self._playback_cancel_event.clear()
        return self._playback_cancel_event

    def finish_bot_speaking(self) -> None:
        """Mark that bot audio playback finished normally or was stopped."""
        self._is_bot_speaking = False
        self._playback_cancel_event.clear()

    def register_in_flight_task(self, task: asyncio.Task[object]) -> None:
        """Track in-flight background task (e.g. LLM/TTS generation) for cancellation."""
        self._is_generation_in_flight = True
        self._in_flight_tasks.add(task)
        task.add_done_callback(self._on_task_done)

    def _on_task_done(self, task: asyncio.Task[object]) -> None:
        self._in_flight_tasks.discard(task)
        if not self._in_flight_tasks:
            self._is_generation_in_flight = False

    def clear_in_flight_tasks(self) -> None:
        """Cancel and clear all registered in-flight tasks."""
        for t in list(self._in_flight_tasks):
            if not t.done():
                t.cancel()
        self._in_flight_tasks.clear()
        self._is_generation_in_flight = False

    def on_user_speech_frame(self, has_voice: bool, now: float | None = None) -> bool:
        """Evaluate incoming user audio frame energy/voice activity against echo-bleed guard.

        Args:
            has_voice: True if current audio frame or STT partial indicates speech presence.
            now: Optional current timestamp (perf_counter).

        Returns:
            True if barge-in was triggered and playback stopped; False otherwise.
        """
        current_time = now if now is not None else time.perf_counter()

        if not has_voice:
            # Voice stopped or silence frame: reset speech duration accumulator
            self._speech_start_ts = None
            return False

        # Speech detected
        if self._speech_start_ts is None:
            self._speech_start_ts = current_time

        duration_ms = (current_time - self._speech_start_ts) * 1000.0

        # R15 Echo Bleed Guard: ignore bursts shorter than minimum duration
        if duration_ms < self.min_speech_duration_ms:
            logger.debug(
                "[BargeIn Guard] Transient speech energy (%.1f ms < %.1f ms). Ignoring as potential echo bleed.",
                duration_ms,
                self.min_speech_duration_ms,
            )
            return False

        # Sustained speech exceeds minimum duration threshold
        if self._is_bot_speaking or self._is_generation_in_flight:
            t0 = time.perf_counter()
            self._trigger_barge_in()
            self._last_stop_latency_ms = (time.perf_counter() - t0) * 1000.0
            logger.info(
                "[Barge-in] Confirmed interruption after %.1f ms sustained speech. Halting bot playback. Stop latency: %.2f ms.",
                duration_ms,
                self._last_stop_latency_ms,
            )
            return True

        return False

    def _trigger_barge_in(self) -> None:
        """Trigger immediate cancellation of playback and in-flight tasks."""
        self._playback_cancel_event.set()
        self._is_bot_speaking = False
        self.clear_in_flight_tasks()
        self._speech_start_ts = None
        self._last_barge_in_ts = time.perf_counter()

        if self.on_barge_in_triggered:
            try:
                res = self.on_barge_in_triggered()
                if asyncio.iscoroutine(res):
                    asyncio.create_task(res)
            except Exception as e:
                logger.error("[Barge-in] Callback error: %s", e)
