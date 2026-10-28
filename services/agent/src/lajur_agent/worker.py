"""Lajur Voice Ordering Agent Worker (Minggu 5 - Web Simulator & Web Protocol v1).

Cascade:
  WebRTC Audio (User) -> Silero VAD / Deepgram Nova-3 -> Groq Qwen Intent Parser
  -> Cart State Machine (packages/cart) -> Reply Generator (Template / LLM)
  -> ElevenLabs TTS -> WebRTC Audio (Agent) + WebRTC Data Channel ("lajur-control").

Data Channel Protocol:
  Implements Web Protocol v1 (docs/design/web-protocol.md & ADR-0014).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from lajur_cart.menu_service import MenuService
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli

from lajur_agent.adapters.deepgram import DeepgramSTTAdapter, PersistentDeepgramStream
from lajur_agent.adapters.elevenlabs import ElevenLabsTTSAdapter
from lajur_agent.adapters.fakes import FakeLLMIntentAdapter, FakeSTTAdapter, FakeTTSAdapter
from lajur_agent.adapters.groq import GroqLLMIntentAdapter
from lajur_agent.observability import TurnEventLogger
from lajur_agent.pipeline import VoiceOrderingPipeline
from lajur_agent.protocol import (
    create_bot_reply_text_event,
    create_bot_speaking_end_event,
    create_bot_speaking_start_event,
    create_error_event,
    create_final_transcript_event,
    create_handoff_event,
    create_intent_applied_event,
    create_partial_transcript_event,
    create_pending_question_event,
    create_session_limits_event,
)

# Load environment variables
env_path = Path(__file__).resolve().parents[4] / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lajur.agent.worker")


def create_pipeline(session_id: str, client_identity: str = "web-client") -> VoiceOrderingPipeline:
    """Instantiate a VoiceOrderingPipeline using configured adapters."""
    ms = MenuService()
    event_logger = TurnEventLogger()
    reply_mode = os.getenv("REPLY_MODE", "template").lower()  # "template" or "llm"

    use_fakes = os.getenv("USE_FAKE_ADAPTERS", "").lower() in ("1", "true", "yes")

    deepgram_key = os.getenv("DEEPGRAM_API_KEY", "")
    groq_key = os.getenv("GROQ_API_KEY", "")
    eleven_key = os.getenv("ELEVENLABS_API_KEY", "")

    if use_fakes or not (deepgram_key and groq_key):
        logger.info("[Worker] Initializing pipeline with FAKE adapters for offline testing.")
        stt = FakeSTTAdapter()
        llm = FakeLLMIntentAdapter()
        tts = FakeTTSAdapter()
    else:
        logger.info(
            "[Worker] Initializing pipeline with LIVE adapters (Deepgram Nova-3, Groq Qwen, ElevenLabs)."
        )
        stt = DeepgramSTTAdapter(
            api_key=deepgram_key, model="nova-3", language="id", endpointing=300
        )
        llm = GroqLLMIntentAdapter(api_key=groq_key, model="qwen/qwen3.8-27b", max_tokens=150)
        if eleven_key:
            tts = ElevenLabsTTSAdapter(api_key=eleven_key)
        else:
            logger.warning("[Worker] ELEVENLABS_API_KEY not found; falling back to FakeTTSAdapter.")
            tts = FakeTTSAdapter()

    return VoiceOrderingPipeline(
        session_id=session_id,
        menu_service=ms,
        stt_adapter=stt,
        llm_adapter=llm,
        tts_adapter=tts,
        event_logger=event_logger,
        reply_mode=reply_mode if reply_mode in ("template", "llm") else "template",
        client_identity=client_identity,
    )


async def entrypoint(ctx: JobContext) -> None:
    """Entry point invoked by livekit-agents when dispatched to a room."""
    logger.info("Connecting to LiveKit room: %s", ctx.job.room.name)
    await ctx.connect()
    room = ctx.room

    session_id = f"sess_{room.name}_{int(asyncio.get_event_loop().time())}"
    pipeline = create_pipeline(session_id=session_id)

    # 1. Setup Audio Publisher Track for Agent Voice
    # 16kHz mono PCM matches ElevenLabs output format
    audio_source = rtc.AudioSource(16000, 1)
    agent_audio_track = rtc.LocalAudioTrack.create_audio_track("agent-voice", audio_source)
    publish_options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)

    try:
        await room.local_participant.publish_track(agent_audio_track, publish_options)
        logger.info("Successfully published agent-voice track.")
    except Exception as e:
        logger.warning("Could not publish agent voice track: %s", e)

    # Helper: Publish Web Protocol v1 Event to Data Channel
    async def publish_protocol_event(event_dict: dict, reliable: bool = True) -> None:
        try:
            payload = json.dumps(event_dict).encode("utf-8")
            await room.local_participant.publish_data(
                payload,
                topic="lajur-control",
                reliable=reliable,
            )
        except Exception as e:
            logger.debug("Failed publishing event %s: %s", event_dict.get("type"), e)

    # Legacy broadcast for backward compatibility
    async def broadcast_legacy_cart_state(
        bot_reply: str = "", rejections: list[str] | None = None
    ) -> None:
        cart_snap = {
            **pipeline.session.cart.model_dump(),
            "total_item_count": pipeline.session.cart.total_item_count,
        }
        payload = json.dumps(
            {
                "type": "cart_update",
                "cart": cart_snap,
                "dialog_state": pipeline.session.state,
                "pending_choice": pipeline.session.pending_choice.model_dump()
                if pipeline.session.pending_choice
                else None,
                "bot_reply": bot_reply,
                "rejections": rejections or [],
            }
        ).encode("utf-8")
        try:
            await room.local_participant.publish_data(
                payload,
                topic="lajur-control",
                reliable=True,
            )
        except Exception as e:
            logger.debug("Failed broadcasting legacy cart state: %s", e)

    # Send Welcome Greeting & Initial State
    async def send_welcome() -> None:
        await asyncio.sleep(0.4)
        welcome_text = "Halo kak, selamat datang di Lajur drive-thru! Mau pesan apa hari ini?"

        # Web Protocol v1 Events
        await publish_protocol_event(
            create_intent_applied_event(
                state=pipeline.session.state,
                cart=pipeline.session.cart,
                speech_facts=pipeline.session.speech_facts,
                menu_service=pipeline.menu_service,
            )
        )
        await publish_protocol_event(create_bot_reply_text_event(welcome_text))
        await publish_protocol_event(
            create_session_limits_event(
                turns_used=pipeline.turn_counter,
                max_turns=pipeline.max_turns,
                time_elapsed_seconds=time.perf_counter() - pipeline.created_at,
                time_limit_seconds=pipeline.session_timeout_seconds,
            )
        )
        await broadcast_legacy_cart_state(bot_reply=welcome_text)

        try:
            raw_audio = await pipeline.tts_adapter.synthesize_text(welcome_text)
            if raw_audio:
                await publish_protocol_event(create_bot_speaking_start_event())
                chunk_size = 640  # 20ms at 16kHz 16-bit mono
                for i in range(0, len(raw_audio), chunk_size):
                    chunk = raw_audio[i : i + chunk_size]
                    if len(chunk) == chunk_size:
                        frame = rtc.AudioFrame(
                            data=chunk,
                            sample_rate=16000,
                            num_channels=1,
                            samples_per_channel=320,
                        )
                        await audio_source.capture_frame(frame)
                        await asyncio.sleep(0.018)
                await publish_protocol_event(create_bot_speaking_end_event())
        except Exception as e:
            logger.debug("Error playing welcome audio: %s", e)

    asyncio.create_task(send_welcome())

    # Persistent STT streaming session if supported (e.g. Deepgram Nova-3)
    dg_stream: PersistentDeepgramStream | None = None
    if isinstance(pipeline.stt_adapter, DeepgramSTTAdapter):
        try:
            dg_stream = await pipeline.stt_adapter.create_persistent_stream(sample_rate=16000)
            await dg_stream.connect()
            logger.info("Persistent Deepgram stream initialized for worker session.")
        except Exception as e:
            logger.warning("Could not establish persistent Deepgram stream: %s", e)
            dg_stream = None

    # Handle one user dialog turn
    turn_lock = asyncio.Lock()

    async def handle_user_turn(transcript: str, speech_end: float | None = None) -> None:
        """Execute one complete turn through the pipeline, publish protocol events, and play reply audio."""
        if not transcript.strip():
            return

        async with turn_lock:
            logger.info("[Turn %d] User utterance: '%s'", pipeline.turn_counter + 1, transcript)

            # 1. Emit confirmed final transcript
            await publish_protocol_event(create_final_transcript_event(transcript))

            state_before = pipeline.session.state
            try:
                res = await pipeline.process_turn(transcript, speech_end_timestamp=speech_end)
            except Exception as e:
                logger.error("Pipeline processing turn error: %s", e, exc_info=True)
                await publish_protocol_event(
                    create_error_event(
                        code="PIPELINE_ERROR",
                        message="Maaf kak, terjadi kendala saat memproses pesanan. Bisa diulangi?",
                        recoverable=True,
                    )
                )
                return

            logger.info(
                "[Turn %d] Bot reply: '%s' (Latency: %.1f ms)",
                pipeline.turn_counter,
                res.reply_text,
                res.turn_latency_ms,
            )

            # 2. Emit intent_applied with cart snapshot & speech facts
            await publish_protocol_event(
                create_intent_applied_event(
                    state=pipeline.session.state,
                    cart=pipeline.session.cart,
                    speech_facts=pipeline.session.speech_facts,
                    menu_service=pipeline.menu_service,
                    state_from=state_before,
                )
            )

            # 3. If in awaiting_choice state, emit pending_question
            if pipeline.session.state == "awaiting_choice" and pipeline.session.pending_choice:
                await publish_protocol_event(
                    create_pending_question_event(
                        pipeline.session.pending_choice,
                        menu_service=pipeline.menu_service,
                    )
                )

            # 4. If in handoff state, emit handoff event
            if pipeline.session.state == "handoff":
                await publish_protocol_event(
                    create_handoff_event(
                        reason="customer_request_or_limit",
                        crew_message="Mohon tunggu sebentar ya kak, kasir manusia kami akan segera melayani Anda.",
                    )
                )

            # 5. Emit bot_reply_text
            await publish_protocol_event(create_bot_reply_text_event(res.reply_text))

            # 6. Emit session limits
            await publish_protocol_event(
                create_session_limits_event(
                    turns_used=pipeline.turn_counter,
                    max_turns=pipeline.max_turns,
                    time_elapsed_seconds=time.perf_counter() - pipeline.created_at,
                    time_limit_seconds=pipeline.session_timeout_seconds,
                )
            )

            # 7. Legacy cart broadcast
            await broadcast_legacy_cart_state(bot_reply=res.reply_text, rejections=res.rejections)

            # 8. Push audio frames to WebRTC audio track with speaking markers
            if res.audio_bytes:
                await publish_protocol_event(create_bot_speaking_start_event())
                chunk_size = 640  # 20ms at 16kHz 16-bit mono
                for i in range(0, len(res.audio_bytes), chunk_size):
                    chunk = res.audio_bytes[i : i + chunk_size]
                    if len(chunk) == chunk_size:
                        frame = rtc.AudioFrame(
                            data=chunk,
                            sample_rate=16000,
                            num_channels=1,
                            samples_per_channel=320,
                        )
                        await audio_source.capture_frame(frame)
                        await asyncio.sleep(0.018)
                await publish_protocol_event(create_bot_speaking_end_event())

    # 3. Data Channel Listener (handles ping/pong, text orders fallback, reset)
    last_pong_time = 0.0

    @room.on("data_received")
    def on_data_received(data_packet: rtc.DataPacket) -> None:
        nonlocal last_pong_time
        try:
            raw_text = data_packet.data.decode("utf-8")
            msg = json.loads(raw_text)
            msg_type = msg.get("type")

            if msg_type == "ping":
                now = asyncio.get_event_loop().time()
                if now - last_pong_time < 0.5:
                    return
                last_pong_time = now
                pong_data = json.dumps(
                    {
                        "type": "pong",
                        "client_time": msg.get("client_time"),
                    }
                ).encode("utf-8")
                asyncio.create_task(
                    room.local_participant.publish_data(
                        pong_data,
                        topic="lajur-control",
                        reliable=False,
                    )
                )
            elif msg_type == "user_transcript":
                transcript = msg.get("text", "")
                if transcript:
                    asyncio.create_task(handle_user_turn(transcript))
            elif msg_type == "reset_session":
                logger.info("Received reset_session request from client.")
                pipeline.reset_session()
                asyncio.create_task(send_welcome())
        except Exception as e:
            logger.debug("Error handling data packet: %s", e)

    # 4. Audio stream listener for incoming microphone
    active_stream_tasks: dict[str, asyncio.Task[None]] = {}

    async def process_audio_stream(track: rtc.Track) -> None:
        logger.info("Subscribed to participant audio track: %s", track.sid)
        audio_stream = rtc.AudioStream(
            track,
            sample_rate=16000,
            num_channels=1,
            frame_size_ms=20,
        )

        def on_partial(text: str) -> None:
            if text.strip():
                asyncio.create_task(
                    publish_protocol_event(create_partial_transcript_event(text), reliable=False)
                )

        def on_speech_final(final_text: str, ts: float) -> None:
            if final_text.strip():
                asyncio.create_task(handle_user_turn(final_text, speech_end=ts))

        if dg_stream:
            dg_stream.begin_turn(
                on_first_partial=lambda ts: None,
                on_speech_final=on_speech_final,
                on_partial=on_partial,
            )

        try:
            async for event in audio_stream:
                if dg_stream and dg_stream.is_connected:
                    chunk = event.frame.data.tobytes()
                    await dg_stream.send_audio_chunk(chunk)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Audio stream error: %s", e)
        finally:
            await audio_stream.aclose()
            active_stream_tasks.pop(track.sid, None)

    def handle_track(track: rtc.Track) -> None:
        if track.kind == rtc.TrackKind.KIND_AUDIO and track.sid not in active_stream_tasks:
            task = asyncio.create_task(process_audio_stream(track))
            active_stream_tasks[track.sid] = task

    @room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ) -> None:
        handle_track(track)

    for participant in room.remote_participants.values():
        for publication in participant.track_publications.values():
            if publication.track:
                handle_track(publication.track)

    logger.info("Lajur Voice Ordering Agent (Web Protocol v1) is ready and listening...")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="lajur-voice-agent",
        )
    )
