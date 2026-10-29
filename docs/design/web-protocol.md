# Web Protocol Specification v1 (Data Channel & Client-Agent Contract)

**Document:** `docs/design/web-protocol.md`  
**Milestone:** Minggu 5 (Web Simulator & UI Contract)  
**Status:** DRAFT / COMMITTED BEFORE IMPLEMENTATION  
**Version:** 1.0  
**Authors:** Daryl (Solo Dev) & Assistant  

---

## 1. Latar Belakang & Acceptance Criteria

### 1.1 Target Minggu 5 (PROJECT_PLAN.md §13 Verbatim)

> **Minggu 5 — Simulator Web (PROJECT_PLAN.md §13 Verbatim)**  
> - Menu board, layar konfirmasi live, transkrip, toggle ID/EN, status mic.  
> - Orang non-teknis memesan tanpa panduan (uji 3 orang).  
> - **Target:** 3 orang awam menyelesaikan order di perangkat sendiri.  

**Persyaratan Tambahan Pemilik Proyek (Owner Requirement — Keputusan Minggu 4):**
- Web UI wajib menampilkan transkrip langsung saat pengguna berbicara (*live transcript while the user speaks*) dan memperbarui keranjang secara *real-time* saat intent diterapkan (*update cart when the intent is applied*).

### 1.2 Invarian Non-Fungsional & Kepatuhan Privasi (NFR-02, NFR-07, ADR-0005)

1. **Transkrip Teks Langsung Selalu Tampil (NFR-07):** Partial transcript wajib dikirimkan secara langsung saat pengguna sedang berbicara ke mikrofon, diikuti oleh transkrip final. Hal ini memberikan umpan balik visual instan (*immediate perceptual confirmation*) bahwa sistem mendengar ucapan pengguna, mengimbangi latensi cloud cascade.
2. **Kepatuhan Privasi Ketat (ADR-0005 & NFR-02):**
   - **Zero Audio Persistence:** File suara pengguna sama sekali tidak disimpan. Aliran suara WebRTC hanya berada dalam memori volatil (RAM) untuk STT lalu dibuang.
   - **Apa yang Disimpan Agen:** Basis data telemetri SQLite (`data/turn_events.sqlite3`) hanya mencatat metrik latensi teknis per tahapan, token usage, perkiraan biaya, dan tipe mutasi state machine. Teks transkrip ucapan pengguna dan raw audio SAMA SEKALI TIDAK DISIMPAN ke dalam SQLite. Transkrip teks hanya diproses in-memory dan disiarkan via data channel. Browser juga tidak menyimpan transkrip di localStorage/cookies (hanya menyimpan preferensi bahasa `lajur_locale`).
3. **Pemisahan Otoritas Mutasi Keranjang:** State keranjang hanya dimutasi oleh `packages/cart` deterministik. Pesan protokol hanya mengirimkan representasi *snapshot* keranjang yang telah tervalidasi.

---

## 2. Audit Implementasi Agen Saat Ini vs Kesenjangan (*Gap Analysis*)

### 2.1 Kondisi Agent Worker Sebelum Minggu 5
- **Topik Data Channel:** Menggunakan topic tunggal `"lajur-control"`.
- **Event yang Dikirim Sebelumnya:**
  - Hanya satu jenis pesan: `type: "cart_update"` yang dikirim setelah giliran percakapan selesai.
  - Respons `type: "pong"` terhadap pesan ping klien.
- **Pesan Masuk Klien yang Ditangani Sebelumnya:**
  - `type: "ping"`
  - `type: "user_transcript"` (penerima teks langsung)

