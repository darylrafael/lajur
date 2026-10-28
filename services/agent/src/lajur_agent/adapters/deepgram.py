"""Deepgram STT adapter supporting REST file transcription and live WebSocket streaming with Nova-3."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import urllib.parse
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Callable

import aiohttp

from lajur_agent.adapters.base import STTAdapter, TranscriptionEvent

logger = logging.getLogger("lajur.agent.deepgram")


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


class PersistentDeepgramStream:
    """Persistent WebSocket streaming session to Deepgram Nova-3.

    Features:
    - Reuses an existing aiohttp.ClientSession across turns.
    - Sends periodic KeepAlive messages during idle periods to prevent timeout.
    - Transparently reconnects if the socket drops.
    - Emits first partial transcript timestamp (t_first_partial) and speech_final timestamp.
    """

    def __init__(
        self,
        api_key: str,
        ws_url: str,
        params: list[tuple[str, str]],
        session: aiohttp.ClientSession,
    ) -> None:
        self._api_key = api_key
        self._ws_url = ws_url
        self._params = params
        self._session = session
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._keepalive_task: asyncio.Task[None] | None = None
        self._receiver_task: asyncio.Task[None] | None = None
        self._is_running = False
        self._connect_time_ms: float = 0.0

        # Turn callbacks and state
        self._on_first_partial: Callable[[float], None] | None = None
        self._on_speech_final: Callable[[str, float], None] | None = None
        self._accumulated_parts: list[str] = []
        self.t_first_partial: float | None = None
        self.t_speech_final: float | None = None
        self.last_transcript: str = ""
        self._stt_done_event = asyncio.Event()

    @property
    def is_connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    @property
    def connect_time_ms(self) -> float:
        return self._connect_time_ms

    async def connect(self) -> float:
        """Establish persistent WebSocket connection to Deepgram."""
        t_start = time.perf_counter()
        query_str = urllib.parse.urlencode(self._params)
        url = f"{self._ws_url}?{query_str}"
        headers = {"Authorization": f"Token {self._api_key}"}

        self._ws = await self._session.ws_connect(url, headers=headers)
        self._connect_time_ms = (time.perf_counter() - t_start) * 1000.0
        self._is_running = True
        self._receiver_task = asyncio.create_task(self._receiver_loop())
        self._start_keepalive()
        logger.info("Persistent Deepgram stream connected in %.1f ms", self._connect_time_ms)
        return self._connect_time_ms

    async def reconnect(self) -> float:
        """Reconnect a dropped Deepgram WebSocket connection."""
        logger.warning("Reconnecting dropped Deepgram WebSocket connection...")
        t_start = time.perf_counter()
        query_str = urllib.parse.urlencode(self._params)
        url = f"{self._ws_url}?{query_str}"
        headers = {"Authorization": f"Token {self._api_key}"}

        if self._ws and not self._ws.closed:
            await self._ws.close()

        self._ws = await self._session.ws_connect(url, headers=headers)
        reconnect_ms = (time.perf_counter() - t_start) * 1000.0
        if self._receiver_task is None or self._receiver_task.done():
            self._receiver_task = asyncio.create_task(self._receiver_loop())
        logger.info("Deepgram stream reconnected in %.1f ms", reconnect_ms)
        return reconnect_ms

    def _start_keepalive(self) -> None:
        if self._keepalive_task is None or self._keepalive_task.done():
            self._keepalive_task = asyncio.create_task(self._keepalive_loop())

    async def _keepalive_loop(self) -> None:
        """Send periodic KeepAlive messages every 5 seconds during idle periods."""
        while self._is_running:
            await asyncio.sleep(5.0)
            if not self._is_running:
                break
            try:
                if self._ws and not self._ws.closed:
                    await self._ws.send_str(json.dumps({"type": "KeepAlive"}))
            except Exception as e:
                logger.debug("Deepgram keepalive error: %s", e)

    def begin_turn(
        self,
        on_first_partial: Callable[[float], None] | None = None,
        on_speech_final: Callable[[str, float], None] | None = None,
    ) -> asyncio.Event:
        """Prepare stream for a new dialog turn."""
        self._on_first_partial = on_first_partial
        self._on_speech_final = on_speech_final
        self._accumulated_parts.clear()
        self.t_first_partial = None
        self.t_speech_final = None
        self.last_transcript = ""
        self._stt_done_event.clear()
        return self._stt_done_event

    async def send_audio_chunk(self, chunk: bytes) -> None:
        """Send a single raw PCM chunk to Deepgram with automatic reconnect on failure."""
        if not self._is_running or not chunk:
            return
        if self._ws is None or self._ws.closed:
            await self.reconnect()
        assert self._ws is not None
        try:
            await self._ws.send_bytes(chunk)
        except Exception:
            await self.reconnect()
            assert self._ws is not None
            await self._ws.send_bytes(chunk)

    async def finalize(self) -> None:
        """Send Finalize message to flush remaining audio through Deepgram."""
        if self._ws and not self._ws.closed:
            try:
                await self._ws.send_str(json.dumps({"type": "Finalize"}))
            except Exception:
                pass

    async def _receiver_loop(self) -> None:
        """Background receiver for streaming transcript events."""
        while self._is_running and self._ws and not self._ws.closed:
            try:
                async for msg in self._ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        is_final = data.get("is_final", False)
                        speech_final = data.get("speech_final", False)

                        # Capture partial / interim transcript
                        transcript_part = ""
                        try:
                            transcript_part = data["channel"]["alternatives"][0]["transcript"].strip()
                        except (KeyError, IndexError):
                            pass

                        if transcript_part:
                            now = time.perf_counter()
                            if self.t_first_partial is None:
                                self.t_first_partial = now
                                if self._on_first_partial:
                                    self._on_first_partial(now)

                            if is_final:
                                self._accumulated_parts.append(transcript_part)

                        # Capture endpointing speech_final event
                        if speech_final:
                            now = time.perf_counter()
                            self.t_speech_final = now
                            full_transcript = " ".join(self._accumulated_parts).strip()
                            self.last_transcript = full_transcript
                            if self._on_speech_final:
                                self._on_speech_final(full_transcript, now)
                            self._stt_done_event.set()

                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        break
            except Exception as e:
                logger.warning("Deepgram receiver exception: %s", e)
                if self._is_running:
                    await asyncio.sleep(0.5)
                    try:
                        await self.reconnect()
                    except Exception:
                        pass

    async def close(self) -> None:
        """Shut down the persistent stream and release resources."""
        self._is_running = False
        if self._keepalive_task:
            self._keepalive_task.cancel()
            self._keepalive_task = None
        if self._ws and not self._ws.closed:
            try:
                await self._ws.send_bytes(b"")
                await self._ws.close()
            except Exception:
                pass
            self._ws = None
        if self._receiver_task:
            self._receiver_task.cancel()
            self._receiver_task = None


class DeepgramSTTAdapter(STTAdapter):
    """Speech-to-Text adapter connecting to Deepgram Nova-3 / Nova-2 models."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "nova-2",
        language: str = "id",
        smart_format: bool = True,
        endpointing: int | None = 500,
        keyterms: list[str] | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("DEEPGRAM_API_KEY", "")
        if not self._api_key:
            raise ValueError("DEEPGRAM_API_KEY must be provided or set in environment variables.")
        self._model = model
        self._language = language
        self._smart_format = smart_format
        self._endpointing = endpointing
        self._keyterms = keyterms if keyterms is not None else load_default_menu_keyterms(max_terms=100)
        self._session = session
        self._owns_session = session is None
        self._rest_url = "https://api.deepgram.com/v1/listen"
        self._ws_url = "wss://api.deepgram.com/v1/listen"

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

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

    async def create_persistent_stream(self, sample_rate: int = 16000) -> PersistentDeepgramStream:
        """Create and return a PersistentDeepgramStream attached to this adapter's session."""
        session = await self._get_session()
        params = self._build_query_params(sample_rate=sample_rate)
        return PersistentDeepgramStream(
            api_key=self._api_key,
            ws_url=self._ws_url,
            params=params,
            session=session,
        )

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

        session = await self._get_session()
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

        session = await self._get_session()
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

    async def close(self) -> None:
        """Close session if owned by adapter."""
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()
