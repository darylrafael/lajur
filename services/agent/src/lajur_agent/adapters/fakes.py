"""Deterministic fake adapters for offline evaluation harness and unit testing."""

from __future__ import annotations

import asyncio
import math
import struct
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from lajur_agent.adapters.base import (
    IntentResult,
    LLMIntentAdapter,
    STTAdapter,
    TranscriptionEvent,
    TTSAdapter,
    TTSAudioChunk,
)


class FakeSTTAdapter(STTAdapter):
    """Deterministic, simulated STT adapter for offline benchmarks and CI."""

    def __init__(
        self,
        canned_transcripts: dict[str, str] | None = None,
        default_transcript: str = "saya mau pesan burger sapi tunggal satu",
        simulated_delay_ms: float = 10.0,
    ) -> None:
        self._canned = canned_transcripts or {}
        self._default = default_transcript
        self._delay_s = simulated_delay_ms / 1000.0

    @property
    def name(self) -> str:
        return "fake-stt"

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        sample_rate: int = 16000,
    ) -> AsyncIterator[TranscriptionEvent]:
        # Consume stream
        chunk_count = 0
        async for chunk in audio_stream:
            chunk_count += 1
            if self._delay_s > 0:
                await asyncio.sleep(self._delay_s)
            if chunk_count % 3 == 0:
                yield TranscriptionEvent(
                    text="saya mau...",
                    is_final=False,
                    confidence=0.8,
                    latency_ms=chunk_count * 50.0,
                )

        # Final recognition
        yield TranscriptionEvent(
            text=self._default,
            is_final=True,
            confidence=0.98,
            latency_ms=chunk_count * 50.0 + 30.0,
        )

    async def transcribe_file(self, file_path: Path | str) -> str:
        p = Path(file_path)
        if self._delay_s > 0:
            await asyncio.sleep(self._delay_s)
        return self._canned.get(p.name, self._canned.get(str(p), self._default))


class FakeTTSAdapter(TTSAdapter):
    """Deterministic, simulated TTS adapter generating synthetic PCM sine waves."""

    def __init__(
        self,
        sample_rate: int = 16000,
        simulated_ttft_ms: float = 20.0,
    ) -> None:
        self._sample_rate = sample_rate
        self._ttft_s = simulated_ttft_ms / 1000.0

    @property
    def name(self) -> str:
        return "fake-tts"

    def _generate_sine_pcm(self, duration_s: float = 0.5, freq_hz: float = 440.0) -> bytes:
        total_samples = int(self._sample_rate * duration_s)
        out = bytearray()
        for i in range(total_samples):
            val = int(math.sin(2.0 * math.pi * freq_hz * (i / self._sample_rate)) * 10000)
            out.extend(struct.pack("<h", max(-32768, min(32767, val))))
        return bytes(out)

    async def synthesize_stream(
        self,
        text_stream: AsyncIterator[str],
    ) -> AsyncIterator[TTSAudioChunk]:
        first = True
        async for text_chunk in text_stream:
            if not text_chunk.strip():
                continue
            if first and self._ttft_s > 0:
                await asyncio.sleep(self._ttft_s)
                first = False
            # Generate 0.1s PCM chunk per token
            pcm = self._generate_sine_pcm(duration_s=0.1)
            yield TTSAudioChunk(audio_bytes=pcm, sample_rate=self._sample_rate, is_final=False)

        yield TTSAudioChunk(audio_bytes=b"", sample_rate=self._sample_rate, is_final=True)

    async def synthesize_text(self, text: str) -> bytes:
        if self._ttft_s > 0:
            await asyncio.sleep(self._ttft_s)
        duration = max(0.5, min(5.0, len(text) * 0.05))
        return self._generate_sine_pcm(duration_s=duration)


class FakeLLMIntentAdapter(LLMIntentAdapter):
    """Deterministic, simulated LLM intent parsing adapter."""

    def __init__(
        self,
        canned_intents: dict[str, list[dict[str, Any]]] | None = None,
        simulated_ttft_ms: float = 25.0,
    ) -> None:
        self._canned = canned_intents or {}
        self._ttft_s = simulated_ttft_ms / 1000.0

    @property
    def name(self) -> str:
        return "fake-llm"

    async def parse_intent(
        self,
        transcript: str,
        history: list[dict[str, str]] | None = None,
    ) -> IntentResult:
        start_time = time.perf_counter()
        if self._ttft_s > 0:
            await asyncio.sleep(self._ttft_s)

        ttft_ms = (time.perf_counter() - start_time) * 1000.0

        # Check canned intents
        if transcript in self._canned:
            intents = self._canned[transcript]
        elif "kentang" in transcript.lower() or "fries" in transcript.lower():
            intents = [
                {
                    "type": "add_item",
                    "params": {"item_id": "kentang_goreng", "quantity": 1, "size": "size_regular"},
                }
            ]
        elif "batal" in transcript.lower() or "tidak jadi" in transcript.lower():
            intents = [{"type": "undo", "params": {"steps": 1}}]
        else:
            intents = [
                {
                    "type": "add_item",
                    "params": {"item_id": "burger_sapi_tunggal", "quantity": 1, "size": "size_regular"},
                }
            ]

        total_ms = (time.perf_counter() - start_time) * 1000.0
        words = transcript.split()

        return IntentResult(
            intents=intents,
            bot_reply="Baik kak, pesanannya sudah saya catat ya.",
            ttft_ms=ttft_ms,
            total_latency_ms=total_ms,
            tokens_in=len(words) * 6 + 120,
            tokens_out=45,
            raw_response="{\"intents\": [...] }",
            metadata={"model": "fake-llm-v1"},
        )
