"""Deterministic natural Indonesian template reply generator from SpeechFacts.

Produces consistent, professional drive-thru cashier speech in <0.1ms with 0 token spend.
"""

from __future__ import annotations

from lajur_cart.state_machine import SpeechFacts


def format_idr(amount: int) -> str:
    """Format an integer amount into Indonesian Rupiah format (e.g. 45.000)."""
    return f"{amount:,}".replace(",", ".")


def generate_template_reply(facts: SpeechFacts, item_names: dict[str, str] | None = None) -> str:
    """Generate a conversational Indonesian reply purely from SpeechFacts.

    Args:
        facts: Structured facts emitted by CartSession.apply().
        item_names: Optional mapping from item_id to human-readable Indonesian name.

    Returns:
        Natural, concise Indonesian drive-thru cashier spoken sentence.
    """
    names = item_names or {}

    def get_name(item_id: str) -> str:
        return names.get(item_id, item_id.replace("_", " ").title())

    # 1. Rejections take precedence (explain error clearly)
    if facts.rejections:
        msg = facts.rejections[0].message
        return f"Mohon maaf kak, {msg}"

    # 2. Awaiting customer choice (combo slot or ambiguity)
    if facts.dialog_state == "awaiting_choice" and facts.pending_prompt:
        return facts.pending_prompt.prompt

    # 3. Handoff to human crew
    if facts.dialog_state == "handoff":
        return "Baik kak, pesanan dialihkan ke kasir ya."

    # 4. Final confirmed order (done)
    if facts.dialog_state == "done":
        total_str = format_idr(facts.cart_total_price)
        return f"Pesanan dikonfirmasi! Total Rp{total_str}."

    # 5. Confirming state (review before completion)
    if facts.dialog_state == "confirming":
        total_str = format_idr(facts.cart_total_price)
        return f"Total pesanan Rp{total_str}. Ada tambahan?"

    # 6. Item Replaced
    if facts.items_replaced:
        rep = facts.items_replaced[0]
        new_id = rep.get("new_item_id", "")
        new_name = get_name(new_id) if new_id else "item baru"
        return f"Siap kak, sudah diganti {new_name}."

    # 7. Item Removed
    if facts.items_removed:
        rem = facts.items_removed[0]
        name = get_name(rem.get("item_id", ""))
        qty = rem.get("quantity", 1)
        qty_str = f" {qty}" if qty > 1 else ""
        return f"Baik kak, {name}{qty_str} dibatalkan."

    # 8. Item Modified
    if facts.items_modified:
        mod = facts.items_modified[0]
        name = get_name(mod.get("item_id", ""))
        return f"Siap kak, {name} sudah disesuaikan."

    # 9. Item Added
    if facts.items_added:
        added = facts.items_added[0]
        name = get_name(added.get("item_id", ""))
        qty = added.get("quantity", 1)
        prefix = f"{qty} " if qty > 1 else "1 "
        return f"Baik kak, {prefix}{name} dicatat."

    # 10. Specific Intents Handled without direct item delta
    if facts.intent_handled == "undo_last":
        return "Perubahan terakhir sudah dibatalkan ya kak."

    if facts.intent_handled == "clear_cart":
        return "Keranjang belanja sudah dikosongkan kak."

    if facts.intent_handled == "decline_more":
        total_str = format_idr(facts.cart_total_price)
        return f"Baik kak, totalnya Rp{total_str}."

    if facts.intent_handled == "ask_info":
        return (
            "Kami menyediakan aneka burger sapi, ayam goreng renyah, kentang goreng, "
            "dan aneka minuman segar. Mau coba paket hemat kami kak?"
        )

    # 11. Fallback / Unknown
    return "Mohon maaf kak, bisa diulangi pesanannya?"
