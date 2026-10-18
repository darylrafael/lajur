"""Lajur Walking Skeleton Echo Agent Worker (Minggu 1).

Connects to LiveKit Cloud (or local LiveKit Server) on job dispatch.
Echoes WebRTC data-channel messages (including ping-pong latency measurement)
and echoes incoming audio frames back to the client room without external AI APIs.
"""

import asyncio
import json
import logging
from pathlib import Path

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli

# Load environment variables from root .env if present
env_path = Path(__file__).resolve().parents[4] / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lajur.agent.echo")


async def entrypoint(ctx: JobContext) -> None:
    """Entry point invoked by livekit-agents when dispatched to a room."""
    logger.info("Connecting to LiveKit room: %s", ctx.job.room.name)
    await ctx.connect()
    room = ctx.room

    logger.info("Connected to room %s. Local participant: %s", room.name, room.local_participant.identity)

    # 1. Setup audio echo source & publisher track
    audio_source = rtc.AudioSource(48000, 1)
    echo_track = rtc.LocalAudioTrack.create_audio_track("agent-audio-echo", audio_source)
    publish_options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)

    try:
        await room.local_participant.publish_track(echo_track, publish_options)
        logger.info("Successfully published agent-audio-echo track.")
    except Exception as e:
        logger.warning("Could not publish initial audio track: %s", e)

    # 2. Welcome announcement over data channel
    welcome_msg = json.dumps({
        "type": "echo",
        "payload": "Agent worker aktif (Minggu 1: Echo Mode). WebRTC audio dua arah & data channel terhubung.",
    }).encode("utf-8")

    async def send_welcome() -> None:
        await asyncio.sleep(0.5)
        try:
            await room.local_participant.publish_data(
                welcome_msg,
                topic="lajur-control",
                reliable=True,
            )
        except Exception as e:
            logger.debug("Failed sending welcome message: %s", e)

    asyncio.create_task(send_welcome())

    # 3. Data channel listener (handles ping -> pong for RTT calculation)
    @room.on("data_received")
    def on_data_received(data_packet: rtc.DataPacket) -> None:
        try:
            raw_text = data_packet.data.decode("utf-8")
            msg = json.loads(raw_text)
            if msg.get("type") == "ping":
                # Immediately respond with pong preserving client_time (unreliable for UDP speed)
                pong_data = json.dumps({
                    "type": "pong",
                    "client_time": msg.get("client_time"),
                }).encode("utf-8")
                asyncio.create_task(
                    room.local_participant.publish_data(
                        pong_data,
                        topic="lajur-control",
                        reliable=False,
                    )
                )
        except Exception as e:
            logger.debug("Error processing data packet: %s", e)

    # 4. Audio echo loop
    active_stream_tasks: dict[str, asyncio.Task[None]] = {}

    async def echo_audio_stream(track: rtc.Track) -> None:
        logger.info("Starting audio frame echoing for track %s", track.sid)
        # 50ms frames drastically reduce FFI lock contention on Windows (20 fps instead of 100 fps)
        audio_stream = rtc.AudioStream(
            track,
            sample_rate=48000,
            num_channels=1,
            frame_size_ms=50,
        )
        try:
            async for event in audio_stream:
                await audio_source.capture_frame(event.frame)
                # Yield control to Python asyncio event loop so worker health pings are not blocked
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Audio echo stream error: %s", e)
        finally:
            await audio_stream.aclose()
            active_stream_tasks.pop(track.sid, None)

    def handle_track(track: rtc.Track) -> None:
        if track.kind == rtc.TrackKind.KIND_AUDIO and track.sid not in active_stream_tasks:
            logger.info("Subscribing to audio track: %s", track.sid)
            task = asyncio.create_task(echo_audio_stream(track))
            active_stream_tasks[track.sid] = task

    @room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ) -> None:
        handle_track(track)

    # Check if remote participants already have published audio tracks
    for participant in room.remote_participants.values():
        for publication in participant.track_publications.values():
            if publication.track:
                handle_track(publication.track)

    logger.info("Agent is listening for audio and data channel messages...")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="lajur-echo-agent",
        )
    )
