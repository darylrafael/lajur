"""Groq Cloud STT adapter using Whisper Large v3 / Turbo models."""

from __future__ import annotations

import io
import os
import time
import wave
from collections.abc import AsyncIterator
from pathlib import Path

import aiohttp

from lajur_agent.adapters.base import STTAdapter, TranscriptionEvent


class GroqSTTAdapter(STTAdapter):
    """Speech-to-Text adapter backed by Groq's high-speed Whisper endpoints."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "whisper-large-v3-turbo",
        language: str = "id",
    ) -> None:
        self._api_key = api_key or os.getenv("GROQ_API_KEY", "")
        if not self._api_key:
            raise ValueError("GROQ_API_KEY must be provided or set in environment variables.")
        self._model = model
        self._language = language
        self._endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"

    @property
    def name(self) -> str:
        return f"groq-{self._model}"

    async def transcribe_file(self, file_path: Path | str) -> str:
        """Transcribe an audio file into text using Groq Whisper API."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        data = aiohttp.FormData()
        with open(path, "rb") as f:
            file_bytes = f.read()

        data.add_field("file", file_bytes, filename=path.name, content_type="audio/wav")
        data.add_field("model", self._model)
        if self._language:
            data.add_field("language", self._language)
        data.add_field("response_format", "json")

        headers = {"Authorization": f"Bearer {self._api_key}"}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self._endpoint,
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    raise RuntimeError(f"Groq STT failed with status {resp.status}: {err[:300]}")
                result = await resp.json()
                return result.get("text", "").strip()

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        sample_rate: int = 16000,
    ) -> AsyncIterator[TranscriptionEvent]:
        """Buffer incoming PCM chunks into a WAV payload and transcribe turn at completion."""
        pcm_buffer = bytearray()

        async for chunk in audio_stream:
            pcm_buffer.extend(chunk)

        if not pcm_buffer:
            yield TranscriptionEvent(text="", is_final=True, latency_ms=0.0)
            return

        # Pack buffered PCM 16-bit into in-memory WAV container
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit PCM
            wf.setframerate(sample_rate)
            wf.writeframes(bytes(pcm_buffer))

        wav_bytes = wav_io.getvalue()

        data = aiohttp.FormData()
        data.add_field("file", wav_bytes, filename="stream.wav", content_type="audio/wav")
        data.add_field("model", self._model)
        if self._language:
            data.add_field("language", self._language)
        data.add_field("response_format", "json")

        headers = {"Authorization": f"Bearer {self._api_key}"}

        req_start = time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self._endpoint,
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                latency_ms = (time.perf_counter() - req_start) * 1000.0
                if resp.status != 200:
                    err = await resp.text()
                    raise RuntimeError(f"Groq STT failed with status {resp.status}: {err[:300]}")
                result = await resp.json()
                transcript = result.get("text", "").strip()

        yield TranscriptionEvent(
            text=transcript,
            is_final=True,
            confidence=1.0,
            latency_ms=latency_ms,
        )
