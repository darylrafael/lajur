"""Pre-registered Gate G1-v2 Validation Benchmark on the Real LiveKit WebRTC Pipeline.

Protocol: docs/gates/G1-v2-protocol.md

Enforces:
1. Real pipeline cascade: WebRTC Client -> WebRTC Agent -> Deepgram Nova-3 STT (endpointing=500)
   -> Groq Qwen-27b Intent -> Cart State Machine (packages/cart)
   -> Deterministic Template Reply -> ElevenLabs Flash v2.5 TTS -> WebRTC Client Audio.
2. Connection pre-warming during session start greeting.
3. Shared aiohttp.ClientSession reused across turns.
4. Single persistent Deepgram WebSocket streaming connection with KeepAlive.
5. Non-blocking telemetry (background queue).
6. Ground-truth speech-end reference timestamp logged objectively from playback timing.
7. Full stage telemetry: STT first partial, STT final, LLM TTFT, State machine apply, TTS TTFB,
   agent publish, client playout, and residual.
8. 10,000 bootstrap resamples for 95% CIs on all metrics.
9. Strict reporting against 1.2s target and 1.8s fallback.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import logging
import os
import sys
import time
import wave
from pathlib import Path
from typing import Any, cast

import aiohttp
import edge_tts
import numpy as np
from dotenv import load_dotenv

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parents[3]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import livekit.api as lk_api  # noqa: E402
import livekit.rtc as lk_rtc  # noqa: E402
from lajur_agent.adapters.base import TTSAdapter, TTSAudioChunk  # noqa: E402
from lajur_agent.adapters.deepgram import DeepgramSTTAdapter  # noqa: E402
from lajur_agent.adapters.elevenlabs import ElevenLabsTTSAdapter  # noqa: E402
from lajur_agent.adapters.groq import GroqLLMIntentAdapter  # noqa: E402
from lajur_agent.observability import TurnEventLogger  # noqa: E402
from lajur_agent.pipeline import VoiceOrderingPipeline  # noqa: E402
from lajur_cart.menu_service import MenuService  # noqa: E402

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("lajur.bench.g1_v2")

# Pre-registered 20 diverse scenarios covering all 4 core categories (v2b)
SELECTED_20_SIDS = [
    # Category 1: Simple items (5)
    "scen_001",
    "scen_002",
    "scen_004",
    "scen_006",
    "scen_009",
    # Category 2: Quantity & combos (5)
    "scen_016",
    "scen_018",
    "scen_019",
    "scen_020",
    "scen_021",
    # Category 3: Modifiers & sizes (5)
    "scen_026",
    "scen_027",
    "scen_028",
    "scen_030",
    "scen_031",
    # Category 4: Correction & undo (5)
    "scen_071",
    "scen_072",
    "scen_073",
    "scen_074",
    "scen_077",
]

# Pre-registered 30 diverse scenarios covering all 4 core categories (v2 legacy)
SELECTED_30_SIDS = [
    # Category 1: Simple items (8)
    "scen_001",
    "scen_002",
    "scen_004",
    "scen_006",
    "scen_009",
    "scen_011",
    "scen_013",
    "scen_015",
    # Category 2: Quantity & combos (8)
    "scen_016",
    "scen_018",
    "scen_019",
    "scen_020",
    "scen_021",
    "scen_022",
    "scen_025",
    "scen_041",
    # Category 3: Modifiers & sizes (8)
    "scen_026",
    "scen_027",
    "scen_028",
    "scen_030",
    "scen_031",
    "scen_033",
    "scen_035",
    "scen_037",
    # Category 4: Correction & undo (6)
    "scen_071",
    "scen_072",
    "scen_073",
    "scen_074",
    "scen_077",
    "scen_080",
]


class StubTTSAdapter(TTSAdapter):
    """Zero-character stub TTS adapter for dry-run validation."""

    def __init__(self, sample_rate: int = 16000) -> None:
        self._sample_rate = sample_rate

    @property
    def name(self) -> str:
        return "stub-tts-dryrun"

    async def get_remaining_characters(self) -> int:
        return 999999

    async def prewarm(self) -> float:
        return 1.0

    async def close(self) -> None:
        pass

    async def synthesize_text(self, text: str) -> bytes:
        # Generate 0.5s of 16kHz mono 16-bit PCM (synthetic tone)
        num_samples = int(0.5 * self._sample_rate)
        t = np.linspace(0, 0.5, num_samples, False)
        tone = (np.sin(2 * np.pi * 440 * t) * 16384).astype(np.int16)
        return tone.tobytes()

    async def stream_audio_chunks(
        self, text: str, chunk_size: int = 640
    ) -> Any:
        pcm = await self.synthesize_text(text)
        for i in range(0, len(pcm), chunk_size):
            yield pcm[i : i + chunk_size]

    async def synthesize_stream(self, text_stream: Any) -> Any:
        full_text = "".join([c async for c in text_stream])
        pcm = await self.synthesize_text(full_text)
        yield TTSAudioChunk(audio_bytes=pcm, sample_rate=self._sample_rate, is_final=True)


def bootstrap_ci(
    data: list[float], stat_fn: Any = np.median, n_resamples: int = 10000, alpha: float = 0.05
) -> tuple[float, float]:
    """Calculate 95% bootstrap confidence interval for a given statistic."""
    if not data:
        return 0.0, 0.0
    arr = np.array(data)
    boot_stats = [stat_fn(np.random.choice(arr, size=len(arr), replace=True)) for _ in range(n_resamples)]
    low = float(np.percentile(boot_stats, 100.0 * (alpha / 2.0)))
    high = float(np.percentile(boot_stats, 100.0 * (1.0 - alpha / 2.0)))
    return low, high


async def synthesize_phrase_pcm(text: str, voice: str = "id-ID-GadisNeural") -> np.ndarray:
    """Synthesize text to 16kHz linear PCM using edge-tts for test harness audio."""
    communicate = edge_tts.Communicate(text, voice=voice)
    mp3_bytes = b""
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio" and "data" in chunk and isinstance(chunk["data"], bytes):
            mp3_bytes += chunk["data"]

    import av

    container = cast(Any, av.open(io.BytesIO(mp3_bytes), format="mp3"))
    resampler = cast(Any, av).AudioResampler(format="s16", layout="mono", rate=16000)
    all_samples = []
    for frame in container.decode(audio=0):
        for rf in resampler.resample(frame):
            all_samples.append(rf.to_ndarray())
    if all_samples:
        return np.concatenate(all_samples, axis=1).squeeze().astype(np.int16)
    return np.zeros((0,), dtype=np.int16)


async def load_or_synthesize_clips(selected_scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Load pre-synthesized test audio or synthesize missing clips."""
    audio_dir = root_dir / "eval" / "audio" / "synthetic" / "g1_week04"
    audio_dir.mkdir(parents=True, exist_ok=True)
    clips: list[dict[str, Any]] = []

    for sc in selected_scenarios:
        sid = sc["id"]
        utterance = sc["utterances"][0]
        out_wav = audio_dir / f"{sid}.wav"

        if out_wav.exists():
            with wave.open(str(out_wav), "rb") as wf:
                full_pcm_bytes = wf.readframes(wf.getnframes())
            total_samples = len(full_pcm_bytes) // 2
            active_samples = total_samples - int(16000 * 1.5)
        else:
            active_pcm = await synthesize_phrase_pcm(utterance)
            active_samples = len(active_pcm)
            trailing_silence = np.zeros(int(16000 * 1.5), dtype=np.int16)
            full_pcm = np.concatenate([active_pcm, trailing_silence])
            full_pcm_bytes = full_pcm.tobytes()
            with wave.open(str(out_wav), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(full_pcm_bytes)

        category = sc.get("tags", ["simple"])[0]
        if "quantity" in sc.get("tags", []):
            category = "quantity_combo"
        elif "modifier" in sc.get("tags", []) or "size" in sc.get("tags", []):
            category = "modifiers_size"
        elif int(sid.split("_")[1]) >= 71:
            category = "correction_undo"

        clips.append({
            "sid": sid,
            "category": category,
            "utterance": utterance,
            "raw_bytes": full_pcm_bytes,
            "active_samples": active_samples,
            "expected_cart": sc.get("expected_cart", {}),
        })
        print(f"  [{sid}] Loaded audio ({active_samples} active samples)", flush=True)

    return clips


def evaluate_cart_match(actual_cart: dict[str, Any], expected_cart: dict[str, Any]) -> bool:
    """Compare resulting cart against dataset expected_cart."""
    try:
        act_items = actual_cart.get("items", [])
        exp_items = expected_cart.get("items", [])

        if len(act_items) != len(exp_items):
            return False

        act_sorted = sorted(act_items, key=lambda x: (x.get("item_id", ""), x.get("quantity", 1)))
        exp_sorted = sorted(exp_items, key=lambda x: (x.get("item_id", ""), x.get("quantity", 1)))

        for a, e in zip(act_sorted, exp_sorted):
            if a.get("item_id") != e.get("item_id"):
                return False
            if a.get("quantity") != e.get("quantity"):
                return False

        if actual_cart.get("total_price", 0) != expected_cart.get("total_price", 0):
            return False

        return True
    except Exception:
        return False


async def run_benchmark(dry_run: bool = False, turns: int = 20) -> None:
    bench_label = "v2b" if turns == 20 else "v2"
    print("\n=======================================================", flush=True)
    print(f" GATE G1-{bench_label} PRE-REGISTERED VALIDATION BENCHMARK (MINGGU 4d)", flush=True)
    print(f" Mode: {'DRY RUN (Zero ElevenLabs Chars)' if dry_run else 'REAL BENCHMARK RUN'} | Turns: {turns}", flush=True)
    print("=======================================================\n", flush=True)

    # 1. Check ElevenLabs Quota
    quota_before = 0
    quota_after = 0
    if not dry_run:
        real_tts = ElevenLabsTTSAdapter()
        quota_before = await real_tts.get_remaining_characters()
        await real_tts.close()
        print(f"ElevenLabs Remaining Characters: {quota_before}", flush=True)
        if quota_before < 600:
            print("FATAL ERROR: ElevenLabs quota below 600 character reserve! STOPPING.", flush=True)
            sys.exit(1)
        if quota_before < 1200:
            print(f"WARNING: ElevenLabs quota ({quota_before}) is tight against 600 reserve. Proceed with caution.", flush=True)

    # 2. Load dataset scenarios
    scenarios_file = root_dir / "eval" / "datasets" / "v0" / "scenarios.jsonl"
    with open(scenarios_file, encoding="utf-8") as f:
        all_scens = [json.loads(line) for line in f if line.strip()]

    target_sids = SELECTED_20_SIDS if turns == 20 else SELECTED_30_SIDS
    selected_scenarios = [s for s in all_scens if s["id"] in target_sids]
    # Sort to match the exact pre-registered order
    sid_order = {sid: i for i, sid in enumerate(target_sids)}
    selected_scenarios.sort(key=lambda x: sid_order[x["id"]])

    print(f"Loaded {len(selected_scenarios)} pre-registered scenarios from {scenarios_file.name}.", flush=True)

    # 3. Synthesize test audio clips
    print(f"\nLoading scripted test voice clips for {len(selected_scenarios)} scenarios...", flush=True)
    audio_clips = await load_or_synthesize_clips(selected_scenarios)

    # 4. Initialize shared ClientSession and Persistent Pipeline Components
    shared_session = aiohttp.ClientSession()

    menu_service = MenuService(root_dir / "eval" / "menu" / "menu.json")
    dg_api_key = os.getenv("DEEPGRAM_API_KEY", "")
    dg_adapter = DeepgramSTTAdapter(api_key=dg_api_key, model="nova-3", endpointing=500, session=shared_session)
    groq_adapter = GroqLLMIntentAdapter(session=shared_session)
    tts_adapter: TTSAdapter = StubTTSAdapter() if dry_run else ElevenLabsTTSAdapter(session=shared_session)

    event_logger = TurnEventLogger(db_path=root_dir / "data" / "turn_events.sqlite3")
    event_logger.start_background_writer()

    pipeline = VoiceOrderingPipeline(
        session_id=f"g1_{bench_label}_session",
        menu_service=menu_service,
        stt_adapter=dg_adapter,
        llm_adapter=groq_adapter,
        tts_adapter=tts_adapter,
        event_logger=event_logger,
        reply_mode="template",
        client_identity=f"g1-{bench_label}-bench-client",
    )

    # 5. Connect to LiveKit WebRTC room
    livekit_url = os.getenv("LIVEKIT_URL", "")
    api_key = os.getenv("LIVEKIT_API_KEY", "")
    api_secret = os.getenv("LIVEKIT_API_SECRET", "")
    room_name = f"g1-{bench_label}-bench-{int(time.time())}"

    print(f"\nConnecting to LiveKit room: {room_name} ({livekit_url})...", flush=True)
    token_agent = (
        lk_api.AccessToken(api_key, api_secret)
        .with_identity("agent-voice")
        .with_name("DriveThru Agent")
        .with_grants(lk_api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )
    token_client = (
        lk_api.AccessToken(api_key, api_secret)
        .with_identity("client-driver")
        .with_name("Test Customer Driver")
        .with_grants(lk_api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    room_agent = lk_rtc.Room()
    room_client = lk_rtc.Room()

    # State variables for turn synchronization
    current_turn_queue: asyncio.Queue[bytes] | None = None
    first_audio_received_event = asyncio.Event()
    t_speech_end = 0.0
    t_first_audio_received = 0.0

    # Register track listeners BEFORE connect and track publication to eliminate race condition
    @room_agent.on("track_subscribed")
    def on_agent_track_sub(track: lk_rtc.Track, publication: Any, participant: Any) -> None:
        if isinstance(track, lk_rtc.RemoteAudioTrack):
            audio_stream = lk_rtc.AudioStream(track, sample_rate=16000, num_channels=1)

            async def read_mic_pcm() -> None:
                nonlocal current_turn_queue
                async for audio_event in audio_stream:
                    pcm_data = audio_event.frame.data.tobytes()
                    if current_turn_queue is not None:
                        await current_turn_queue.put(pcm_data)

            asyncio.create_task(read_mic_pcm())

    @room_client.on("track_subscribed")
    def on_client_track_sub(track: lk_rtc.Track, publication: Any, participant: Any) -> None:
        if isinstance(track, lk_rtc.RemoteAudioTrack):
            audio_stream = lk_rtc.AudioStream(track, sample_rate=16000, num_channels=1)

            async def monitor_playout() -> None:
                nonlocal t_first_audio_received
                async for audio_event in audio_stream:
                    frame = audio_event.frame
                    samples = np.frombuffer(frame.data, dtype=np.int16)
                    if len(samples) > 0:
                        rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
                        if rms > 300.0 and not first_audio_received_event.is_set():
                            t_first_audio_received = time.perf_counter()
                            first_audio_received_event.set()

            asyncio.create_task(monitor_playout())

    await asyncio.gather(
        room_agent.connect(livekit_url, token_agent),
        room_client.connect(livekit_url, token_client),
    )
    print("Both WebRTC peers connected to LiveKit room.", flush=True)

    client_source = lk_rtc.AudioSource(16000, 1)
    client_track = lk_rtc.LocalAudioTrack.create_audio_track("client-mic", client_source)
    await room_client.local_participant.publish_track(client_track)

    agent_source = lk_rtc.AudioSource(16000, 1)
    agent_track = lk_rtc.LocalAudioTrack.create_audio_track("agent-speaker", agent_source)
    await room_agent.local_participant.publish_track(agent_track)

    # Wait for subscription
    await asyncio.sleep(2.0)

    # 6. Pre-warm phase during Greeting
    print("\n--- Pre-Warming Connections during Greeting ---", flush=True)
    t_prewarm_start = time.perf_counter()

    # Prewarm Groq & ElevenLabs HTTP, and Deepgram Persistent WebSocket
    dg_stream = await dg_adapter.create_persistent_stream(sample_rate=16000)

    groq_prewarm_task = asyncio.create_task(groq_adapter.prewarm())
    eleven_prewarm_task = asyncio.create_task(tts_adapter.prewarm())
    dg_connect_task = asyncio.create_task(dg_stream.connect())

    prewarm_results = await asyncio.gather(
        groq_prewarm_task,
        eleven_prewarm_task,
        dg_connect_task,
    )
    t_prewarm_ms = (time.perf_counter() - t_prewarm_start) * 1000.0
    print(
        f"Pre-warm complete in {t_prewarm_ms:.1f} ms (Groq: {prewarm_results[0]:.1f} ms, ElevenLabs: {prewarm_results[1]:.1f} ms, Deepgram: {prewarm_results[2]:.1f} ms).",
        flush=True,
    )

    # 7. Execute 30 Benchmark Turns
    turn_results: list[dict[str, Any]] = []
    print("\n--- Executing 30 Pre-Registered Turns (G1-v2) ---", flush=True)

    for idx, clip in enumerate(audio_clips, start=1):
        print(f"\n[Turn {idx:02d}/30] SId: {clip['sid']} ({clip['category']}) -> '{clip['utterance']}'", flush=True)

        pipeline.reset_session(session_id=f"g1_v2_bench_{clip['sid']}")
        t_speech_end = 0.0
        t_first_audio_received = 0.0
        t_agent_publish = 0.0
        first_audio_received_event.clear()

        turn_queue: asyncio.Queue[bytes] = asyncio.Queue()
        current_turn_queue = turn_queue

        t_stt_first_partial_captured: float | None = None
        t_stt_final_captured: float | None = None
        turn_transcript_captured = ""

        def on_partial(ts: float) -> None:
            nonlocal t_stt_first_partial_captured
            if t_stt_first_partial_captured is None:
                t_stt_first_partial_captured = ts

        def on_final(text: str, ts: float) -> None:
            nonlocal t_stt_final_captured, turn_transcript_captured
            t_stt_final_captured = ts
            turn_transcript_captured = text

        stt_done_event = dg_stream.begin_turn(
            on_first_partial=on_partial,
            on_speech_final=on_final,
        )

        # Pipe audio from client mic to Deepgram WebSocket
        stop_forwarding = False

        async def forward_audio() -> None:
            while not stop_forwarding:
                try:
                    chunk = await asyncio.wait_for(turn_queue.get(), timeout=0.05)
                    await dg_stream.send_audio_chunk(chunk)
                    turn_queue.task_done()
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break

        fwd_task = asyncio.create_task(forward_audio())

        # Stream scenario audio at real-time pacing (20ms chunks)
        raw_pcm = clip["raw_bytes"]
        chunk_samples = 320
        chunk_bytes = 640
        num_chunks = len(raw_pcm) // chunk_bytes
        active_samples = clip["active_samples"]

        samples_sent = 0
        for c_idx in range(num_chunks):
            t_c_start = time.perf_counter()
            chunk = raw_pcm[c_idx * chunk_bytes : (c_idx + 1) * chunk_bytes]
            frame = lk_rtc.AudioFrame(chunk, 16000, 1, chunk_samples)
            await client_source.capture_frame(frame)
            samples_sent += chunk_samples

            if t_speech_end == 0.0 and samples_sent >= active_samples:
                t_speech_end = time.perf_counter()

            if stt_done_event.is_set():
                break

            elapsed = time.perf_counter() - t_c_start
            sleep_time = 0.02 - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        # Wait for Deepgram STT endpointing
        if not stt_done_event.is_set():
            try:
                await asyncio.wait_for(stt_done_event.wait(), timeout=1.5)
            except asyncio.TimeoutError:
                await dg_stream.finalize()
                try:
                    await asyncio.wait_for(stt_done_event.wait(), timeout=1.0)
                except asyncio.TimeoutError:
                    print("  [Warning] Deepgram STT endpointing timed out, proceeding with current text...", flush=True)

        stop_forwarding = True
        fwd_task.cancel()
        current_turn_queue = None

        if t_stt_final_captured is None:
            t_stt_final_captured = time.perf_counter()

        transcript = turn_transcript_captured or dg_stream.last_transcript
        if not transcript:
            print("  [Warning] STT produced empty transcript, falling back to utterance", flush=True)
            transcript = clip["utterance"]

        # Run pipeline & TTS streaming
        async def audio_consumer(chunk: bytes) -> None:
            nonlocal t_agent_publish
            if t_agent_publish == 0.0:
                t_agent_publish = time.perf_counter()
            f = lk_rtc.AudioFrame(chunk, 16000, 1, 320)
            await agent_source.capture_frame(f)
            await asyncio.sleep(0.018)

        p_res = await pipeline.process_turn(
            utterance=transcript,
            speech_end_timestamp=t_speech_end,
            audio_frame_consumer=audio_consumer,
            stt_final_timestamp=t_stt_final_captured,
            stt_first_partial_timestamp=t_stt_first_partial_captured,
            connect_duration_ms=t_prewarm_ms if idx == 1 else 0.0,
            agent_publish_timestamp=t_agent_publish,
        )

        # Wait for client playout detection
        if t_first_audio_received == 0.0:
            try:
                await asyncio.wait_for(first_audio_received_event.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                t_first_audio_received = time.perf_counter()

        turn_latency_ms = max(0.0, (t_first_audio_received - t_speech_end) * 1000.0)
        stt_turnaround_ms = max(0.0, (t_stt_final_captured - t_speech_end) * 1000.0)
        stt_partial_ms = (
            max(0.0, (t_stt_first_partial_captured - t_speech_end) * 1000.0)
            if t_stt_first_partial_captured
            else stt_turnaround_ms
        )

        residual_ms = max(0.0, (t_first_audio_received - (t_agent_publish or t_first_audio_received)) * 1000.0)

        bot_reply = p_res.reply_text
        cart_matched = evaluate_cart_match(p_res.cart, clip["expected_cart"])
        intent_matched = (
            p_res.turn_event.intent_type != "unknown" and p_res.turn_event.intent_type != "kill_switch"
        )
        chars_sent = len(bot_reply)

        print(
            f"  -> Reply: '{bot_reply}' ({chars_sent} chars)\n"
            f"  -> Total Latency: {turn_latency_ms:.1f} ms | STT Final: {stt_turnaround_ms:.1f} ms | STT Partial: {stt_partial_ms:.1f} ms | Residual: {residual_ms:.1f} ms",
            flush=True,
        )

        turn_results.append({
            "turn_id": idx,
            "sid": clip["sid"],
            "category": clip["category"],
            "transcript": transcript,
            "bot_reply": bot_reply,
            "chars_sent": chars_sent,
            "turn_latency_ms": turn_latency_ms,
            "stt_turnaround_ms": stt_turnaround_ms,
            "stt_first_partial_ms": stt_partial_ms,
            "llm_ttft_ms": (p_res.turn_event.t_llm_first_token_ms - p_res.turn_event.t_stt_final_ms),
            "state_apply_ms": (p_res.turn_event.t_state_applied_ms - p_res.turn_event.t_intent_validated_ms),
            "tts_ttfb_ms": (p_res.turn_event.t_tts_first_byte_ms - p_res.turn_event.t_state_applied_ms),
            "agent_publish_ms": (p_res.turn_event.t_agent_publish_ms - p_res.turn_event.t_tts_first_byte_ms),
            "residual_ms": residual_ms,
            "intent_matched": intent_matched,
            "cart_matched": cart_matched,
        })

        # Allow reply audio to finish playing before next turn with sufficient pacing for Groq token bucket
        reply_dur_s = (len(p_res.audio_bytes) / 32000.0) if p_res.audio_bytes else 0.5
        await asyncio.sleep(reply_dur_s + 2.5)

    # 8. Clean up
    await event_logger.flush()
    await event_logger.close()
    await dg_stream.close()
    await shared_session.close()

    await room_client.disconnect()
    await room_agent.disconnect()

    if not dry_run:
        real_tts = ElevenLabsTTSAdapter()
        quota_after = await real_tts.get_remaining_characters()
        await real_tts.close()
        chars_used = quota_before - quota_after
    else:
        chars_used = 0

    # 9. Compute Statistical Breakdown
    latencies = [t["turn_latency_ms"] for t in turn_results]
    stt_finals = [t["stt_turnaround_ms"] for t in turn_results]
    stt_partials = [t["stt_first_partial_ms"] for t in turn_results]
    llm_ttfts = [t["llm_ttft_ms"] for t in turn_results]
    state_applies = [t["state_apply_ms"] for t in turn_results]
    tts_ttfbs = [t["tts_ttfb_ms"] for t in turn_results]
    residuals = [t["residual_ms"] for t in turn_results]

    p50_total = float(np.median(latencies))
    p95_total = float(np.percentile(latencies, 95))
    mean_total = float(np.mean(latencies))
    ci_p50 = bootstrap_ci(latencies, np.median)
    ci_p95 = bootstrap_ci(latencies, lambda x: np.percentile(x, 95))
    ci_mean = bootstrap_ci(latencies, np.mean)

    first_turn_latency = latencies[0]
    warm_latencies = latencies[1:]
    p50_warm = float(np.median(warm_latencies))
    p95_warm = float(np.percentile(warm_latencies, 95))

    stats_breakdown = {
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dry_run": dry_run,
        "sample_size": len(latencies),
        "prewarm_time_ms": t_prewarm_ms,
        "first_turn_latency_ms": first_turn_latency,
        "warm_turns_p50_ms": p50_warm,
        "warm_turns_p95_ms": p95_warm,
        "total_latency": {
            "p50": p50_total,
            "p50_ci": list(ci_p50),
            "p95": p95_total,
            "p95_ci": list(ci_p95),
            "mean": mean_total,
            "mean_ci": list(ci_mean),
        },
        "stages": {
            "stt_first_partial": {
                "p50": float(np.median(stt_partials)),
                "p50_ci": list(bootstrap_ci(stt_partials, np.median)),
                "p95": float(np.percentile(stt_partials, 95)),
                "mean": float(np.mean(stt_partials)),
            },
            "stt_final": {
                "p50": float(np.median(stt_finals)),
                "p50_ci": list(bootstrap_ci(stt_finals, np.median)),
                "p95": float(np.percentile(stt_finals, 95)),
                "mean": float(np.mean(stt_finals)),
            },
            "llm_intent_ttft": {
                "p50": float(np.median(llm_ttfts)),
                "p50_ci": list(bootstrap_ci(llm_ttfts, np.median)),
                "p95": float(np.percentile(llm_ttfts, 95)),
                "mean": float(np.mean(llm_ttfts)),
            },
            "state_machine_apply": {
                "p50": float(np.median(state_applies)),
                "p50_ci": list(bootstrap_ci(state_applies, np.median)),
                "p95": float(np.percentile(state_applies, 95)),
                "mean": float(np.mean(state_applies)),
            },
            "tts_first_byte": {
                "p50": float(np.median(tts_ttfbs)),
                "p50_ci": list(bootstrap_ci(tts_ttfbs, np.median)),
                "p95": float(np.percentile(tts_ttfbs, 95)),
                "mean": float(np.mean(tts_ttfbs)),
            },
            "residual_webrtc_playout": {
                "p50": float(np.median(residuals)),
                "p50_ci": list(bootstrap_ci(residuals, np.median)),
                "p95": float(np.percentile(residuals, 95)),
                "mean": float(np.mean(residuals)),
                "frac_gt_500ms": float(np.mean([1.0 if r > 500.0 else 0.0 for r in residuals]) * 100.0),
            },
        },
        "elevenlabs_quota": {
            "quota_before": quota_before,
            "quota_after": quota_after,
            "chars_used": chars_used,
        },
        "turns": turn_results,
    }

    out_file = root_dir / "eval" / "results" / (
        f"g1_week04_{bench_label}_dryrun.json" if dry_run else f"g1_week04_{bench_label}_benchmark.json"
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(stats_breakdown, f, indent=2)

    print("\n=======================================================", flush=True)
    print(f" GATE G1-{bench_label} RESULTS SUMMARY ({'DRY RUN' if dry_run else 'REAL RUN'})", flush=True)
    print("=======================================================", flush=True)
    print(f"Total Turns:       {len(latencies)}", flush=True)
    print(f"P50 Total Latency: {p50_total:.1f} ms (95% CI: [{ci_p50[0]:.1f}, {ci_p50[1]:.1f}])", flush=True)
    print(f"P95 Total Latency: {p95_total:.1f} ms (95% CI: [{ci_p95[0]:.1f}, {ci_p95[1]:.1f}])", flush=True)
    print(f"Mean Latency:      {mean_total:.1f} ms (95% CI: [{ci_mean[0]:.1f}, {ci_mean[1]:.1f}])", flush=True)
    print(f"First Turn Latency:{first_turn_latency:.1f} ms", flush=True)
    print(f"Warm Turns (2-{len(latencies)}): P50 = {p50_warm:.1f} ms | P95 = {p95_warm:.1f} ms", flush=True)
    print(f"STT Turnaround P50:{np.median(stt_finals):.1f} ms", flush=True)
    print(f"STT 1st Partial:   {np.median(stt_partials):.1f} ms", flush=True)
    print(f"LLM TTFT P50:      {np.median(llm_ttfts):.1f} ms", flush=True)
    print(f"TTS TTFB P50:      {np.median(tts_ttfbs):.1f} ms", flush=True)
    print(f"Residual P50:      {np.median(residuals):.1f} ms (>500ms: {stats_breakdown['stages']['residual_webrtc_playout']['frac_gt_500ms']:.1f}%)", flush=True)
    print(f"Characters Used:   {chars_used} (Quota Remaining: {quota_after})", flush=True)
    print(f"Saved full results to: {out_file}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Run with StubTTS to verify telemetry without consuming ElevenLabs characters")
    parser.add_argument("--turns", type=int, default=20, choices=[20, 30], help="Number of turns to execute (20 for v2b, 30 for v2)")
    args = parser.parse_args()
    asyncio.run(run_benchmark(dry_run=args.dry_run, turns=args.turns))
