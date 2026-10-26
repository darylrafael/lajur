"""Groq Cloud STT and LLM adapters using Whisper and Qwen models."""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import time
import wave
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import aiohttp
from lajur_cart.intents import IntentEnvelope, UnknownIntent
from pydantic import ValidationError

from lajur_agent.adapters.base import IntentResult, LLMIntentAdapter, STTAdapter, TranscriptionEvent
from lajur_agent.prompts import load_prompt

logger = logging.getLogger("lajur.agent.groq_llm")


class GroqSTTAdapter(STTAdapter):
    """Speech-to-Text adapter backed by Groq's high-speed Whisper endpoints."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "whisper-large-v3-turbo",
        language: str = "id",
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("GROQ_API_KEY", "")
        if not self._api_key:
            raise ValueError("GROQ_API_KEY must be provided or set in environment variables.")
        self._model = model
        self._language = language
        self._endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"
        self._session = session
        self._owns_session = session is None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

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


logger = logging.getLogger("lajur.agent.groq_llm")


class GroqLLMIntentAdapter(LLMIntentAdapter):
    """LLM Intent Parser and Reply Generator adapter backed by Groq Cloud."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "qwen/qwen3.8-27b",
        max_tokens: int = 150,
        temperature: float = 0.1,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("GROQ_API_KEY", "")
        if not self._api_key:
            raise ValueError("GROQ_API_KEY must be provided or set in environment variables.")
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._chat_url = "https://api.groq.com/openai/v1/chat/completions"
        self._parser_prompt, self._parser_prompt_hash = load_prompt("intent_parser_v1.txt")
        self._reply_prompt, self._reply_prompt_hash = load_prompt("reply_generator_v1.txt")
        self._session = session
        self._owns_session = session is None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def prewarm(self) -> float:
        """Pre-warm connection to Groq API and measure TLS/TCP handshake latency in ms ($0 spend)."""
        session = await self._get_session()
        t_start = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with session.get(
                "https://api.groq.com/openai/v1/models",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                await resp.read()
        except Exception as e:
            logger.debug("Groq prewarm error (non-fatal): %s", e)
        return (time.perf_counter() - t_start) * 1000.0

    async def close(self) -> None:
        """Close HTTP session if owned by this adapter."""
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    @property
    def name(self) -> str:
        return f"groq-llm-{self._model}"

    @property
    def prompt_hash(self) -> str:
        return self._parser_prompt_hash

    async def parse_intent(
        self,
        transcript: str,
        history: list[dict[str, str]] | None = None,
        cart_snapshot: dict[str, Any] | None = None,
        pending_choice: dict[str, Any] | None = None,
        menu_context: dict[str, Any] | None = None,
    ) -> IntentResult:
        """Parse an utterance into structured intents according to intent-parser-contract."""
        if not transcript.strip():
            return IntentResult(
                intents=[{"type": "unknown", "raw_text": "", "reason": "empty_transcript"}],
                bot_reply="Bisa diulangi kak?",
                ttft_ms=0.0,
                total_latency_ms=0.0,
                tokens_in=0,
                tokens_out=0,
                raw_response="{}",
                metadata={"prompt_hash": self._parser_prompt_hash, "retries": 0},
            )

        payload_context = {
            "utterance": transcript,
            "cart_snapshot": cart_snapshot or {},
            "pending_choice": pending_choice,
            "menu_context": menu_context or {},
        }
        user_message = json.dumps(payload_context, ensure_ascii=False)

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        # Bounded retry loop (max 1 retry)
        retries = 0
        error_feedback: str | None = None
        latency_ms = 0.0
        tokens_in = 0
        tokens_out = 0

        while retries <= 1:
            messages = [{"role": "system", "content": self._parser_prompt}]
            if history:
                messages.extend(history[-4:])
            if error_feedback:
                messages.append({
                    "role": "user",
                    "content": f"{user_message}\n\nPREVIOUS ERROR: {error_feedback}. Please fix and return valid JSON adhering strictly to the schema.",
                })
            else:
                messages.append({"role": "user", "content": user_message})

            body = {
                "model": self._model,
                "messages": messages,
                "response_format": {"type": "json_object"},
                "temperature": self._temperature,
                "max_tokens": self._max_tokens,
            }

            session = await self._get_session()
            req_start = time.perf_counter()
            try:
                async with session.post(
                    self._chat_url,
                    headers=headers,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                        latency_ms = (time.perf_counter() - req_start) * 1000.0
                        if resp.status != 200:
                            err_text = await resp.text()
                            logger.warning("Groq chat error (%d): %s", resp.status, err_text[:200])
                            if resp.status == 429:
                                try:
                                    retry_after = float(resp.headers.get("retry-after", "6.0"))
                                except (ValueError, TypeError):
                                    retry_after = 6.0
                                await asyncio.sleep(max(3.0, min(retry_after, 8.0)))
                            retries += 1
                            error_feedback = f"HTTP {resp.status}"
                            continue
                        data = await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as net_err:
                logger.warning("Groq network connection error: %s. Retrying...", net_err)
                await asyncio.sleep(2.0)
                retries += 1
                error_feedback = f"Network error: {net_err}"
                continue

            usage = data.get("usage", {})
            tokens_in = usage.get("prompt_tokens", 0)
            tokens_out = usage.get("completion_tokens", 0)
            raw_content = data["choices"][0]["message"]["content"].strip()

            try:
                parsed_json = json.loads(raw_content)
                envelope_dict = {
                    "intents": parsed_json.get("intents", []),
                    "customer_language": parsed_json.get("customer_language", "id"),
                }
                envelope = IntentEnvelope.model_validate(envelope_dict)
                intents_list = [it.model_dump() for it in envelope.intents]
                suggested_reply = parsed_json.get("suggested_reply", "")

                return IntentResult(
                    intents=intents_list,
                    bot_reply=suggested_reply,
                    ttft_ms=latency_ms,
                    total_latency_ms=latency_ms,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    raw_response=raw_content,
                    metadata={
                        "prompt_hash": self._parser_prompt_hash,
                        "model_id": self._model,
                        "retries": retries,
                    },
                )
            except (json.JSONDecodeError, ValidationError) as e:
                logger.info("Intent validation error on attempt %d: %s", retries, e)
                error_feedback = f"Schema validation error: {str(e)[:200]}"
                retries += 1

        # Safe fallback after bounded retry exhaustion
        fallback = UnknownIntent(raw_text=transcript, reason="parse_validation_failed")
        return IntentResult(
            intents=[fallback.model_dump()],
            bot_reply="Mohon maaf kak, bisa diulangi kembali?",
            ttft_ms=latency_ms,
            total_latency_ms=latency_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            raw_response="{}",
            metadata={
                "prompt_hash": self._parser_prompt_hash,
                "model_id": self._model,
                "retries": retries,
                "fallback": True,
            },
        )

    async def verbalize_reply(
        self,
        speech_facts: dict[str, Any],
        cart_snapshot: dict[str, Any],
    ) -> tuple[str, float, int, int]:
        """Verbalize speech facts into conversational Indonesian using LLM (Mode 1).

        Returns:
            tuple of (reply_text, latency_ms, tokens_in, tokens_out)
        """
        payload = {
            "speech_facts": speech_facts,
            "cart": cart_snapshot,
        }
        messages = [
            {"role": "system", "content": self._reply_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 150,
        }

        session = await self._get_session()
        req_start = time.perf_counter()
        try:
            async with session.post(
                self._chat_url,
                headers=headers,
                json=body,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                    latency_ms = (time.perf_counter() - req_start) * 1000.0
                    if resp.status != 200:
                        return "Baik kak, pesanan sudah dicatat.", latency_ms, 0, 0
                    data = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as net_err:
            latency_ms = (time.perf_counter() - req_start) * 1000.0
            logger.warning("Groq verbalize network error: %s", net_err)
            return "Baik kak, pesanan dicatat.", latency_ms, 0, 0

        usage = data.get("usage", {})
        reply_text = data["choices"][0]["message"]["content"].strip()
        return reply_text, latency_ms, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
