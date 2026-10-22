# Intent Parser Contract (LLM Interface Specification)

**Document:** `docs/design/intent-parser-contract.md`  
**Milestone:** Minggu 3 (Cart State Machine + Intent Schema v1)  
**Status:** DRAFT / COMMITTED BEFORE IMPLEMENTATION  
**Version:** 1.0  
**Authors:** Daryl (Solo Dev) & Implementation Agent  

---

## 1. Konteks & Latar Belakang

Pada audit evaluasi akhir Minggu 2 (G1f), diidentifikasi bahwa parser intent LLM yang dievaluasi secara terisolasi mengalami kendala pada ujaran korektif dan bertahap (*multi-turn dialog*). Salah satu penyebab utamanya adalah **parser tidak menerima konteks keranjang belanja saat ini (*current cart context*)**.

Ketika pelanggan berkata:
> *"Eh ganti yang large aja kentangnya"* atau *"Jangan pakai saus sambal ya"*

Parser yang tidak melihat isi keranjang tidak tahu bahwa sudah ada item kentang di keranjang, sehingga tidak dapat membedakan apakah pelanggan ingin menambahkan kentang baru, mengganti ukuran kentang yang sudah ada (`modify_item`), atau menukar item (`replace_item`).

Kontrak ini mendefinisikan interface data yang ketat antara **Agent Worker / Orchestrator** dan **LLM Semantic Parser** untuk fase Minggu 4 mendatang, tanpa memanggil LLM apa pun pada fase Minggu 3.

---

## 2. Input Contract: Apa yang Diterima oleh LLM

Setiap kali LLM dipanggil untuk memetakan ujaran suara menjadi intent, LLM menerima payload JSON terstruktur dengan 4 komponen:

```json
{
  "utterance": "Mbak ganti kentang gorengnya jadi nasi uduk ya, sama es tehnya satu",
  "cart_snapshot": {
    "lines": [
      {
        "line_id": "line_1",
        "item_id": "burger_sapi_keju",
        "name_id": "Burger Sapi Keju",
        "quantity": 1,
        "size": "regular",
        "modifiers": ["opt_extra_cheese"],
        "slots": {}
      },
      {
        "line_id": "line_2",
        "item_id": "kentang_goreng",
        "name_id": "Kentang Goreng",
        "quantity": 1,
        "size": "regular",
        "modifiers": [],
        "slots": {}
      }
    ],
    "total_item_count": 2,
    "total_price_idr": 42000,
    "dialog_state": "ordering"
  },
  "pending_choice": null,
  "menu_context": {
    "allowed_item_ids": [
      "burger_sapi_keju",
      "burger_ayam",
      "nasi_uduk",
      "kentang_goreng",
      "es_teh_manis",
      "coca_cola"
    ],
    "key_aliases": {
      "french fries": "kentang_goreng",
      "fries": "kentang_goreng",
      "nasi": "nasi_uduk",
      "sweet tea": "es_teh_manis",
      "es teh": "es_teh_manis"
    }
  }
}
```

### Penjelasan Komponen Input:
1. **`utterance` (string):** Transkrip teks dari mesin STT streaming (Deepgram Nova-3).
2. **`cart_snapshot` (object):** Snapshot ringkas isi keranjang belanja terkini. Setiap baris memiliki `line_id` stabil (`line_1`, `line_2`, dst.), kuantitas, ukuran, dan modifier yang aktif.
3. **`pending_choice` (object | null):** Jika dialog berada dalam state `awaiting_choice`, memuat pertanyaan pilihan yang sedang ditunggu (misal slot minuman pada combo atau disambiguasi baris).
4. **`menu_context` (object):** Daftar ID menu baku dan sinonim/alias fonetik utama yang sah untuk mencegah halusinasi ID yang tidak terdaftar di `menu.json`.

---

## 3. Output Contract: Apa yang Wajib Dikembalikan oleh LLM

LLM **wajib** mengembalikan response dalam format JSON murni (`response_format={"type": "json_object"}`) yang mematuhi skema amplop (`IntentEnvelope`) dan tervalidasi terhadap [`packages/cart/intent.schema.json`](file:///c:/Users/Lenovo/Downloads/drivethru/packages/cart/intent.schema.json).

### Format Envelope JSON:
```json
{
  "intents": [
    {
      "type": "replace_item",
      "target_line_id": "line_2",
      "replacement_item_id": "nasi_uduk",
      "quantity": 1
    },
    {
      "type": "add_item",
      "item_id": "es_teh_manis",
      "quantity": 1,
      "size": "regular",
      "modifiers": []
    }
  ],
  "customer_language": "id"
}
```

---

## 4. Aturan Validasi & Batasan Keamanan

1. **Haram Memuat Angka Finansial:** Output JSON dilarang memuat harga, diskon, atau total belanja. Jika ada key finansial, Pydantic validator akan langsung merejeki payload dengan status error `FORBIDDEN_FIELD`.
2. **Hanya Menggunakan ID Resmi:** `item_id`, `modifier_id`, dan `slot_id` wajib berupa slug identifier resmi dari katalog menu (misal `"kentang_goreng"`), bukan nama bebas (*"French Fries Crispy"*).
3. **Penyelesaian Referensi Baris:** Jika pelanggan merujuk pada item yang sudah ada di keranjang, LLM diarahkan untuk menyertakan `line_id` dari `cart_snapshot` jika tidak ambigu.
4. **Dilarang Menghasilkan Teks Kasir di Sini:** Tugas menyusun kalimat balasan audio kasir dipisahkan secara terisolasi setelah Cart State Machine menghasilkan `speech_facts`.

---

## 5. Implementasi & Mocking di Minggu 3

Pada fase Minggu 3, **tidak ada pemanggilan LLM API nyata**.  
Seluruh pengujian intent dijalankan menggunakan:
1. Dataset `eval/datasets/v0/gold_intents_v2.jsonl` (hand-written intents).
2. Generator properti acak Hypothesis (`tests/test_property_state_machine.py`).
3. REPL interaktif CLI offline (`python -m lajur_cart.repl`).
