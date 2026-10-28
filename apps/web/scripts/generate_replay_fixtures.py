"""Generate deterministic replay event sequences for web simulator replay mode.

Runs scenarios through packages/cart (CartSession) to produce realistic, verified
WebProtocolEvent sequences for:
1. simple: Simple burger and drink order
2. combo: Combo meal with pending choice resolution
3. correction: Adding item, swapping/modifying with undo, confirming
4. out_of_stock: Attempting to order 86'd item with graceful rejection
5. handoff: Customer explicitly escalating to human drive-thru crew
"""

from __future__ import annotations

import json
from pathlib import Path

from lajur_agent.protocol import (
    create_bot_reply_text_event,
    create_bot_speaking_end_event,
    create_bot_speaking_start_event,
    create_final_transcript_event,
    create_handoff_event,
    create_intent_applied_event,
    create_partial_transcript_event,
    create_pending_question_event,
    create_session_limits_event,
)
from lajur_agent.templates import generate_template_reply
from lajur_cart.intents import (
    AddItemIntent,
    AnswerChoiceIntent,
    ConfirmIntent,
    HandoffIntent,
    ReplaceItemIntent,
)
from lajur_cart.menu_service import MenuService
from lajur_cart.state_machine import CartSession, SpeechFacts


def build_scenario_replay(
    scenario_id: str,
    title_id: str,
    title_en: str,
    turns: list[dict],
    ms: MenuService,
) -> dict:
    session = CartSession(ms)
    events = []
    current_time_ms = 0.0

    # 1. Welcome greeting
    welcome_text = "Halo kak, selamat datang di Lajur drive-thru! Mau pesan apa hari ini?"
    current_time_ms += 400.0

    events.append(
        {
            "delay_ms": 400,
            "event": create_intent_applied_event(
                state=session.state,
                cart=session.cart,
                speech_facts=SpeechFacts(
                    intent_handled="welcome",
                    cart_item_count=0,
                    cart_total_price=0,
                    dialog_state=session.state,
                ),
                menu_service=ms,
                timestamp_ms=current_time_ms,
            ),
        }
    )
    events.append(
        {
            "delay_ms": 100,
            "event": create_bot_reply_text_event(welcome_text, timestamp_ms=current_time_ms + 100),
        }
    )
    events.append(
        {
            "delay_ms": 50,
            "event": create_session_limits_event(
                turns_used=0,
                max_turns=12,
                time_elapsed_seconds=0.5,
                time_limit_seconds=180.0,
                timestamp_ms=current_time_ms + 150,
            ),
        }
    )
    events.append(
        {
            "delay_ms": 100,
            "event": create_bot_speaking_start_event(timestamp_ms=current_time_ms + 250),
        }
    )
    events.append(
        {
            "delay_ms": 1800,
            "event": create_bot_speaking_end_event(timestamp_ms=current_time_ms + 2050),
        }
    )
    current_time_ms += 2100.0

    # 2. Process each turn
    for turn_idx, t in enumerate(turns, start=1):
        utterance = t["utterance"]
        partial = t.get("partial", utterance[: len(utterance) // 2])
        intent = t["intent"]

        # Pause before customer starts speaking
        current_time_ms += 800.0
        events.append(
            {
                "delay_ms": 800,
                "event": create_partial_transcript_event(partial, timestamp_ms=current_time_ms),
            }
        )

        # Speech completes
        current_time_ms += 1200.0
        events.append(
            {
                "delay_ms": 1200,
                "event": create_final_transcript_event(utterance, timestamp_ms=current_time_ms),
            }
        )

        # State machine processing
        state_before = session.state
        sm_res = session.apply(intent)
        item_names = {k: v.name_id for k, v in ms.items.items()}
        item_names.update({k: v.name_id for k, v in ms.combos.items()})
        bot_reply = generate_template_reply(sm_res.speech_facts, item_names)

        # Agent processing delay (simulated ~400ms)
        current_time_ms += 450.0
        events.append(
            {
                "delay_ms": 450,
                "event": create_intent_applied_event(
                    state=session.state,
                    cart=session.cart,
                    speech_facts=sm_res.speech_facts,
                    menu_service=ms,
                    state_from=state_before,
                    timestamp_ms=current_time_ms,
                ),
            }
        )

        if session.state == "awaiting_choice" and session.pending_choice:
            events.append(
                {
                    "delay_ms": 50,
                    "event": create_pending_question_event(
                        session.pending_choice,
                        menu_service=ms,
                        timestamp_ms=current_time_ms + 50,
                    ),
                }
            )

        if session.state == "handoff":
            events.append(
                {
                    "delay_ms": 50,
                    "event": create_handoff_event(
                        reason="customer_request",
                        crew_message="Mohon tunggu sebentar ya kak, kasir manusia kami akan segera melayani Anda.",
                        timestamp_ms=current_time_ms + 50,
                    ),
                }
            )

        events.append(
            {
                "delay_ms": 50,
                "event": create_bot_reply_text_event(bot_reply, timestamp_ms=current_time_ms + 100),
            }
        )

        events.append(
            {
                "delay_ms": 50,
                "event": create_session_limits_event(
                    turns_used=turn_idx,
                    max_turns=12,
                    time_elapsed_seconds=round(current_time_ms / 1000.0, 1),
                    time_limit_seconds=180.0,
                    timestamp_ms=current_time_ms + 150,
                ),
            }
        )

        # Bot audio playback
        events.append(
            {
                "delay_ms": 100,
                "event": create_bot_speaking_start_event(timestamp_ms=current_time_ms + 250),
            }
        )

        speaking_duration = max(1200, len(bot_reply) * 45)
        events.append(
            {
                "delay_ms": speaking_duration,
                "event": create_bot_speaking_end_event(
                    timestamp_ms=current_time_ms + 250 + speaking_duration
                ),
            }
        )
        current_time_ms += 250 + speaking_duration

    return {
        "id": scenario_id,
        "title_id": title_id,
        "title_en": title_en,
        "total_duration_ms": current_time_ms,
        "turns_count": len(turns),
        "events": events,
    }


def generate_all_replays() -> None:
    ms = MenuService()
    replays = {}

    # Scenario 1: Simple Order (Burger + Drink)
    replays["simple"] = build_scenario_replay(
        scenario_id="simple",
        title_id="Pesanan Sederhana (Burger & Es Teh)",
        title_en="Simple Order (Burger & Iced Tea)",
        turns=[
            {
                "utterance": "Pesan burger sapi tunggal satu sama es teh manis satu",
                "partial": "Pesan burger sapi tunggal",
                "intent": AddItemIntent(item_id="burger_sapi_tunggal", quantity=1),
            },
            {
                "utterance": "Sama es teh manis satu ya",
                "partial": "Sama es teh",
                "intent": AddItemIntent(item_id="teh_manis", quantity=1),
            },
            {
                "utterance": "Sudah itu saja kak",
                "partial": "Sudah itu",
                "intent": ConfirmIntent(),
            },
        ],
        ms=ms,
    )

    # Scenario 2: Combo Meal with Slot Selection (Awaiting Choice)
    replays["combo"] = build_scenario_replay(
        scenario_id="combo",
        title_id="Paket Combo & Pilihan Minuman (Awaiting Choice)",
        title_en="Combo Meal & Drink Selection (Awaiting Choice)",
        turns=[
            {
                "utterance": "Saya mau pesan paket hemat burger tunggal satu",
                "partial": "Saya mau pesan paket hemat",
                "intent": AddItemIntent(item_id="paket_hemat_burger_tunggal", quantity=1),
            },
            {
                "utterance": "Pilihan utamanya burger sapi tunggal",
                "partial": "Pilihan utamanya burger",
                "intent": AnswerChoiceIntent(choice_id="burger_sapi_tunggal", slot_id="main"),
            },
            {
                "utterance": "Pendampingnya kentang goreng",
                "partial": "Pendampingnya kentang",
                "intent": AnswerChoiceIntent(choice_id="kentang_goreng", slot_id="side"),
            },
            {
                "utterance": "Minumnya coca cola ya",
                "partial": "Minumnya coca",
                "intent": AnswerChoiceIntent(choice_id="cola", slot_id="drink"),
            },
            {
                "utterance": "Udah itu aja",
                "partial": "Udah itu",
                "intent": ConfirmIntent(),
            },
        ],
        ms=ms,
    )

    # Scenario 3: Correction & Modification (Undo / Ganti Item)
    replays["correction"] = build_scenario_replay(
        scenario_id="correction",
        title_id="Koreksi Pesanan & Ganti Item (Undo / Swap)",
        title_en="Order Correction & Item Swap (Undo / Replace)",
        turns=[
            {
                "utterance": "Minta kentang goreng satu",
                "partial": "Minta kentang",
                "intent": AddItemIntent(item_id="kentang_goreng", quantity=1),
            },
            {
                "utterance": "Eh gak jadi kentang, ganti nasi hangat aja",
                "partial": "Eh gak jadi kentang",
                "intent": ReplaceItemIntent(
                    target_item_id="kentang_goreng", replacement_item_id="nasi_putih"
                ),
            },
            {
                "utterance": "Selesai kak",
                "partial": "Selesai",
                "intent": ConfirmIntent(),
            },
        ],
        ms=ms,
    )

    # Scenario 4: Out of Stock (86'd Item Handling)
    ms.items["es_krim_vanila"].in_stock = False
    replays["out_of_stock"] = build_scenario_replay(
        scenario_id="out_of_stock",
        title_id="Stok Habis & Penolakan Ramah (86'd Item)",
        title_en="Out of Stock Handling (86'd Item)",
        turns=[
            {
                "utterance": "Mau pesan es krim vanila dua dong",
                "partial": "Mau pesan es krim vanila",
                "intent": AddItemIntent(item_id="es_krim_vanila", quantity=2),
            },
            {
                "utterance": "Kalau gitu ganti es krim cokelat satu aja",
                "partial": "Kalau gitu ganti es krim cokelat",
                "intent": AddItemIntent(item_id="es_krim_cokelat", quantity=1),
            },
            {
                "utterance": "Udah cukup",
                "partial": "Udah cukup",
                "intent": ConfirmIntent(),
            },
        ],
        ms=ms,
    )
    ms.items["es_krim_vanila"].in_stock = True  # restore

    # Scenario 5: Handoff to Human Crew
    replays["handoff"] = build_scenario_replay(
        scenario_id="handoff",
        title_id="Eskalasi ke Kru Kasir Manusia (Handoff)",
        title_en="Escalation to Human Crew (Handoff)",
        turns=[
            {
                "utterance": "Pesan burger ayam satu",
                "partial": "Pesan burger ayam",
                "intent": AddItemIntent(item_id="burger_ayam_crispy", quantity=1),
            },
            {
                "utterance": "Mbak saya mau ngomong langsung sama kasirnya bisa?",
                "partial": "Mbak saya mau ngomong",
                "intent": HandoffIntent(reason="customer_request"),
            },
        ],
        ms=ms,
    )

    out_file = (
        Path(__file__).resolve().parents[3] / "apps" / "web" / "src" / "data" / "replays.json"
    )
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(replays, f, indent=2, ensure_ascii=False)

    print(f"Generated {out_file} with {len(replays)} scenario fixtures:")
    for k, v in replays.items():
        print(
            f"  - {k}: {v['title_id']} ({v['turns_count']} turns, {v['total_duration_ms']:.0f} ms)"
        )


if __name__ == "__main__":
    generate_all_replays()
