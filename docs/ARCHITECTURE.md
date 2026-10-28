# Arsitektur Sistem — Lajur

**Status:** v1.1 · **Terkait:** ADR-0001 s/d ADR-0009

---

## 1. Ikhtisar Arsitektur

Lajur menggunakan arsitektur **cascade streaming pipeline** (STT &rarr; LLM &rarr; TTS) yang dikendalikan oleh worker Python berbasis LiveKit Agents, dipasangkan dengan **Cart State Machine deterministik murni** di luar LLM.

Desain ini sengaja menghindari model audio-to-audio end-to-end proprietary untuk memastikan:
1. **Validasi deterministik**: Menu, modifikasi, stok, dan harga diverifikasi sebelum bot berbicara.
2. **Explainability & Observability**: Latensi dan tingkat kesalahan diukur per komponen secara transparan.
3. **Vendor Agility**: Seluruh penyedia pihak ketiga berada di balik antarmuka adapter (ADR-0004).

---

## 2. Diagram Aliran Data & Komponen

```text
Browser (Next.js, i18n)
  mic + preset noise (Web Audio API) ──WebRTC──► LiveKit Cloud (atau local dev server)
  menu board / layar konfirmasi / transkrip ◄── Data Channel ──┐
                                                               │
Agent Worker (Python, livekit-agents) ◄────── dispatch ────────┘
   ├─ VAD & Turn Detection (Silero VAD + Semantic Pause Detection)
   ├─ STT Streaming Adapter (Deepgram / Soniox / Gladia)
   ├─ LLM + Tool Calling Adapter (Gemini Flash / GPT-4o-mini) ──► Intent JSON
   ├─ Cart State Machine (Deterministik murni)
   │     └─ Menu Service (Menu, combo rules, modifiers, stok 86'd, jam operasional)
   ├─ TTS Streaming Adapter (Azure Speech / Cartesia / ElevenLabs)
   ├─ Guardrails (Batas item, batas turn, anti-injection, session timeout)
   └─ Structured Event Log (Turn, intent, latensi per tahap, token/karakter) ──► SQLite/Postgres
                                                                             └─► Dashboard Metrik Publik

Eval Harness (Offline / CI):
  Skenario JSONL ──► Audio Sintetis (+ Noise & SNR) ──► Agent Worker ──► Evaluasi Cart vs Ground Truth
```

---

## 3. Komponen dan Pembagian Tanggung Jawab

| Komponen | Tanggung Jawab Utama | Hal yang DILARANG Dilakukan |
|---|---|---|
| **Cart State Machine** | Satu-satunya sumber kebenaran keranjang belanja; mengeksekusi mutasi (`add`, `remove`, `modify`, `undo`, `confirm`, `handoff`); memvalidasi ketersediaan stok dan jam menu. | Melakukan parsing bahasa alami atau memanggil I/O eksternal secara langsung. |
| **LLM Intent Parser** | Mengubah transkrip ucapan pengguna menjadi intent terstruktur (format JSON) dan menyusun respons lisan kasir yang ringkas (< 150 token). | Mengubah keranjang belanja secara langsung; mengarang item di luar menu; mengakses database. |
| **Menu Service** | Menyediakan daftar item menu, variasi ukuran, aturan slot paket hemat (combo), alias pengucapan ID–EN, dan harga resmi. | Mengelola state percakapan atau state keranjang pelanggan. |
| **Agent Worker** | Mengorkestrasi WebRTC streaming, deteksi jeda bicara (turn detection), penanganan interupsi (*barge-in*), pemanggilan adapter, dan pengiriman event via WebRTC data channel. | Menyimpan audio suara pengguna ke disk/storage permanen. |
| **Event Logger** | Merekam jejak audit operasional: timestamp turn, intent JSON, latensi per komponen, dan token usage untuk metrik publik. | Merekam rekaman suara / raw audio biometrik pengguna (ADR-0005). |

---

## 4. Invarian Arsitektur (Hard Constraints)

