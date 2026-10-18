"""Live Edge-TTS adapter for zero-cost, high-fidelity Indonesian Neural TTS."""

from __future__ import annotations

import io
from collections.abc import AsyncIterator

import edge_tts

from lajur_agent.adapters.base import TTSAdapter, TTSAudioChunk


class EdgeTTSAdapter(TTSAdapter):
    """Zero-cost TTS adapter using Microsoft Edge Azure Neural voices."""

    def __init__(
        self,
        voice: str = "id-ID-GadisNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
    ) -> None:
        self._voice = voice
        self._rate = rate
        self._volume = volume
        self._pitch = pitch

    @property
    def name(self) -> str:
        return f"edge-tts-{self._voice.lower().replace('id-id-', '')}"

    @property
    def voice(self) -> str:
        return self._voice

    async def synthesize_text(self, text: str) -> bytes:
        """Synthesize text into raw audio bytes."""
        if not text.strip():
            return b""
        communicate = edge_tts.Communicate(
            text=text,
            voice=self._voice,
            rate=self._rate,
            volume=self._volume,
            pitch=self._pitch,
        )
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio" and "data" in chunk:
                data = chunk["data"]
                if isinstance(data, bytes):
                    buffer.write(data)
        return buffer.getvalue()

    async def synthesize_stream(
        self,
        text_stream: AsyncIterator[str],
    ) -> AsyncIterator[TTSAudioChunk]:
        """Synthesize incoming text chunks into streaming audio chunks."""
        async for text_segment in text_stream:
            if not text_segment.strip():
                continue
            communicate = edge_tts.Communicate(
                text=text_segment,
                voice=self._voice,
                rate=self._rate,
                volume=self._volume,
                pitch=self._pitch,
            )
            async for chunk in communicate.stream():
                if chunk.get("type") == "audio" and "data" in chunk:
                    data = chunk["data"]
                    if isinstance(data, bytes):
                        yield TTSAudioChunk(
                            audio_bytes=data,
                            sample_rate=24000,
                            is_final=False,
                        )
        yield TTSAudioChunk(audio_bytes=b"", sample_rate=24000, is_final=True)
