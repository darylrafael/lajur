"""Voice Ordering Pipeline Orchestrator (Cascade: STT -> Intent -> Cart -> TTS).

Enforces:
- Deterministic Cart State Machine mutation alone (packages/cart).
- Strict guardrails (3 min session, 12 turns max, 20 items cap, kill switch).
- Mode toggle: (1) LLM verbalization of SpeechFacts vs (2) Deterministic template reply.
- Per-stage latency timestamps recorded into SQLite event log.
- Hallucination detection logging for verbalized replies.
"""

from __future__ import annotations

import datetime
import logging
import os
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal, cast

from lajur_cart.menu_service import MenuService
from lajur_cart.state_machine import CartSession, SpeechFacts

from lajur_agent.adapters.base import LLMIntentAdapter, STTAdapter, TTSAdapter
from lajur_agent.observability import TurnEvent, TurnEventLogger
from lajur_agent.templates import generate_template_reply

logger = logging.getLogger("lajur.agent.pipeline")


@dataclass
class PipelineTurnResult:
    reply_text: str
    audio_bytes: bytes
    cart: dict[str, Any]
    speech_facts: dict[str, Any]
    turn_event: TurnEvent
    turn_latency_ms: float
    rejections: list[str]
    tts_degraded: bool = False


class VoiceOrderingPipeline:
    """Manages the lifecycle and turn processing of a voice ordering session."""

    def __init__(
        self,
        session_id: str,
        menu_service: MenuService,
        stt_adapter: STTAdapter,
        llm_adapter: LLMIntentAdapter,
        tts_adapter: TTSAdapter,
        event_logger: TurnEventLogger,
        reply_mode: Literal["template", "llm"] = "template",
        client_identity: str = "web-client",
        max_turns: int = 12,
        session_timeout_seconds: float = 180.0,
    ) -> None:
        self.session_id = session_id
        self.menu_service = menu_service
        self.stt_adapter = stt_adapter
        self.llm_adapter = llm_adapter
        self.tts_adapter = tts_adapter
        self.event_logger = event_logger
        self.reply_mode = reply_mode
        self.client_identity = client_identity
        self.max_turns = max_turns
        self.session_timeout_seconds = session_timeout_seconds

        self.session = CartSession(menu_service)
        self.turn_counter = 0
        self.created_at = time.perf_counter()
        self.cumulative_cost_usd = 0.0
        self.max_unknown_intents = int(os.getenv("MAX_UNKNOWN_INTENTS_HANDOFF", "3"))
        self.consecutive_unknown_count = 0
        self.upsell_offered = False
        self.upsell_declined = False
        self.pending_upsell: Any | None = None

        # Build menu context cache for LLM parser
        self._item_names = {item.id: item.name_id for item in menu_service.items.values()}
        self._item_names.update({combo.id: combo.name_id for combo in menu_service.combos.values()})

        aliases_map: dict[str, str] = {}
        for item in menu_service.items.values():
            for a in item.aliases:
                aliases_map[a.lower()] = item.id
        for combo in menu_service.combos.values():
            for a in combo.aliases:
                aliases_map[a.lower()] = combo.id

        self._allowed_item_ids = list(self._item_names.keys())
        self._all_aliases = aliases_map
        self._menu_context = {
            "allowed_item_ids": self._allowed_item_ids,
            "key_aliases": dict(list(aliases_map.items())[:20]),
        }

    def reset_session(self, session_id: str | None = None) -> None:
        """Reset the cart session and timers for a new customer ordering session."""
        self.session_id = session_id or f"sess_{int(time.perf_counter())}"
        self.session = CartSession(self.menu_service)
        self.turn_counter = 0
        self.created_at = time.perf_counter()
        self.consecutive_unknown_count = 0
        self.upsell_offered = False
        self.upsell_declined = False
        self.pending_upsell = None

    def _check_kill_switch(self) -> bool:
        """Check kill switch environment flag."""
        return os.getenv("KILL_SWITCH", "").lower() in ("1", "true", "yes") or os.getenv(
            "EMERGENCY_STOP", ""
        ).lower() in ("1", "true", "yes")

    def _build_cart_snapshot(self) -> dict[str, Any]:
        """Construct compact current-cart snapshot according to intent-parser-contract."""
        lines = []
        for line in self.session.cart.items:
            lines.append({
                "line_id": line.line_id,
                "item_id": line.item_id,
                "name_id": self._item_names.get(line.item_id, line.item_id),
                "quantity": line.quantity,
                "size": line.size,
                "modifiers": list(line.modifiers),
                "slots": dict(line.slots),
            })
        return {
            "lines": lines,
            "total_item_count": self.session.cart.total_item_count,
            "total_price_idr": self.session.cart.total_price,
            "dialog_state": self.session.state,
        }

    def _detect_reply_hallucination(self, reply: str, facts: SpeechFacts) -> None:
        """Log a warning if verbalized reply mentions a menu item absent from facts/cart."""
        reply_lower = reply.lower()
        mentioned_absent: list[str] = []

        active_item_ids = {line.item_id for line in self.session.cart.items}
        for item_dict in facts.items_added + facts.items_modified + facts.items_replaced:
            if "item_id" in item_dict:
                active_item_ids.add(item_dict["item_id"])

        for item_id, name in self._item_names.items():
            if name.lower() in reply_lower and item_id not in active_item_ids:
                mentioned_absent.append(f"{name} ({item_id})")

        if mentioned_absent:
            logger.warning(
                "[Hallucination Alert] Reply mentions items not in cart or facts: %s. Reply: '%s'",
                ", ".join(mentioned_absent),
                reply,
            )

    async def process_turn(
        self,
        utterance: str,
        speech_end_timestamp: float | None = None,
        audio_frame_consumer: Any = None,
        stt_final_timestamp: float | None = None,
        stt_first_partial_timestamp: float | None = None,
        connect_duration_ms: float = 0.0,
        agent_publish_timestamp: float | None = None,
    ) -> PipelineTurnResult:
        """Execute one complete dialog turn across the full cascade."""
        self.turn_counter += 1
        t_speech_end = speech_end_timestamp if speech_end_timestamp is not None else time.perf_counter()
        t_stt_final = stt_final_timestamp if stt_final_timestamp is not None else time.perf_counter()
        state_before = self.session.state

        # Guardrail 1: Kill switch
        if self._check_kill_switch():
            logger.error("Kill switch active! Aborting session %s", self.session_id)
            reply = "Mohon maaf kak, sistem layanan sedang dalam pemeliharaan darurat."
            audio = await self.tts_adapter.synthesize_text(reply)
            t_now = time.perf_counter()
            event = TurnEvent(
                session_id=self.session_id,
                turn_id=self.turn_counter,
                client_identity=self.client_identity,
                timestamp_iso=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                t_speech_end_ms=t_speech_end * 1000.0,
                t_stt_final_ms=t_stt_final * 1000.0,
                t_llm_first_token_ms=t_now * 1000.0,
                t_intent_validated_ms=t_now * 1000.0,
                t_state_applied_ms=t_now * 1000.0,
                t_tts_first_byte_ms=t_now * 1000.0,
                t_first_audio_frame_ms=t_now * 1000.0,
                turn_latency_ms=(t_now - t_speech_end) * 1000.0,
                intent_type="kill_switch",
                state_from=state_before,
                state_to="handoff",
                tokens_in=0,
                tokens_out=0,
                llm_model_id="none",
                tts_model_id=self.tts_adapter.name,
                prompt_hash="none",
                cost_usd=0.0,
                mode=self.reply_mode,
            )
            self.event_logger.log_turn(event)
            return PipelineTurnResult(
                reply_text=reply,
                audio_bytes=audio,
                cart={**self.session.cart.model_dump(), "total_item_count": self.session.cart.total_item_count},
                speech_facts={"dialog_state": "handoff"},
                turn_event=event,
                turn_latency_ms=event.turn_latency_ms,
                rejections=["KILL_SWITCH_ACTIVE"],
            )

        # Guardrail 2: Session timeout (3 minutes)
        elapsed_session = time.perf_counter() - self.created_at
        if elapsed_session > self.session_timeout_seconds:
            reply = "Waktu pemesanan telah mencapai batas 3 menit. Silakan konfirmasi di loket ya kak."
            audio = await self.tts_adapter.synthesize_text(reply)
            t_now = time.perf_counter()
            event = TurnEvent(
                session_id=self.session_id,
                turn_id=self.turn_counter,
                client_identity=self.client_identity,
                timestamp_iso=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                t_speech_end_ms=t_speech_end * 1000.0,
                t_stt_final_ms=t_stt_final * 1000.0,
                t_llm_first_token_ms=t_now * 1000.0,
                t_intent_validated_ms=t_now * 1000.0,
                t_state_applied_ms=t_now * 1000.0,
                t_tts_first_byte_ms=t_now * 1000.0,
                t_first_audio_frame_ms=t_now * 1000.0,
                turn_latency_ms=(t_now - t_speech_end) * 1000.0,
                intent_type="timeout",
                state_from=state_before,
                state_to="handoff",
                tokens_in=0,
                tokens_out=0,
                llm_model_id="none",
                tts_model_id=self.tts_adapter.name,
                prompt_hash="none",
                cost_usd=0.0,
                mode=self.reply_mode,
            )
            self.event_logger.log_turn(event)
            return PipelineTurnResult(
                reply_text=reply,
                audio_bytes=audio,
                cart={**self.session.cart.model_dump(), "total_item_count": self.session.cart.total_item_count},
                speech_facts={"dialog_state": "handoff"},
                turn_event=event,
                turn_latency_ms=event.turn_latency_ms,
                rejections=["SESSION_TIMEOUT_EXCEEDED"],
            )

        # Guardrail 3: Max turns (12 turns)
        if self.turn_counter > self.max_turns:
            reply = "Batas maksimum giliran percakapan tercapai. Pesanan dialihkan ke kasir."
            audio = await self.tts_adapter.synthesize_text(reply)
            t_now = time.perf_counter()
            event = TurnEvent(
                session_id=self.session_id,
                turn_id=self.turn_counter,
                client_identity=self.client_identity,
                timestamp_iso=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                t_speech_end_ms=t_speech_end * 1000.0,
                t_stt_final_ms=t_stt_final * 1000.0,
                t_llm_first_token_ms=t_now * 1000.0,
                t_intent_validated_ms=t_now * 1000.0,
                t_state_applied_ms=t_now * 1000.0,
                t_tts_first_byte_ms=t_now * 1000.0,
                t_first_audio_frame_ms=t_now * 1000.0,
                turn_latency_ms=(t_now - t_speech_end) * 1000.0,
                intent_type="max_turns_exceeded",
                state_from=state_before,
                state_to="handoff",
                tokens_in=0,
                tokens_out=0,
                llm_model_id="none",
                tts_model_id=self.tts_adapter.name,
                prompt_hash="none",
                cost_usd=0.0,
                mode=self.reply_mode,
            )
            self.event_logger.log_turn(event)
            return PipelineTurnResult(
                reply_text=reply,
                audio_bytes=audio,
                cart={**self.session.cart.model_dump(), "total_item_count": self.session.cart.total_item_count},
                speech_facts={"dialog_state": "handoff"},
                turn_event=event,
                turn_latency_ms=event.turn_latency_ms,
                rejections=["MAX_TURNS_EXCEEDED"],
            )

        # Stage 1: LLM Intent Parsing
        cart_snap = self._build_cart_snapshot()
        pending_snap = self.session.pending_choice.model_dump() if self.session.pending_choice else None

        t_llm_start = time.perf_counter()
        utterance_lower = utterance.lower()
        matched_aliases = {k: v for k, v in self._all_aliases.items() if k in utterance_lower}
        if len(matched_aliases) < 15:
            for k, v in list(self._all_aliases.items())[:20]:
                if len(matched_aliases) >= 20:
                    break
                matched_aliases[k] = v

        turn_menu_context = {
            "allowed_item_ids": self._allowed_item_ids,
            "key_aliases": matched_aliases,
        }

        intent_res = await self.llm_adapter.parse_intent(
            transcript=utterance,
            cart_snapshot=cart_snap,
            pending_choice=pending_snap,
            menu_context=turn_menu_context,
        )
        t_llm_first_tok = t_llm_start + (intent_res.ttft_ms / 1000.0)
        t_intent_valid = time.perf_counter()

        # Stage 2: State Machine Apply (Only packages/cart mutates the cart)
        last_facts = SpeechFacts(
            intent_handled="unknown",
            cart_item_count=self.session.cart.total_item_count,
            cart_total_price=self.session.cart.total_price,
            dialog_state=self.session.state,
        )

        for raw_it in intent_res.intents:
            from lajur_cart.intents import (
                AddItemIntent,
                AnswerChoiceIntent,
                AskInfoIntent,
                ClearCartIntent,
                ConfirmIntent,
                DeclineMoreIntent,
                HandoffIntent,
                ModifyItemIntent,
                RemoveItemIntent,
                ReplaceItemIntent,
                UndoLastIntent,
                UnknownIntent,
            )

            type_cls_map = {
                "add_item": AddItemIntent,
                "remove_item": RemoveItemIntent,
                "modify_item": ModifyItemIntent,
                "replace_item": ReplaceItemIntent,
                "undo_last": UndoLastIntent,
                "clear_cart": ClearCartIntent,
                "answer_choice": AnswerChoiceIntent,
                "confirm": ConfirmIntent,
                "decline_more": DeclineMoreIntent,
                "handoff": HandoffIntent,
                "ask_info": AskInfoIntent,
                "unknown": UnknownIntent,
            }
            itype = raw_it.get("type", "unknown")
            cls_ = type_cls_map.get(itype, UnknownIntent)
            clean_it = dict(raw_it)
            if "params" in clean_it and isinstance(clean_it["params"], dict):
                params_dict = clean_it.pop("params")
                for k, v in params_dict.items():
                    if k not in clean_it:
                        clean_it[k] = v
            try:
                it_obj = cls_.model_validate(clean_it)
            except Exception as e:
                logger.warning("Intent validation fallback on '%s': %s", itype, e)
                it_obj = UnknownIntent(raw_text=utterance, reason="unsupported_fields")

            res = self.session.apply(it_obj)
            last_facts = res.speech_facts

        t_state_applied = time.perf_counter()

        # Check repeated unknown / low confidence failures (FR-09 handoff trigger)
        if last_facts.intent_handled == "unknown":
            self.consecutive_unknown_count += 1
            if self.consecutive_unknown_count >= self.max_unknown_intents and self.session.state != "handoff":
                logger.warning(
                    "[Handoff Trigger] Consecutive unknown intents (%d >= %d). Triggering crew handoff.",
                    self.consecutive_unknown_count,
                    self.max_unknown_intents,
                )
                self.session.state = "handoff"
                self.session.cart.status = "handoff"
                last_facts.dialog_state = "handoff"
                last_facts.intent_handled = "handoff"
        elif self.session.state != "handoff":
            self.consecutive_unknown_count = 0

        # Check customer decline for upsell (FR-10: never repeated after decline)
        any_decline = any(raw_it.get("type") == "decline_more" for raw_it in intent_res.intents)
        if any_decline or any(w in utterance_lower for w in ("tidak usah", "nggak usah", "gak usah", "cukup itu aja", "itu aja", "nggak", "tidak", "gak")):
            self.upsell_declined = True
            self.pending_upsell = None
        elif self.pending_upsell is not None:
            # Customer accepted pending upsell
            any_confirm = any(raw_it.get("type") in ("confirm", "answer_choice", "add_item") for raw_it in intent_res.intents)
            if any_confirm or any(w in utterance_lower for w in ("ya", "iya", "mau", "boleh", "upsize")):
                target_item = getattr(self.pending_upsell, "target_item", None)
                if target_item:
                    from lajur_cart.intents import AddItemIntent
                    res_upsell = self.session.apply(AddItemIntent(item_id=target_item, quantity=1))
                    last_facts = res_upsell.speech_facts
                self.pending_upsell = None

        # Stage 3: Reply Generation
        tokens_in = intent_res.tokens_in
        tokens_out = intent_res.tokens_out

        if self.session.state == "handoff":
            reply_text = "Baik kak, pesanan dialihkan ke kasir ya."
        elif self.reply_mode == "template":
            reply_text = generate_template_reply(last_facts, self._item_names)
        else:
            # Mode 1: LLM verbalization of SpeechFacts
            if hasattr(self.llm_adapter, "verbalize_reply"):
                v_text, _, v_in, v_out = await self.llm_adapter.verbalize_reply(
                    speech_facts=last_facts.model_dump(),
                    cart_snapshot=self._build_cart_snapshot(),
                )
                reply_text = v_text
                tokens_in += v_in
                tokens_out += v_out
            else:
                reply_text = generate_template_reply(last_facts, self._item_names)

            self._detect_reply_hallucination(reply_text, last_facts)

        # Contextual Upsell Trigger (FR-10: max 1 per order, non-blocking, driven by menu rules)
        if not self.upsell_offered and not self.upsell_declined and self.session.state in ("ordering", "awaiting_choice"):
            for line in self.session.cart.items:
                if line.item_id in self.menu_service.combos:
                    combo = self.menu_service.combos[line.item_id]
                    if combo.upsell_rules:
                        rule = combo.upsell_rules[0]
                        self.upsell_offered = True
                        self.pending_upsell = rule
                        reply_text = f"{reply_text.rstrip('. ')}. {rule.prompt_id}"
                        break

        # Stage 4: TTS Synthesis with Graceful Degradation
        t_tts_start = time.perf_counter()
        t_tts_first_byte: float | None = None
        t_first_audio: float | None = None
        collected_chunks: list[bytes] = []
        tts_degraded = False

        try:
            stream_fn = cast(Any, getattr(self.tts_adapter, "stream_audio_chunks", None))
            if audio_frame_consumer is not None and callable(stream_fn):
                stream_iter = cast(AsyncIterator[bytes], stream_fn(reply_text))
                async for pcm_frame in stream_iter:
                    now = time.perf_counter()
                    if t_tts_first_byte is None:
                        t_tts_first_byte = now
                        t_first_audio = now
                    collected_chunks.append(pcm_frame)
                    await audio_frame_consumer(pcm_frame)
                audio_bytes = b"".join(collected_chunks)
            else:
                audio_bytes = await self.tts_adapter.synthesize_text(reply_text)
                t_first_audio = time.perf_counter()
                t_tts_first_byte = t_tts_start + 0.120
        except Exception as tts_err:
            logger.warning(
                "[TTS Degradation] TTS synthesis failed (%s). Continuing in text-only mode.",
                tts_err,
            )
            audio_bytes = b""
            tts_degraded = True
            t_first_audio = time.perf_counter()
            t_tts_first_byte = t_first_audio

        if t_tts_first_byte is None:
            t_tts_first_byte = time.perf_counter()
        if t_first_audio is None:
            t_first_audio = time.perf_counter()

        # Compute cost estimation
        # Groq Qwen: ~$0.20/1M tokens, Deepgram ~$0.0077/min, ElevenLabs Free
        cost = (tokens_in * 0.0000002) + (tokens_out * 0.0000002)
        self.cumulative_cost_usd += cost

        # Construct and log TurnEvent
        turn_latency_ms = (t_first_audio - t_speech_end) * 1000.0
        prompt_hash = getattr(self.llm_adapter, "prompt_hash", "none")

        event = TurnEvent(
            session_id=self.session_id,
            turn_id=self.turn_counter,
            client_identity=self.client_identity,
            timestamp_iso=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            t_speech_end_ms=t_speech_end * 1000.0,
            t_stt_final_ms=t_stt_final * 1000.0,
            t_llm_first_token_ms=t_llm_first_tok * 1000.0,
            t_intent_validated_ms=t_intent_valid * 1000.0,
            t_state_applied_ms=t_state_applied * 1000.0,
            t_tts_first_byte_ms=t_tts_first_byte * 1000.0,
            t_first_audio_frame_ms=t_first_audio * 1000.0,
            turn_latency_ms=turn_latency_ms,
            intent_type=last_facts.intent_handled,
            state_from=state_before,
            state_to=self.session.state,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            llm_model_id=self.llm_adapter.name,
            tts_model_id="text_only_fallback" if tts_degraded else self.tts_adapter.name,
            prompt_hash=prompt_hash,
            cost_usd=cost,
            mode=self.reply_mode,
            t_stt_first_partial_ms=(stt_first_partial_timestamp * 1000.0) if stt_first_partial_timestamp else 0.0,
            t_connect_ms=connect_duration_ms,
            t_agent_publish_ms=(agent_publish_timestamp * 1000.0) if agent_publish_timestamp else (t_first_audio * 1000.0),
        )
        self.event_logger.log_turn(event)

        rejection_msgs = [r.message for r in last_facts.rejections]
        return PipelineTurnResult(
            reply_text=reply_text,
            audio_bytes=audio_bytes,
            cart={**self.session.cart.model_dump(), "total_item_count": self.session.cart.total_item_count},
            speech_facts=last_facts.model_dump(),
            turn_event=event,
            turn_latency_ms=turn_latency_ms,
            rejections=rejection_msgs,
            tts_degraded=tts_degraded,
        )