1. **Pipeline adalah Cascade**: Urutan alur selalu STT &rarr; LLM &rarr; TTS. Bot kasir tidak pernah bersuara sebelum intent divalidasi oleh Cart State Machine.
2. **Cart State Machine Mutates Cart**: LLM hanya menghasilkan intent JSON. State machine memvalidasi intent tersebut terhadap aturan menu sebelum menerapkan mutasi.
3. **Harga dari Menu Service**: LLM dilarang menghitung atau menyebutkan total harga dari ingatannya sendiri. Harga selalu dikalkulasi secara deterministik oleh Menu Service.
4. **Semua Vendor di Balik Adapter**: Kode inti sistem tidak pernah mengimpor library SDK vendor secara langsung. Semua vendor diakses via antarmuka standar (`STTProvider`, `LLMProvider`, `TTSProvider`).
5. **LLM Tanpa Akses Database Langsung**: LLM beroperasi secara stateless berbasis instruksi prompt dan function calling terisolasi.
6. **Zero Audio Persistence**: Audio stream diproses di memori dan langsung dibuang. Tidak ada penyimpanan file suara ke disk lokal maupun cloud bucket.

---

## 5. Implementasi Walking Skeleton (Minggu 1)

Topologi implementasi awal pada Minggu 1 berfokus pada pembuktian jalur komunikasi WebRTC tanpa memicu biaya API vendor (STT/LLM/TTS):

```text
Browser Client (Next.js 14)
   │
   ├── HTTP POST /api/token ──► Issues LiveKit JWT token (server-side secret)
   │
   ├── WebRTC Audio Track (Mic) ──► LiveKit Server ──► AudioStream ──► Agent Worker
   │                                                                     │ (Echo loop)
   │   WebRTC Audio Track (Speaker) ◄── LiveKit Server ◄── AudioSource ◄─┘
   │
   └── WebRTC Data Channel ("lajur-control")
          Ping { type: "ping", timestamp } ──► Agent Worker
          Pong { type: "pong", client_time, server_time } ◄── Agent Worker
          └──► Client computes Round-Trip Latency (RTT ms) live
```

1. **`apps/web` (Next.js App Router):**
   - Menggunakan `@livekit/components-react` untuk koneksi room WebRTC.
   - Endpoint `/api/token` mengenerate access token berdurasi singkat secara acak per room, dengan placeholder siap pasang untuk Cloudflare Turnstile dan rate-limiting IP.
   - Mengukur round-trip time (RTT) secara live via data channel `lajur-control` setiap detik.
2. **`services/agent` (Python Worker):**
   - Berjalan dengan runtime `livekit-agents` (1.8.x) Python 3.12.
   - Mengonsumsi track audio mikrofon pelanggan via `rtc.AudioStream`, lalu memancarkannya kembali ke room via `rtc.AudioSource` (echo test murni tanpa vendor STT/TTS).
   - Menanggapi heartbeat ping-pong untuk pengujian latency WebRTC.
3. **`infra/docker-compose.yml`:**
   - Menyediakan instance LiveKit Server lokal mandiri (port 7880) untuk pengembangan offline di Windows / WSL tanpa bergantung kuota LiveKit Cloud.
4. **Keputusan Hosting:**
   - Didokumentasikan dalam ADR-0009 (`docs/decisions/0009-hosting-frontend-and-worker.md`).


---

## 6. Cart State Machine & Intent Schema v1 (Minggu 3)

Implementasi state machine deterministik murni dan skema intent v1 (`packages/cart`):

```text
LLM Semantic Intent Parser (Stateless, Prompt / Tool Calling)
   │
   └──► Proposes IntentEnvelope JSON (Discriminator: type, extra="forbid", no price fields)
           │
           ▼
   apply_intent(current_state, cart, intent, menu_service, context, history, pending_choice)
           │
           ├─► MenuService Validation (in_stock, available_hours, size, modifiers, 20-item cap)
           ├─► Dialog Transitions: ordering ──► awaiting_choice ──► confirming ──► done / handoff
           ├─► Total Price Computation (Strictly integer rupiah from menu.json)
           └─► StateMachineResult(new_state, cart, events, rejections, speech_facts, pending_choice)
```

