"""SQLite Turn Event Logger & Observability for Lajur Voice Pipeline.

Adheres strictly to ADR-0005 (Privacy & Telemetry):
- No raw audio or audio recordings are persisted.
- No visitor PII is stored.
- Records turn-level engineering latency timestamps, token counts, and state transitions.
"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


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


class TurnEventLogger:
    """Thread-safe SQLite turn event database logger."""

    def __init__(self, db_path: str | Path = "data/turn_events.sqlite3") -> None:
        self._db_path = str(db_path)
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
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
                    mode TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def log_turn(self, event: TurnEvent) -> None:
        """Insert a turn event row into SQLite."""
        sql = """
        INSERT INTO turn_events (
            session_id, turn_id, client_identity, timestamp_iso,
            t_speech_end_ms, t_stt_final_ms, t_llm_first_token_ms,
            t_intent_validated_ms, t_state_applied_ms, t_tts_first_byte_ms,
            t_first_audio_frame_ms, turn_latency_ms, intent_type,
            state_from, state_to, tokens_in, tokens_out,
            llm_model_id, tts_model_id, prompt_hash, cost_usd, mode
        ) VALUES (
            :session_id, :turn_id, :client_identity, :timestamp_iso,
            :t_speech_end_ms, :t_stt_final_ms, :t_llm_first_token_ms,
            :t_intent_validated_ms, :t_state_applied_ms, :t_tts_first_byte_ms,
            :t_first_audio_frame_ms, :turn_latency_ms, :intent_type,
            :state_from, :state_to, :tokens_in, :tokens_out,
            :llm_model_id, :tts_model_id, :prompt_hash, :cost_usd, :mode
        )
        """
        with self._get_connection() as conn:
            conn.execute(sql, asdict(event))
            conn.commit()

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
