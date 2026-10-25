"""ElevenLabs TTS streaming adapter supporting low-latency PCM output."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import aiohttp

from lajur_agent.adapters.base import TTSAdapter, TTSAudioChunk


class ElevenLabsTTSAdapter(TTSAdapter):
    """Text-to-Speech adapter connecting to ElevenLabs Flash v2.5 streaming endpoints."""

    def __init__(
        self,
        api_key: str | None = None,
        voice_id: str = "EXAVITQu4vr4xnSDxMaL",  # Sarah (warm, friendly)
        model_id: str = "eleven_flash_v2_5",
        output_format: str = "pcm_16000",
    ) -> None:
        self._api_key = api_key or os.getenv("ELEVENLABS_API_KEY", "")
        if not self._api_key:
            raise ValueError("ELEVENLABS_API_KEY must be provided or set in environment variables.")
        self._voice_id = voice_id
        self._model_id = model_id
        self._output_format = output_format
        self._sample_rate = 16000 if "16000" in output_format else 24000
        self._base_url = f"https://api.elevenlabs.io/v1/text-to-speech/{self._voice_id}/stream"

    @property
    def name(self) -> str:
        return f"elevenlabs-{self._model_id}"

    async def get_remaining_characters(self) -> int:
        """Query ElevenLabs subscription endpoint for remaining monthly characters."""
        url = "https://api.elevenlabs.io/v1/user/subscription"
        headers = {"xi-api-key": self._api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    char_count = data.get("character_count", 0)
                    char_limit = data.get("character_limit", 0)
                    return max(0, char_limit - char_count)
                raise RuntimeError(f"Failed to fetch subscription quota: {resp.status}")

    async def synthesize_text(self, text: str) -> bytes:
        """Synthesize an entire string into raw audio bytes (PCM or MP3)."""
        if not text.strip():
            return b""

        url = f"{self._base_url}?output_format={self._output_format}&optimize_streaming_latency=4"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": self._model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    raise RuntimeError(f"ElevenLabs synthesis failed ({resp.status}): {err[:300]}")
                return await resp.read()

    async def stream_audio_chunks(
        self, text: str, chunk_size: int = 640
    ) -> AsyncIterator[bytes]:
        """Stream raw audio chunks of exact size as they arrive over HTTP streaming."""
        if not text.strip():
            return

        url = f"{self._base_url}?output_format={self._output_format}&optimize_streaming_latency=4"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": self._model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    raise RuntimeError(f"ElevenLabs streaming failed ({resp.status}): {err[:300]}")

                buf = bytearray()
                async for chunk in resp.content.iter_chunked(2048):
                    buf.extend(chunk)
                    while len(buf) >= chunk_size:
                        frame = bytes(buf[:chunk_size])
                        del buf[:chunk_size]
                        yield frame
                if buf:
                    buf.extend(b"\x00" * (chunk_size - len(buf)))
                    yield bytes(buf)

    async def synthesize_stream(
        self,
        text_stream: AsyncIterator[str],
    ) -> AsyncIterator[TTSAudioChunk]:
        """Collect incoming text chunks and stream raw PCM audio chunks back."""
        # Collect full turn text (streaming input requires websocket; REST stream takes text body)
        full_text_list: list[str] = []
        async for chunk in text_stream:
            full_text_list.append(chunk)

        full_text = "".join(full_text_list).strip()
        if not full_text:
            yield TTSAudioChunk(audio_bytes=b"", sample_rate=self._sample_rate, is_final=True)
            return

        url = f"{self._base_url}?output_format={self._output_format}&optimize_streaming_latency=4"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": full_text,
            "model_id": self._model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    raise RuntimeError(f"ElevenLabs streaming failed ({resp.status}): {err[:300]}")

                # Stream out chunks as they arrive from ElevenLabs
                async for chunk in resp.content.iter_chunked(2048):
                    if chunk:
                        yield TTSAudioChunk(
                            audio_bytes=chunk,
                            sample_rate=self._sample_rate,
                            is_final=False,
                        )

                yield TTSAudioChunk(
                    audio_bytes=b"",
                    sample_rate=self._sample_rate,
                    is_final=True,
                )