1. **Intent Schema v1 Frozen (`packages/cart/intent.schema.json`):**
   - Diskriminated union 12 intent Pydantic: `add_item`, `remove_item`, `modify_item`, `replace_item`, `undo_last`, `clear_cart`, `answer_choice`, `confirm`, `decline_more`, `handoff`, `ask_info`, `unknown`.
   - Menggunakan `ConfigDict(extra="forbid")` dan tidak memiliki satupun field keuangan (`price`, `total`, `discount`), sehingga manipulasi harga oleh LLM menjadi mustahil secara konstruksi (*impossible by construction*).
2. **Pure & Deterministic State Machine (`lajur_cart.state_machine`):**
   - Fungsi murni `apply_intent()` mengembalikan state baru tanpa efek samping (I/O murni terpisah).
   - Seluruh mutasi keranjang hanya dapat dipicu oleh state machine; LLM terisolasi total dari state memori maupun mutasi langsung.
   - Mendukung riwayat multi-turn, undo per aksi, penanganan ambiguitas, dan slot paket hemat (`awaiting_choice`).
3. **Kepatuhan Skenario 100%:**
   - Lulus 136/136 pengujian replay dataset pada `eval/datasets/v0/gold_intents_v2.jsonl`.
   - 100% lulus di seluruh kategori utama: *simple* (15/15), *quantity* (14/14), *modifier* (21/21), *combo* (24/24), *correction/undo* (11/11), *out_of_stock* (5/5), *breakfast* (9/9), *handoff* (8/8), *injection* (8/8).
4. **Verifikasi Properti & Coverage:**
   - Pengujian berbasis properti (`Hypothesis`) memverifikasi 8 invarian bisnis utama (validitas keranjang, determinisme, batas kuantitas 20, batas jam operasional, idempotensi konfirmasi, ketahanan terhadap terminal state).
   - Mencapai 96% line coverage pada modul `packages/cart`.
5. **Interactive REPL CLI (`python -m lajur_cart.repl`):**
   - Memungkinkan pengujian interaktif langsung oleh manusia via CLI dengan format JSON intent atau perintah teks singkat (`add`, `remove`, `replace`, `modify`, `confirm`, `undo`).

---

## 7. Arsitektur Voice Ordering Pipeline Tracer Bullet (Minggu 4)

Pada Minggu 4, walking skeleton dikembangkan menjadi tracer bullet pipeline suara penuh yang mengintegrasikan cascade nyata dari audio WebRTC hingga audio balasan kasir:

```text
WebRTC Audio Client (Mic)
       │
       ▼
[LiveKit Agent Worker (services/agent)]
       │
       ├─► 1. STT Adapter (Deepgram Nova-3 WebSocket, endpointing=500ms)
       │       └──> Output: Transkrip Teks Bahasa Indonesia
       │
       ├─► 2. LLM Intent Adapter (Groq Qwen-27b Non-Reasoning, max 150 token)
       │       └──> Output: IntentEnvelope (Pydantic Schema v1 tervalidasi)
       │
       ├─► 3. Cart State Machine (packages/cart deterministik murni)
       │       └──> Output: SpeechFacts + State Baru + Keranjang Belanja Terupdate
       │
       ├─► 4. Balasan Kasir (Mode Ganda yang Dapat Dipilih):
       │       ├─ Mode 1: Verbalisasi LLM (Groq Qwen-27b dari SpeechFacts)
       │       └─ Mode 2: Templat Deterministik (Tanpa jeda token LLM)
       │
       ├─► 5. TTS Streaming Adapter (ElevenLabs Flash v2.5, chunk 640-byte linear16)
       │       └──> Output: Streaming Frame PCM 16kHz
       │
       ├─► 6. WebRTC Audio Output (Agent Audio Track)
       │
       └─► 7. WebRTC Data Channel ("lajur-control")
               └──> Payload JSON: Sync Cart, Transkrip Langsung, SpeechFacts

[Observability & Guardrails]
       ├─ Guardrails: Kill switch (KILL_SWITCH / EMERGENCY_STOP), 3-min timeout, max 12 turns, 20-items cap
       └─ SQLite Event Logger (TurnEventLogger): Latensi per-tahap, token, biaya, zero raw audio persistence
```

