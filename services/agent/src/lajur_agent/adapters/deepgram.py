"""Deepgram STT adapter supporting REST file transcription and live WebSocket streaming with Nova-3."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
from collections.abc import AsyncIterator
from pathlib import Path

import aiohttp

from lajur_agent.adapters.base import STTAdapter, TranscriptionEvent


def load_default_menu_keyterms(max_terms: int = 100) -> list[str]:
    """Extract priority keyterms from menu.json for Deepgram Nova-3 keyterm boosting."""
    candidates = [
        Path(__file__).resolve().parents[4] / "eval" / "menu" / "menu.json",
        Path("eval/menu/menu.json"),
        Path("../eval/menu/menu.json"),
    ]
    menu_file = next((c for c in candidates if c.exists()), None)
    if not menu_file:
        return []

    try:
        data = json.loads(menu_file.read_text(encoding="utf-8"))
        terms: set[str] = set()
        for item in data.get("items", []):
            terms.add(item["name_id"].lower())
            for a in item.get("aliases", []):
                terms.add(a.lower())
        for combo in data.get("combos", []):
            terms.add(combo["name_id"].lower())
            for a in combo.get("aliases", []):
                terms.add(a.lower())

        clean = [t for t in sorted(terms) if len(t) > 2 and not t.isdigit()]
        return clean[:max_terms]
    except Exception:
        return []


class DeepgramSTTAdapter(STTAdapter):
    """Speech-to-Text adapter connecting to Deepgram Nova-3 / Nova-2 models."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "nova-2",
        language: str = "id",
        smart_format: bool = True,
        endpointing: int | None = 300,
        keyterms: list[str] | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("DEEPGRAM_API_KEY", "")
        if not self._api_key:
            raise ValueError("DEEPGRAM_API_KEY must be provided or set in environment variables.")
        self._model = model
        self._language = language
        self._smart_format = smart_format
        self._endpointing = endpointing
        self._keyterms = keyterms if keyterms is not None else load_default_menu_keyterms(max_terms=100)
        self._rest_url = "https://api.deepgram.com/v1/listen"
        self._ws_url = "wss://api.deepgram.com/v1/listen"

    @property
    def name(self) -> str:
        return f"deepgram-{self._model}"

    def _build_query_params(self, sample_rate: int | None = None) -> list[tuple[str, str]]:
        """Construct query tuples for Deepgram Nova-3."""
        params: list[tuple[str, str]] = [
            ("model", self._model),
            ("language", self._language),
            ("smart_format", "true" if self._smart_format else "false"),
        ]
        if sample_rate:
            params.extend([
                ("encoding", "linear16"),
                ("sample_rate", str(sample_rate)),
            ])
        if self._endpointing is not None:
            params.append(("endpointing", str(self._endpointing)))

        # Nova-3 Keyterm prompting: repeat 'keyterm' parameter without weights
        for term in self._keyterms[:100]:
            params.append(("keyterm", term))

        return params

    async def transcribe_file(self, file_path: Path | str) -> str:
        """Transcribe an entire audio file via Deepgram REST API."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        content_type = "audio/wav" if path.suffix.lower() == ".wav" else "audio/mp3"

        with open(path, "rb") as f:
            audio_bytes = f.read()

        params = self._build_query_params()
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
            return data["results"]["channels"][0]["alternatives"][0]["transcript"].strip()
        except (KeyError, IndexError):
            return ""

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        sample_rate: int = 16000,
    ) -> AsyncIterator[TranscriptionEvent]:
        """Stream raw audio chunks over WebSocket to Deepgram and yield events in real time."""
        params = self._build_query_params(sample_rate=sample_rate)
        query_str = urllib.parse.urlencode(params)
        url = f"{self._ws_url}?{query_str}"
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