### 2.2 Daftar Kesenjangan (*Gaps to Close*)
1. **Tidak Ada Field Versi Protokol:** Pesan sebelumnya tidak memiliki field `version`. Diperlukan penanda eksplisit `version: "v1"`.
2. **Ketiadaan `partial_transcript`:** Deepgram Nova-3 menghasilkan interim transcripts, namun worker tidak meneruskannya ke data channel saat pengguna sedang berbicara.
3. **Ketiadaan `final_transcript`:** Tidak ada pemisahan tegas antara pengakuan teks final ucapan pengguna dengan perubahan keranjang.
4. **Ketiadaan `intent_applied` Terstruktur:** Pesan `cart_update` lama menggabungkan teks balasan bot, state, dan keranjang tanpa menyertakan `speech_facts` terstruktur, `state_from`, atau identifikasi baris keranjang (`line_id`).
5. **Ketiadaan `bot_reply_text` Terpisah:** Teks bot hanya tercantum di dalam objek cart lama.
6. **Ketiadaan `bot_speaking_start` dan `bot_speaking_end`:** Klien tidak mengetahui kapan bot mulai dan selesai berbicara, sehingga indikator UI "speaking" dan pencegahan collision interaksi tidak sinkron dengan audio WebRTC.
7. **Ketiadaan `pending_question`:** Ketika state masuk ke `awaiting_choice` (misal pilihan minuman combo atau modifier wajib), pilihan yang tersedia (`allowed_choices` / `prompt`) tidak terstruktur rapi untuk komponen UI.
8. **Ketiadaan `handoff`:** Tidak ada pesan eskalasi khusus saat terjadi handoff ke staf manusia dengan pesan simulasi kru restoran.
9. **Ketiadaan `error`:** Kegagalan STT, LLM, atau timeout tidak menghasilkan pesan error terstruktur dengan indikator apakah error dapat dipulihkan (*recoverable*).
10. **Ketiadaan `session_limits`:** Informasi kuota turn (maks 12) dan batas waktu sesi (maks 180 detik / 3 menit per NFR-03 & §11.2) tidak dikirimkan secara berkala ke klien.

---

## 3. Spesifikasi Skema Protokol Web v1

Topik WebRTC Data Channel: **`"lajur-control"`**  
Format Serialisasi: **JSON (UTF-8 encoded)**  
Versi Protokol: **`"v1"`**  

### 3.1 Pesan dari Agent Worker ke Web Client (*Downstream Events*)

Setiap event memiliki discriminator field `type` dan field wajib `version: "v1"`.

#### A. `partial_transcript`
Dikirim secara *unreliable/low-latency* setiap kali STT menghasilkan transkrip sementara saat pengguna masih berbicara.
```json
{
  "version": "v1",
  "type": "partial_transcript",
  "text": "saya mau pesan burger",
  "is_final": false,
  "timestamp_ms": 12450.0
}
```

#### B. `final_transcript`
Dikirim segera setelah deteksi akhir ucapan (*speech_final*) tuntas dan transkrip final dikonfirmasi.
```json
{
  "version": "v1",
  "type": "final_transcript",
  "text": "saya mau pesan burger rendang satu",
  "is_final": true,
  "timestamp_ms": 13150.0
}
```

#### C. `intent_applied`
Dikirim segera setelah Cart State Machine menerapkan intent, memvalidasi menu, dan menghitung total harga baru.
```json
{
  "version": "v1",
  "type": "intent_applied",
  "state": "ordering",
  "state_from": "ordering",
  "cart": {
    "items": [
      {
        "line_id": "line_1",
        "item_id": "burger_rendang",
        "name_id": "Burger Rendang Sapi",
        "name_en": "Beef Rendang Burger",
        "quantity": 1,
        "size": "regular",
        "unit_price": 38000,
        "price": 38000,
        "modifiers": [],
        "slots": {},
        "upsell_rules": []
      }
    ],
    "total_price": 38000,
    "total_item_count": 1,
    "status": "in_progress"
  },
  "speech_facts": {
    "intent_handled": "add_item",
    "items_added": [{"item_id": "burger_rendang", "quantity": 1, "size": "regular"}],
    "items_removed": [],
    "items_modified": [],
    "items_replaced": [],
    "rejections": [],
    "cart_item_count": 1,
    "cart_total_price": 38000,
    "dialog_state": "ordering",
    "requires_confirmation": false
  },
  "timestamp_ms": 13750.0
}
```

#### D. `bot_reply_text`
Teks balasan bot yang dihasilkan (via template deterministik atau LLM verbalizer) yang dibacakan bersamaan dengan audio TTS.
```json
{
  "version": "v1",
  "type": "bot_reply_text",
  "text": "Baik kak, 1 Burger Rendang Sapi sudah masuk keranjang. Ada tambahan lain?",
  "timestamp_ms": 13900.0
}
```