1. **Streaming Audio Chunking & Low TTFB:** Audio balasan dari ElevenLabs Flash v2.5 di-stream langsung secara per-chunk (640 bytes = 20ms frame) ke WebRTC AudioSource tanpa menunggu buffering file audio utuh, memangkas latensi putaran balasan kasir.
2. **Koneksi STT Per-Turn:** Setiap giliran ucapan menggunakan koneksi streaming WebSocket Deepgram independen dengan `endpointing=500`, menjamin 0% false cutoff dan mengisolasi konteks VAD antar-skenario.
3. **Sinkronisasi Layar Klien:** State keranjang mutakhir dan status dialog disiarkan secara real-time via data channel WebRTC `lajur-control`.
4. **Audit Observabilitas Tanpa Penyimpanan Suara:** Setiap giliran percakapan mencatat jejak timestamp objektif ke `data/turn_events.sqlite3` tanpa menyimpan raw audio (mematuhi ADR-0005).


---

## 8. Arsitektur Simulator Web & Web Protocol v1 (Minggu 5)

Pada Minggu 5, antarmuka visual (`apps/web`) diintegrasikan dengan pipeline suara melalui **Web Protocol v1** (`docs/design/web-protocol.md`, `packages/cart/web-protocol.schema.json`). Simulator web beroperasi dalam dua mode yang berbagi komponen UI dan logika penanganan event yang identik:

```text
[Mode 1: Live WebRTC Mode (Worker Laptop)]
Browser (Mic Input) ──WebRTC Audio──► LiveKit Cloud ──WebRTC Audio──► Agent Worker (Laptop)
                                                                           │
                                                                 (Event Serializer)
                                                                           │
Browser (React UI) ◄──DataChannel ("lajur-control")────────────────────────┘
  ├─ Live Partial Transcript (NFR-07)
  ├─ Real-Time Cart Update (NFR-07)
  └─ Bot Speaking Visualizer & State Controls

[Mode 2: Offline Replay Mode (Zero Backend / Static / Showcase)]
Browser (Next.js) ──Local Timer Loop──► Event Dispatcher (useSimulator hook)
  ├─ Fixtures: 5 Gold Replay Scenarios (packages/cart state machine generated)
  └─ Komponen UI memproses event yang identik dengan Mode Live (tanpa WebRTC/Vendor)
```

### Karakteristik & Invarian Utama:
1. **Web Protocol v1 Strict Schema:**
   - Seluruh pesan antara worker dan antarmuka web divalidasi terhadap JSON Schema (`packages/cart/web-protocol.schema.json`).
   - Tipe event resmi:
     - `partial_transcript`: Transkrip sementara saat pengguna masih berbicara (NFR-07).
     - `final_transcript`: Transkrip final setelah endpointing STT.
     - `intent_applied`: Pembaruan keranjang belanja langsung setelah state machine memvalidasi intent (NFR-07).
     - `pending_question`: Pertanyaan slot paket hemat atau modifikasi yang memerlukan jawaban pengguna.
     - `handoff`: Eskalasi ke staf/kru manusia bila terjadi permintaan khusus atau anomali dialog.
     - `bot_reply_text`: Teks ucapan kasir yang sedang/akan diucapkan oleh TTS.
     - `bot_speaking_start` & `bot_speaking_end`: Indikator sinkronisasi visual animasi kasir berbicara.
     - `session_limits`: Pembaruan sisa waktu sesi (hitung mundur 3 menit) dan sisa giliran (maksimal 12 turn).
     - `error`: Notifikasi kegagalan terstruktur.
2. **Kepatuhan Privasi Data (ADR-0005):**
   - Transkrip hanya disimpan di memori komponen browser selama tab sesi aktif.
   - Tidak ada payload audio yang dikirim melalui data channel.
3. **Aksesibilitas & UI Respon Cepat (WCAG AA & NFR-07):**
   - Panel transkrip menggunakan atribut `role="log"` dan `aria-live="polite"` sehingga pembaca layar membaca pembaruan secara alami.
   - Seluruh kontainer yang dapat di-scroll memiliki `tabIndex={0}` untuk navigasi keyboard penuh.
   - Keranjang menampilkan lencana visual (*"Keranjang Diperbarui"*) secara instan ketika intent diterapkan, mengompensasi latensi audio bot.
