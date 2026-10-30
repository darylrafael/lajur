"""Tests for worker transcript privacy logging and LOG_TRANSCRIPTS control."""

from __future__ import annotations

from lajur_agent.worker import (
    format_bot_reply_log,
    format_user_turn_log,
    should_log_transcripts,
)


def test_should_log_transcripts_defaults_false(monkeypatch):
    """LOG_TRANSCRIPTS defaults to False when unset or set to standard falsy values."""
    monkeypatch.delenv("LOG_TRANSCRIPTS", raising=False)
    assert should_log_transcripts() is False

    monkeypatch.setenv("LOG_TRANSCRIPTS", "false")
    assert should_log_transcripts() is False

    monkeypatch.setenv("LOG_TRANSCRIPTS", "0")
    assert should_log_transcripts() is False

    monkeypatch.setenv("LOG_TRANSCRIPTS", "no")
    assert should_log_transcripts() is False


def test_should_log_transcripts_truthy(monkeypatch):
    """LOG_TRANSCRIPTS returns True when set to true, 1, or yes."""
    monkeypatch.setenv("LOG_TRANSCRIPTS", "true")
    assert should_log_transcripts() is True

    monkeypatch.setenv("LOG_TRANSCRIPTS", "1")
    assert should_log_transcripts() is True

    monkeypatch.setenv("LOG_TRANSCRIPTS", "yes")
    assert should_log_transcripts() is True


def test_format_user_turn_log_privacy_mode():
    """When log_transcripts is False, log only turn ID, length, and event type."""
    secret_utterance = "Saya mau pesan satu burger sapi dengan kartu kredit nomor 1234"
    log_msg = format_user_turn_log(turn_id=3, transcript=secret_utterance, log_transcripts=False)

    assert "[Turn 3]" in log_msg
    assert "event_type=final_transcript" in log_msg
    assert f"length={len(secret_utterance)}" in log_msg
    # Ensure zero transcript words or content are leaked into the log string
    assert "burger" not in log_msg
    assert "kartu kredit" not in log_msg
    assert "1234" not in log_msg
    assert secret_utterance not in log_msg


def test_format_user_turn_log_debug_mode():
    """When log_transcripts is True, include full transcript text."""
    utterance = "Saya mau pesan burger sapi"
    log_msg = format_user_turn_log(turn_id=1, transcript=utterance, log_transcripts=True)

    assert "[Turn 1]" in log_msg
    assert f"User utterance: '{utterance}'" in log_msg


def test_format_bot_reply_log_privacy_mode():
    """When log_transcripts is False, log only turn ID, length, event type, and latency."""
    reply = "Baik kak, 1 burger sapi dicatat. Mau tambah minum?"
    log_msg = format_bot_reply_log(turn_id=2, reply_text=reply, latency_ms=142.8, log_transcripts=False)

    assert "[Turn 2]" in log_msg
    assert "event_type=bot_reply_text" in log_msg
    assert f"length={len(reply)}" in log_msg
    assert "latency=142.8 ms" in log_msg
    # Ensure zero reply text is leaked into the log string
    assert "burger" not in log_msg
    assert "minum" not in log_msg
    assert reply not in log_msg


def test_format_bot_reply_log_debug_mode():
    """When log_transcripts is True, include full bot reply text and latency."""
    reply = "Baik kak, total Rp35.000."
    log_msg = format_bot_reply_log(turn_id=2, reply_text=reply, latency_ms=125.0, log_transcripts=True)

    assert "[Turn 2]" in log_msg
    assert f"Bot reply: '{reply}'" in log_msg
    assert "Latency: 125.0 ms" in log_msg
