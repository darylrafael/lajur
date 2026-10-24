"""Interactive REPL for Lajur Cart State Machine.

Allows interactive testing by typing JSON intents or simplified commands:
- add <item_id> [quantity] [size]
- remove <item_id> [quantity]
- replace <target_item_id> <replacement_item_id> [quantity]
- modify <item_id> [size=...] [quantity=...]
- answer <choice_id> [slot_id]
- undo
- clear
- confirm
- decline
- handoff [reason]
- info [query]
- cart (show current cart)
- reset
- exit / quit

Usage:
    python -m lajur_cart.repl
"""

import json
from typing import Literal

from pydantic import TypeAdapter

from lajur_cart.intents import (
    AddItemIntent,
    AnswerChoiceIntent,
    AskInfoIntent,
    ClearCartIntent,
    ConfirmIntent,
    DeclineMoreIntent,
    HandoffIntent,
    Intent,
    ModifyItemIntent,
    RemoveItemIntent,
    ReplaceItemIntent,
    UndoLastIntent,
)
from lajur_cart.menu_service import MenuService
from lajur_cart.state_machine import CartSession

intent_adapter = TypeAdapter(Intent)


def parse_input_to_intent(line: str) -> Intent | None:
    line = line.strip()
    if not line:
        return None

    # Try raw JSON intent first
    if line.startswith("{") and line.endswith("}"):
        data = json.loads(line)
        return intent_adapter.validate_python(data)

    parts = line.split()
    cmd = parts[0].lower()

    if cmd == "add":
        if len(parts) < 2:
            print("Usage: add <item_id> [quantity] [size]")
            return None
        item_id = parts[1]
        qty = int(parts[2]) if len(parts) > 2 else 1
        size_raw = parts[3] if len(parts) > 3 else "regular"
        size_variant: Literal["regular", "medium", "large"] = (
            size_raw if size_raw in ("regular", "medium", "large") else "regular"
        )
        return AddItemIntent(item_id=item_id, quantity=qty, size=size_variant)

    if cmd == "remove":
        if len(parts) < 2:
            print("Usage: remove <item_id> [quantity]")
            return None
        item_id = parts[1]
        qty = int(parts[2]) if len(parts) > 2 else None
        return RemoveItemIntent(item_id=item_id, quantity=qty)

    if cmd == "replace":
        if len(parts) < 3:
            print("Usage: replace <target_item_id> <replacement_item_id> [quantity]")
            return None
        target = parts[1]
        replacement = parts[2]
        qty = int(parts[3]) if len(parts) > 3 else 1
        return ReplaceItemIntent(
            target_item_id=target, replacement_item_id=replacement, quantity=qty
        )

    if cmd == "modify":
        if len(parts) < 2:
            print("Usage: modify <item_id> [size=regular|medium|large] [qty=N]")
            return None
        item_id = parts[1]
        size: Literal["regular", "medium", "large"] | None = None
        qty: int | None = None
        for p in parts[2:]:
            if p.startswith("size="):
                s = p.split("=", 1)[1]
                if s in ("regular", "medium", "large"):
                    size = s
            elif p.startswith("qty="):
                qty = int(p.split("=", 1)[1])
        return ModifyItemIntent(item_id=item_id, size=size, quantity=qty)

    if cmd == "answer":
        if len(parts) < 2:
            print("Usage: answer <choice_id> [slot_id]")
            return None
        choice_id = parts[1]
        slot_id = parts[2] if len(parts) > 2 else None
        return AnswerChoiceIntent(choice_id=choice_id, slot_id=slot_id)

    if cmd in ("undo", "undo_last"):
        return UndoLastIntent()

    if cmd in ("clear", "clear_cart"):
        return ClearCartIntent()

    if cmd in ("confirm", "checkout"):
        return ConfirmIntent()

    if cmd in ("decline", "decline_more", "cukup"):
        return DeclineMoreIntent()

    if cmd == "handoff":
        reason = " ".join(parts[1:]) if len(parts) > 1 else "customer_requested"
        return HandoffIntent(reason=reason)

    if cmd == "info":
        query = " ".join(parts[1:]) if len(parts) > 1 else "general"
        return AskInfoIntent(query_type=query)

    print(f"Unknown command '{cmd}'. Type 'help' for instructions or enter valid JSON.")
    return None


def print_session_state(session: CartSession):
    cart = session.cart
    print("\n" + "=" * 50)
    print(f"DIALOG STATE : {session.state.upper()} (Cart Status: {cart.status.upper()})")
    print(f"TOTAL ITEMS  : {cart.total_item_count} items")
    print(f"TOTAL PRICE  : Rp {cart.total_price:,}")
    if session.pending_choice:
        print(f"PENDING CHOICE: [{session.pending_choice.type}] {session.pending_choice.prompt}")
        if session.pending_choice.allowed_choices:
            print(f"  Allowed options: {session.pending_choice.allowed_choices}")
    print("-" * 50)
    if not cart.items:
        print("  [Keranjang Kosong]")
    else:
        for idx, line in enumerate(cart.items, 1):
            detail = f"{idx}. {line.item_id} (x{line.quantity}) - {line.size}"
            if line.modifiers:
                detail += f" | mods: {line.modifiers}"
            if line.slots:
                detail += f" | slots: {line.slots}"
            if line.upsell_rules:
                detail += f" | upsells: {line.upsell_rules}"
            detail += f" -> Rp {line.price:,}"
            print("  " + detail)
    print("=" * 50)

    if session.last_result:
        res = session.last_result
        if res.rejections:
            print("REJECTIONS:")
            for rej in res.rejections:
                print(f"  • [{rej.code}] {rej.message}")
        print("SPEECH FACTS (for TTS/Response):")
        print("  " + json.dumps(res.speech_facts.model_dump(exclude_none=True), indent=2))
        print("=" * 50 + "\n")


def main():
    print("==================================================")
    print("   Lajur Cart State Machine REPL (Minggu 3)       ")
    print("==================================================")
    print("Type JSON intent or simplified command:")
    print("  add <item_id> [qty] [size]")
    print("  remove <item_id> [qty]")
    print("  replace <target> <replacement> [qty]")
    print("  modify <item_id> size=large qty=2")
    print("  answer <choice_id> [slot_id]")
    print("  undo | clear | confirm | decline | handoff")
    print("  cart | reset | exit")
    print("==================================================\n")

    ms = MenuService()
    session = CartSession(ms)
    print_session_state(session)

    while True:
        try:
            line = input("lajur> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting REPL.")
            break

        if not line:
            continue

        if line.lower() in ("exit", "quit"):
            print("Goodbye.")
            break

        if line.lower() == "reset":
            session = CartSession(ms)
            print("Session reset.")
            print_session_state(session)
            continue

        if line.lower() == "cart":
            print_session_state(session)
            continue

        try:
            intent = parse_input_to_intent(line)
            if intent is not None:
                session.apply(intent)
                print_session_state(session)
        except Exception as e:
            print(f"Error processing intent: {e}")


if __name__ == "__main__":
    main()
