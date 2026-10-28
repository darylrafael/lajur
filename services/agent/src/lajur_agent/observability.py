"""SQLite Turn Event Logger & Observability for Lajur Voice Pipeline.

Adheres strictly to ADR-0005 (Privacy & Telemetry):
- No raw audio or audio recordings are persisted.
- No visitor PII is stored.
- Records turn-level engineering latency timestamps, token counts, and state transitions.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("lajur.agent.observability")


@dataclass
class TurnEvent:
    session_id: str
    turn_id: int
    client_identity: str
    timestamp_iso: str
    t_speech_end_ms: float
    t_stt_final_ms: float
    t_llm_first_token_ms: float
    t_intent_validated_ms: float
    t_state_applied_ms: float
    t_tts_first_byte_ms: float
    t_first_audio_frame_ms: float
    turn_latency_ms: float
    intent_type: str
    state_from: str
    state_to: str
    tokens_in: int
    tokens_out: int
    llm_model_id: str
    tts_model_id: str
    prompt_hash: str
    cost_usd: float
    mode: str
    t_stt_first_partial_ms: float = 0.0
    t_connect_ms: float = 0.0
    t_agent_publish_ms: float = 0.0


class TurnEventLogger:
    """Thread-safe SQLite turn event database logger with non-blocking async queue support."""

    def __init__(self, db_path: str | Path = "data/turn_events.sqlite3") -> None:
        self._db_path = str(db_path)
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._queue: asyncio.Queue[TurnEvent | None] | None = None
        self._worker_task: asyncio.Task[None] | None = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS turn_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_id INTEGER NOT NULL,
                    client_identity TEXT NOT NULL,
                    timestamp_iso TEXT NOT NULL,
                    t_speech_end_ms REAL NOT NULL,
                    t_stt_final_ms REAL NOT NULL,
                    t_llm_first_token_ms REAL NOT NULL,
                    t_intent_validated_ms REAL NOT NULL,
                    t_state_applied_ms REAL NOT NULL,
                    t_tts_first_byte_ms REAL NOT NULL,
                    t_first_audio_frame_ms REAL NOT NULL,
                    turn_latency_ms REAL NOT NULL,
                    intent_type TEXT NOT NULL,
                    state_from TEXT NOT NULL,
                    state_to TEXT NOT NULL,
                    tokens_in INTEGER NOT NULL,
                    tokens_out INTEGER NOT NULL,
                    llm_model_id TEXT NOT NULL,
                    tts_model_id TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    cost_usd REAL NOT NULL,
                    mode TEXT NOT NULL,
                    t_stt_first_partial_ms REAL NOT NULL DEFAULT 0.0,
                    t_connect_ms REAL NOT NULL DEFAULT 0.0,
                    t_agent_publish_ms REAL NOT NULL DEFAULT 0.0
                )
                """
            )
            # Automatic schema migration for existing databases
            cur = conn.execute("PRAGMA table_info(turn_events)")
            existing_cols = {row["name"] for row in cur.fetchall()}
            for col_name in ("t_stt_first_partial_ms", "t_connect_ms", "t_agent_publish_ms"):
                if col_name not in existing_cols:
                    conn.execute(f"ALTER TABLE turn_events ADD COLUMN {col_name} REAL NOT NULL DEFAULT 0.0")
            conn.commit()

    def start_background_writer(self) -> None:
        """Start the background async worker for non-blocking telemetry writes."""
        if self._worker_task is None or self._worker_task.done():
            self._queue = asyncio.Queue()
            self._worker_task = asyncio.create_task(self._background_worker())

    async def _background_worker(self) -> None:
        assert self._queue is not None
        while True:
            event = await self._queue.get()
            if event is None:
                self._queue.task_done()
                break
            try:
                await asyncio.to_thread(self._write_event_sync, event)
            except Exception as e:
                logger.warning("Error writing turn event in background: %s", e)
            finally:
                self._queue.task_done()

    def _write_event_sync(self, event: TurnEvent) -> None:
        sql = """
        INSERT INTO turn_events (
            session_id, turn_id, client_identity, timestamp_iso,
            t_speech_end_ms, t_stt_final_ms, t_llm_first_token_ms,
            t_intent_validated_ms, t_state_applied_ms, t_tts_first_byte_ms,
            t_first_audio_frame_ms, turn_latency_ms, intent_type,
            state_from, state_to, tokens_in, tokens_out,
            llm_model_id, tts_model_id, prompt_hash, cost_usd, mode,
            t_stt_first_partial_ms, t_connect_ms, t_agent_publish_ms
        ) VALUES (
            :session_id, :turn_id, :client_identity, :timestamp_iso,
            :t_speech_end_ms, :t_stt_final_ms, :t_llm_first_token_ms,
            :t_intent_validated_ms, :t_state_applied_ms, :t_tts_first_byte_ms,
            :t_first_audio_frame_ms, :turn_latency_ms, :intent_type,
            :state_from, :state_to, :tokens_in, :tokens_out,
            :llm_model_id, :tts_model_id, :prompt_hash, :cost_usd, :mode,
            :t_stt_first_partial_ms, :t_connect_ms, :t_agent_publish_ms
        )
        """
        with self._get_connection() as conn:
            conn.execute(sql, asdict(event))
            conn.commit()

    def log_turn(self, event: TurnEvent) -> None:
        """Insert a turn event without blocking the audio critical path."""
        if self._queue is not None:
            self._queue.put_nowait(event)
        else:
            self._write_event_sync(event)

    async def flush(self) -> None:
        """Wait for all pending turn events in the queue to be persisted."""
        if self._queue is not None:
            await self._queue.join()

    async def close(self) -> None:
        """Stop the background writer and ensure all events are flushed."""
        if self._queue is not None and self._worker_task is not None:
            await self._queue.put(None)
            await self._worker_task
            self._worker_task = None
            self._queue = None

    def get_events(self, session_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """Query turn events for analysis."""
        with self._get_connection() as conn:
            if session_id:
                cur = conn.execute(
                    "SELECT * FROM turn_events WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                    (session_id, limit),
                )
            else:
                cur = conn.execute(
                    "SELECT * FROM turn_events ORDER BY id DESC LIMIT ?",
                    (limit,),
                )
            return [dict(r) for r in cur.fetchall()]
