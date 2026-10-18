"""Adapters package providing provider abstractions and test fakes for STT, TTS, and LLM."""

from lajur_agent.adapters.base import (
    IntentResult,
    LLMIntentAdapter,
    STTAdapter,
    TranscriptionEvent,
    TTSAdapter,
    TTSAudioChunk,
)
from lajur_agent.adapters.fakes import (
    FakeLLMIntentAdapter,
    FakeSTTAdapter,
    FakeTTSAdapter,
)

__all__ = [
    "TranscriptionEvent",
    "STTAdapter",
    "TTSAudioChunk",
    "TTSAdapter",
    "IntentResult",
    "LLMIntentAdapter",
    "FakeSTTAdapter",
    "FakeTTSAdapter",
    "FakeLLMIntentAdapter",
]
