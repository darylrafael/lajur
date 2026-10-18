"""Adapters package providing provider abstractions, live clients, and test fakes for STT, TTS, and LLM."""

from lajur_agent.adapters.base import (
    IntentResult,
    LLMIntentAdapter,
    STTAdapter,
    TranscriptionEvent,
    TTSAdapter,
    TTSAudioChunk,
)
from lajur_agent.adapters.deepgram import DeepgramSTTAdapter
from lajur_agent.adapters.edge_tts import EdgeTTSAdapter
from lajur_agent.adapters.fakes import (
    FakeLLMIntentAdapter,
    FakeSTTAdapter,
    FakeTTSAdapter,
)
from lajur_agent.adapters.gemini import GeminiLLMAdapter
from lajur_agent.adapters.groq import GroqSTTAdapter

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
    "DeepgramSTTAdapter",
    "GroqSTTAdapter",
    "GeminiLLMAdapter",
    "EdgeTTSAdapter",
]
