"""Base async adapter interfaces for speech recognition, text-to-speech, and intent parsing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TranscriptionEvent:
    """Represents a speech-to-text recognition event (streaming or final)."""

    text: str
    is_final: bool = False
    confidence: float = 1.0
    latency_ms: float = 0.0


class STTAdapter(ABC):
    """Abstract interface for streaming-capable Speech-to-Text adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Vendor/adapter identifier."""
        ...

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        sample_rate: int = 16000,
    ) -> AsyncIterator[TranscriptionEvent]:
        """Stream raw audio chunks (PCM 16-bit mono) and yield transcription events."""
        ...

    @abstractmethod
    async def transcribe_file(self, file_path: Path | str) -> str:
        """Transcribe an entire audio file into final text."""
        ...


@dataclass(frozen=True)
class TTSAudioChunk:
    """Represents a synthesized PCM audio chunk."""

    audio_bytes: bytes
    sample_rate: int = 16000
    is_final: bool = False


class TTSAdapter(ABC):
    """Abstract interface for streaming-capable Text-to-Speech adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Vendor/adapter identifier."""
        ...

    @abstractmethod
    async def synthesize_stream(
        self,
        text_stream: AsyncIterator[str],
    ) -> AsyncIterator[TTSAudioChunk]:
        """Synthesize a stream of text chunks into streaming audio chunks."""
        ...

    @abstractmethod
    async def synthesize_text(self, text: str) -> bytes:
        """Synthesize an entire string into raw WAV or PCM bytes."""
        ...


@dataclass(frozen=True)
class IntentResult:
    """Represents the structured intent output from an LLM dialog turn."""

    intents: list[dict[str, Any]]
    bot_reply: str
    ttft_ms: float = 0.0
    total_latency_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    raw_response: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMIntentAdapter(ABC):
    """Abstract interface for LLM intent parsing adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Vendor/adapter identifier."""
        ...

    async def verbalize_reply(
        self,
        speech_facts: dict[str, Any],
        cart_snapshot: dict[str, Any],
    ) -> tuple[str, float, int, int]:
        """Verbalize speech facts into conversational reply (reply_text, latency_ms, tokens_in, tokens_out)."""
        return "", 0.0, 0, 0

    @abstractmethod
    async def parse_intent(
        self,
        transcript: str,
        history: list[dict[str, str]] | None = None,
        cart_snapshot: dict[str, Any] | None = None,
        pending_choice: dict[str, Any] | None = None,
        menu_context: dict[str, Any] | None = None,
    ) -> IntentResult:
        """Parse an utterance into structured intents according to intent-parser-contract."""
        ...
