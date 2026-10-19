"""Interactive real microphone test tool for Lajur.

Captures speech directly from your physical microphone, transcribes via Groq and Deepgram,
extracts drive-thru intents via Gemini, and speaks back via Edge-TTS through your speakers.
"""

from __future__ import annotations

import asyncio
import io
import sys
import time
import wave
from pathlib import Path
from typing import Any

import av
import numpy as np
import sounddevice as sd
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


def decode_mp3_to_pcm(mp3_bytes: bytes, target_sr: int = 24000) -> np.ndarray:
    """Decode MP3 bytes into a 1D int16 NumPy array for playback."""
    container: Any = av.open(io.BytesIO(mp3_bytes), format="mp3")
    resampler = av.AudioResampler(format="s16", layout="mono", rate=target_sr)
    all_samples: list[np.ndarray] = []
    for frame in container.decode(audio=0):
        for rf in resampler.resample(frame):
            all_samples.append(rf.to_ndarray())
    if all_samples:
        return np.concatenate(all_samples, axis=1).squeeze()
    return np.zeros((0,), dtype=np.int16)


def record_audio_interactive(sample_rate: int = 16000) -> np.ndarray:
    """Record mono audio from mic interactively (Enter to start, Enter to stop)."""
    input("\nTekan [ENTER] untuk mulai merekam suara Anda...")

    frames: list[np.ndarray] = []

    def callback(indata: np.ndarray, frame_count: int, time_info: Any, status: Any) -> None:
        frames.append(indata.copy())

    stream = sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
        blocksize=1024,
        callback=callback,
    )

    t0 = time.perf_counter()
    with stream:
        input("  [● MEREKAM] Sedang mendengarkan... Tekan [ENTER] jika sudah selesai bicara: ")
    dur_s = time.perf_counter() - t0

    if not frames:
        return np.zeros((0, 1), dtype=np.int16)

    audio_data = np.concatenate(frames, axis=0)
    print(f"  [✓ SELESAI] Rekaman terekam: {dur_s:.1f} detik ({len(audio_data)} sampel).")
    return audio_data


def save_pcm_to_wav(pcm_data: np.ndarray, output_path: Path, sample_rate: int = 16000) -> None:
    """Save int16 NumPy array to standard PCM 16-bit mono WAV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data.tobytes())


async def run_turn(audio_path: Path) -> None:
    groq = GroqSTTAdapter()
    deepgram = DeepgramSTTAdapter()
    gemini = GeminiLLMAdapter()
    tts = EdgeTTSAdapter(voice="id-ID-GadisNeural")

    print("\n" + "-" * 70)
    print("1. MEMPROSES SPEECH-TO-TEXT (STT):")
    print("-" * 70)

    # 1. Transcribe with Groq
    t0 = time.perf_counter()
    groq_text = await groq.transcribe_file(audio_path)
    groq_ms = (time.perf_counter() - t0) * 1000.0
    print(f"  • Groq Whisper Turbo : \"{groq_text}\" ({groq_ms:.0f} ms)")

    # 2. Transcribe with Deepgram
    t0 = time.perf_counter()
    dg_text = await deepgram.transcribe_file(audio_path)
    dg_ms = (time.perf_counter() - t0) * 1000.0
    print(f"  • Deepgram Nova-2    : \"{dg_text}\" ({dg_ms:.0f} ms)")

    user_transcript = groq_text or dg_text
    if not user_transcript.strip():
        print("\n[!] Tidak ada kata-kata yang terdeteksi dari mic. Pastikan volume mic tidak mute.")
        return

    # 3. Process LLM Dialog
    print("\n" + "-" * 70)
    print("2. MEMPROSES INTENT & BALASAN KASIR (GEMINI LLM):")
    print("-" * 70)
    t0 = time.perf_counter()
    llm_res = await gemini.parse_intent(user_transcript)
    llm_ms = (time.perf_counter() - t0) * 1000.0

    print(f"  • Intent Terdeteksi : {llm_res.intents}")
    print(f"  • Respon Kasir AI   : \"{llm_res.bot_reply}\" ({llm_ms:.0f} ms)")

    # 4. Synthesize and Play Voice Reply
    print("\n" + "-" * 70)
    print("3. MEMUTAR SUARA KASIR (TTS GADIS NEURAL):")
    print("-" * 70)
    t0 = time.perf_counter()
    mp3_bytes = await tts.synthesize_text(llm_res.bot_reply)
    tts_ms = (time.perf_counter() - t0) * 1000.0
    print(f"  • Sintesis Suara Selesai ({tts_ms:.0f} ms). Memutar ke speaker Anda...")

    pcm_playback = decode_mp3_to_pcm(mp3_bytes, target_sr=24000)
    if len(pcm_playback) > 0:
        sd.play(pcm_playback, samplerate=24000)
        sd.wait()
    print("  • Suara kasir selesai diputar.")

    total_pipeline_ms = groq_ms + llm_ms + tts_ms
    print(f"\n[TOTAL TURN-AROUND LATENCY]: {total_pipeline_ms:.0f} ms (~{total_pipeline_ms / 1000.0:.2f} detik)")


def main() -> None:
    print("=" * 70)
    print("  LAJUR -- UJI COBA SUARA MIC LANGSUNG (Groq + Deepgram + Gemini + Edge-TTS)")
    print("=" * 70)
    print("Mikrofon Default: Terdeteksi siap merekam.")
    print("Speaker Default : Terdeteksi siap memutar suara kasir.")
    print("Biaya Operasional: $0.00 (100% Gratis).")

    temp_wav = Path("eval/audio/real/user_mic_test.wav")

    while True:
        audio_pcm = record_audio_interactive(sample_rate=16000)
        if len(audio_pcm) == 0:
            print("Tidak ada audio yang terekam.")
            continue

        max_amp = int(np.abs(audio_pcm).max())
        if max_amp < 150:
            print(f"\n[PERINGATAN] Volume suara sangat kecil (Amplitudo maks: {max_amp}). Pastikan mic tidak termute.")

        save_pcm_to_wav(audio_pcm, temp_wav, sample_rate=16000)
        asyncio.run(run_turn(temp_wav))

        print("\n" + "=" * 70)
        try:
            choice = input("Mau coba bicara kalimat lain lagi? ([Y]/n): ").strip().lower()
            if choice == "n":
                print("Uji coba mic selesai.")
                break
        except (KeyboardInterrupt, EOFError):
            print("\nUji coba selesai.")
            break


if __name__ == "__main__":
    main()
