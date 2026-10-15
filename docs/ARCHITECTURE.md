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