#### E. `bot_speaking_start` & `bot_speaking_end`
Menandai awal dan akhir pengaliran audio TTS agen ke WebRTC AudioTrack.
```json
{
  "version": "v1",
  "type": "bot_speaking_start",
  "timestamp_ms": 14100.0
}
```
```json
{
  "version": "v1",
  "type": "bot_speaking_end",
  "timestamp_ms": 17800.0
}
```

#### F. `pending_question`
Dikirim ketika dialog memerlukan pilihan pelanggan (`dialog_state == "awaiting_choice"`).
```json
{
  "version": "v1",
  "type": "pending_question",
  "kind": "combo_slot",
  "prompt": "Mau pilih minuman apa untuk Paket Hemat?",
  "target_line_id": "line_1",
  "slot_id": "drink",
  "allowed_choices": ["cola", "teh_manis", "air_mineral"],
  "choices": [
    {"id": "cola", "name_id": "Coca-Cola", "name_en": "Coca-Cola", "price_delta": 0},
    {"id": "teh_manis", "name_id": "Teh Manis", "name_en": "Sweet Tea", "price_delta": 0},
    {"id": "air_mineral", "name_id": "Air Mineral", "name_en": "Mineral Water", "price_delta": 0}
  ],
  "timestamp_ms": 14200.0
}
```

#### G. `handoff`
Dikirim ketika kendali dialihkan ke kru manusia.
```json
{
  "version": "v1",
  "type": "handoff",
  "reason": "customer_request",
  "crew_message": "Mohon tunggu sebentar ya kak, kasir manusia kami di konter akan segera melayani Anda.",
  "timestamp_ms": 25100.0
}
```

#### H. `error`
Dikirim jika terjadi kegagalan sistem, timeout, atau pelanggaran batas.
```json
{
  "version": "v1",
  "type": "error",
  "code": "STT_ERROR",
  "message": "Maaf kak, suara kurang jelas. Bisa tolong ulangi pesanannya?",
  "recoverable": true,
  "timestamp_ms": 15000.0
}
```

#### I. `session_limits`
Dikirim secara berkala (atau di akhir setiap turn) untuk memonitor kuota durasi dan batas turn.
```json
{
  "version": "v1",
  "type": "session_limits",
  "turns_used": 2,
  "max_turns": 12,
  "time_elapsed_seconds": 35.4,
  "time_limit_seconds": 180.0,
  "timestamp_ms": 35400.0
}
```

---

### 3.2 Pesan dari Web Client ke Agent Worker (*Upstream Messages*)

1. **`ping`:** `{ "type": "ping", "client_time": 12345.6 }` $\to$ dibalas `{ "type": "pong", "client_time": 12345.6 }`.
2. **`user_transcript`:** `{ "type": "user_transcript", "text": "pesan burger rendang satu" }` (mode fallback teks atau pengujian).
3. **`reset_session`:** `{ "type": "reset_session" }` (tombol *start over* / ulangi pemesanan).

---

## 4. Model Penyimpanan dan Privasi Data (ADR-0005 Compliance)

| Entitas Data | Ditransmisikan ke Data Channel? | Dicatat ke Basis Data Lokal? | Disimpan Persisten ke Disk/Cloud? | Masa Retensi |
| :--- | :---: | :---: | :---: | :---: |
| **Suara Pengguna (Audio Frames)** | Ya (via WebRTC AudioTrack) | **TIDAK** (Zero persistence) | **TIDAK PERNAH** | 0 detik (volatil di RAM) |
| **Transkrip Pengguna (Teks)** | Ya (Partial & Final) | Ya (`turn_events.sqlite3`) | Ya (lokal laptop/worker) | Maks 30 hari |
| **State & Snapshot Keranjang** | Ya (`intent_applied`) | Ya (`turn_events.sqlite3`) | Ya (lokal laptop/worker) | Maks 30 hari |
| **Identitas Pengguna** | Nama acak anonim (`user-xxxx`) | Anonim | Anonim | Maks 30 hari |
| **Metrik Latensi & Token** | Ya (`session_limits`) | Ya (`turn_events.sqlite3`) | Ya (lokal laptop/worker) | Maks 30 hari |
