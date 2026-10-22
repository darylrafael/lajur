"""Deepgram STT adapter supporting REST file transcription and live WebSocket streaming."""

from __future__ import annotations

import json
import os
import time
from collections.abc import AsyncIterator
from pathlib import Path

import aiohttp

from lajur_agent.adapters.base import STTAdapter, TranscriptionEvent


class DeepgramSTTAdapter(STTAdapter):
    """Speech-to-Text adapter connecting to Deepgram Nova-2/Nova-3 models."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "nova-2",
        language: str = "id",
        smart_format: bool = True,
    ) -> None:
        self._api_key = api_key or os.getenv("DEEPGRAM_API_KEY", "")
        if not self._api_key:
            raise ValueError("DEEPGRAM_API_KEY must be provided or set in environment variables.")
        self._model = model
        self._language = language
        self._smart_format = smart_format
        self._rest_url = "https://api.deepgram.com/v1/listen"
        self._ws_url = "wss://api.deepgram.com/v1/listen"

    @property
    def name(self) -> str:
        return f"deepgram-{self._model}"

    async def transcribe_file(self, file_path: Path | str) -> str:
        """Transcribe an entire audio file via Deepgram REST API."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        content_type = "audio/wav" if path.suffix.lower() == ".wav" else "audio/mp3"

        with open(path, "rb") as f:
            audio_bytes = f.read()

        params = {
            "model": self._model,
            "language": self._language,
            "smart_format": "true" if self._smart_format else "false",
        }

        headers = {
            "Authorization": f"Token {self._api_key}",
            "Content-Type": content_type,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self._rest_url,
                params=params,
                data=audio_bytes,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    raise RuntimeError(f"Deepgram REST STT failed ({resp.status}): {err[:300]}")
                data = await resp.json()

        try:
            return (
                data["results"]["channels"][0]["alternatives"][0]["transcript"].strip()
            )
        except (KeyError, IndexError):
            return ""

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        sample_rate: int = 16000,
    ) -> AsyncIterator[TranscriptionEvent]:
        """Stream raw audio chunks over WebSocket to Deepgram and yield events in real time."""
        params = (
            f"?model={self._model}&language={self._language}"
            f"&encoding=linear16&sample_rate={sample_rate}"
            f"&smart_format={'true' if self._smart_format else 'false'}"
        )
        url = f"{self._ws_url}{params}"
        headers = {"Authorization": f"Token {self._api_key}"}

        start_time = time.perf_counter()

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url, headers=headers) as ws:
                # 1. Stream all chunks
                async for chunk in audio_stream:
                    if chunk:
                        await ws.send_bytes(chunk)

                # Send close stream flag to Deepgram
                await ws.send_bytes(b"")

                # 2. Receive responses until stream closes
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        is_final = data.get("is_final", False)
                        try:
                            alt = data["channel"]["alternatives"][0]
                            text = alt.get("transcript", "").strip()
                            confidence = float(alt.get("confidence", 1.0))
                        except (KeyError, IndexError):
                            text = ""
                            confidence = 1.0

                        if text:
                            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                            yield TranscriptionEvent(
                                text=text,
                                is_final=is_final,
                                confidence=confidence,
                                latency_ms=elapsed_ms,
                            )
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        break
