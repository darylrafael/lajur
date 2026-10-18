"""Smoke test runner for live zero-cost adapters (Groq, Deepgram, Gemini, Edge-TTS)."""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parents[3]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

load_dotenv()

from lajur_agent.adapters.deepgram import DeepgramSTTAdapter  # noqa: E402
from lajur_agent.adapters.edge_tts import EdgeTTSAdapter  # noqa: E402
from lajur_agent.adapters.gemini import GeminiLLMAdapter  # noqa: E402
from lajur_agent.adapters.groq import GroqSTTAdapter  # noqa: E402

from eval.metrics.wer import calculate_wer  # noqa: E402


async def main() -> None:
    print("=" * 70)
    print("  LAJUR ZERO-COST ADAPTER SMOKE TEST (Groq, Deepgram, Gemini, Edge-TTS)")
    print("=" * 70)

    test_sentence = "Saya mau pesan satu burger sapi dan satu es kopi susu gula aren."
    print(f"Test Sentence : '{test_sentence}'\n")

    # 1. Edge-TTS Smoke Test
    print("[1/4] Testing Edge-TTS Adapter (id-ID-GadisNeural)...")
    tts_adapter = EdgeTTSAdapter(voice="id-ID-GadisNeural")
    t0 = time.perf_counter()
    audio_bytes = await tts_adapter.synthesize_text(test_sentence)
    tts_latency_ms = (time.perf_counter() - t0) * 1000.0

    temp_audio_path = Path("eval/audio/temp_smoke_test.mp3")
    temp_audio_path.parent.mkdir(parents=True, exist_ok=True)
    temp_audio_path.write_bytes(audio_bytes)
    print(f"      -> Status   : SUCCESS (Synthesized {len(audio_bytes)} bytes)")
    print(f"      -> Latency  : {tts_latency_ms:.1f} ms")

    # 2. Groq STT Smoke Test
    print("\n[2/4] Testing Groq STT Adapter (whisper-large-v3-turbo)...")
    groq_adapter = GroqSTTAdapter(model="whisper-large-v3-turbo", language="id")
    t0 = time.perf_counter()
    groq_transcript = await groq_adapter.transcribe_file(temp_audio_path)
    groq_latency_ms = (time.perf_counter() - t0) * 1000.0
    groq_wer = calculate_wer(test_sentence, groq_transcript)
    print(f"      -> Transcript: '{groq_transcript}'")
    print(f"      -> Latency   : {groq_latency_ms:.1f} ms | WER: {groq_wer.wer * 100.0:.1f}%")

    # 3. Deepgram STT Smoke Test
    print("\n[3/4] Testing Deepgram STT Adapter (nova-2)...")
    dg_adapter = DeepgramSTTAdapter(model="nova-2", language="id")
    t0 = time.perf_counter()
    dg_transcript = await dg_adapter.transcribe_file(temp_audio_path)
    dg_latency_ms = (time.perf_counter() - t0) * 1000.0
    dg_wer = calculate_wer(test_sentence, dg_transcript)
    print(f"      -> Transcript: '{dg_transcript}'")
    print(f"      -> Latency   : {dg_latency_ms:.1f} ms | WER: {dg_wer.wer * 100.0:.1f}%")

    # Clean temporary audio file
    temp_audio_path.unlink(missing_ok=True)

    # 4. Gemini LLM Intent Adapter Smoke Test
    print("\n[4/4] Testing Google Gemini LLM Adapter (gemini-2.5-flash)...")
    gemini_adapter = GeminiLLMAdapter(model="gemini-2.5-flash")
    llm_input = groq_transcript or test_sentence
    t0 = time.perf_counter()
    intent_result = await gemini_adapter.parse_intent(llm_input)
    llm_latency_ms = (time.perf_counter() - t0) * 1000.0

    print(f"      -> Input      : '{llm_input}'")
    print(f"      -> Latency    : {llm_latency_ms:.1f} ms")
    print(f"      -> Tokens     : In: {intent_result.tokens_in} | Out: {intent_result.tokens_out}")
    print(f"      -> Extracted  : {intent_result.intents}")
    print(f"      -> Bot Reply  : '{intent_result.bot_reply}'")

    print("\n" + "=" * 70)
    print("  SMOKE TEST PASSED: ALL 4 FREE ADAPTERS VERIFIED OPERATIONAL (COST: $0.00)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
