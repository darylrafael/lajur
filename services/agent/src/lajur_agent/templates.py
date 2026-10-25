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
        return "Baik kak, pesanan segera dialihkan ke kasir kami. Mohon tunggu sebentar ya."

    # 4. Final confirmed order (done)
    if facts.dialog_state == "done":
        total_str = format_idr(facts.cart_total_price)
        return (
            f"Terima kasih kak! Pesanan sudah dikonfirmasi dengan total Rp{total_str}. "
            f"Silakan lanjut ke loket pembayaran."
        )

    # 5. Confirming state (review before completion)
    if facts.dialog_state == "confirming":
        total_str = format_idr(facts.cart_total_price)
        return f"Total pesanan kakak saat ini Rp{total_str}. Ada tambahan lain kak, atau sudah cukup?"

    # 6. Item Replaced
    if facts.items_replaced:
        rep = facts.items_replaced[0]
        old_id = rep.get("old_item_id", "")
        new_id = rep.get("new_item_id", "")
        old_name = get_name(old_id) if old_id else "item sebelumnya"
        new_name = get_name(new_id) if new_id else "item baru"
        return f"Siap kak, {old_name} sudah diganti jadi {new_name}. Ada lagi yang ingin dipesan?"

    # 7. Item Removed
    if facts.items_removed:
        rem = facts.items_removed[0]
        name = get_name(rem.get("item_id", ""))
        qty = rem.get("quantity", 1)
        qty_str = f" {qty}" if qty > 1 else ""
        return f"Baik kak, {name}{qty_str} sudah dibatalkan dari pesanan. Ada tambahan lain?"

    # 8. Item Modified
    if facts.items_modified:
        mod = facts.items_modified[0]
        name = get_name(mod.get("item_id", ""))
        return f"Siap kak, pesanan {name} sudah disesuaikan. Ada lagi?"

    # 9. Item Added
    if facts.items_added:
        added = facts.items_added[0]
        name = get_name(added.get("item_id", ""))
        qty = added.get("quantity", 1)
        prefix = f"{qty} " if qty > 1 else "satu "
        total_str = format_idr(facts.cart_total_price)
        return f"Siap kak, {prefix}{name} sudah masuk keranjang. Total saat ini Rp{total_str}. Mau tambah apa lagi?"

    # 10. Specific Intents Handled without direct item delta
    if facts.intent_handled == "undo_last":
        return "Perubahan terakhir sudah dibatalkan ya kak. Mau pesan apa lagi?"

    if facts.intent_handled == "clear_cart":
        return "Keranjang belanja sudah dikosongkan kak. Mau pesan apa?"

    if facts.intent_handled == "decline_more":
        total_str = format_idr(facts.cart_total_price)
        return f"Baik kak, total pesanannya Rp{total_str}. Mau langsung dikonfirmasi?"

    if facts.intent_handled == "ask_info":
        return (
            "Kami menyediakan aneka burger sapi, ayam goreng renyah, kentang goreng, "
            "dan aneka minuman segar. Mau coba paket hemat kami kak?"
        )

    # 11. Fallback / Unknown
    return "Mohon maaf kak, bisa diulangi pesanannya?"
