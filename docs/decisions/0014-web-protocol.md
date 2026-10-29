# ADR-0014: Protokol Komunikasi Web Simulator (Web Protocol v1)

## Status
Proposed (2026-10-28)

## Konteks
Pada pencapaian Minggu 4, pipeline percakapan suara telah terbentuk dan diuji. Namun, data channel WebRTC (`"lajur-control"`) hanya mengirimkan event generik tunggal `cart_update` tanpa pemisahan peran status transkripsi, status suara bot, penanganan eskalasi kru (*handoff*), maupun pemantauan kuota batas sesi.

Pada Gerbang G1 ([`docs/gates/G1-final-statement.md`](../gates/G1-final-statement.md)), disepakati persyaratan antarmuka kritis:
> *Web UI WAJIB menampilkan transkrip langsung (live partial transcript) saat pengguna sedang berbicara, dan memperbarui tampilan keranjang di layar secara instan begitu intent selesai diaplikasikan oleh state machine.*

Untuk memenuhi NFR-07 (aksesibilitas, transkrip selalu tampil), NFR-03 (batas sesi 3 menit, batas turn 12), serta mendukung mode simulasi replay offline tanpa ketergantungan LiveKit/vendor, sistem memerlukan kontrak protokol pesan terstruktur dengan skema tipe yang jelas.

---

## Keputusan

Sistem mendefinisikan dan menerapkan **Web Protocol v1**:
1. **Transport & Topik:**
   - Berjalan di atas WebRTC Data Channel dengan topik `"lajur-control"` pada sesi LiveKit aktif.
   - Menggunakan serialisasi JSON UTF-8.
   - Mendukung mode *offline replay* di mana urutan event yang sama dapat diputar ulang dari file rekaman JSON di browser tanpa koneksi WebRTC.
2. **Pola Pesan Terversi (*Versioned Message Pattern*):**
   - Setiap pesan downstream (agen ke klien) menyertakan field wajib `version: "v1"` dan `type: string`.
3. **Katalog Event Downstream:**
   - `partial_transcript`: teks sementara dari STT streaming saat pengguna berbicara.
   - `final_transcript`: teks final ucapan pengguna setelah jeda endpointing.
   - `intent_applied`: snapshot keranjang tervalidasi dengan `line_id`, detail modifier, status dialog, dan `speech_facts`.
   - `bot_reply_text`: teks balasan agen yang dibacakan.
   - `bot_speaking_start` & `bot_speaking_end`: penanda sinkronisasi audio bot untuk animasi antarmuka.
   - `pending_question`: pilihan tertunda pada status `awaiting_choice` (slot combo, modifier wajib, ambiguitas).
   - `handoff`: eskalasi ke staf manusia dengan pesan kru.
   - `error`: notifikasi kesalahan sistem/jaringan dengan flag `recoverable`.
   - `session_limits`: pemantauan giliran terpakai (maks 12) dan durasi sesi (maks 180 detik).
4. **Kepatuhan Privasi & Penyimpanan Data (ADR-0005):**
   - **Zero Audio Persistence:** File suara pengguna sama sekali tidak pernah disimpan ke disk atau media persisten manapun. Aliran audio WebRTC diproses secara in-memory lalu dibuang.
   - **Penyimpanan Sisi Agen (Worker):**
     - Basis data telemetri SQLite (`data/turn_events.sqlite3`) hanya mencatat metrik latensi teknis per tahapan, jumlah token, perkiraan biaya, dan tipe mutasi state machine (`intent_type`). **Teks transkrip ucapan pengguna SAMA SEKALI TIDAK DISIMPAN ke dalam SQLite.**
     - Teks transkrip ucapan pengguna hanya berada dalam memori volatil saat diproses menjadi intent JSON dan disiarkan via data channel. Pada log terminal standar worker (`stdout`), ucapan dicetak via `logger.info` untuk observabilitas proses lokal.
     - Retensi data event log dibatasi maksimal 30 hari.
   - **Penyimpanan Sisi Peramban (Browser):**
     - Browser **TIDAK PERNAH** menyimpan transkrip, keranjang, audio, atau riwayat percakapan ke dalam `localStorage`, `sessionStorage`, maupun cookies.
     - Satu-satunya data persisten di `localStorage` adalah preferensi bahasa antarmuka (`lajur_locale` bernilai `"id"` atau `"en"`).
     - Seluruh transkrip langsung dan riwayat percakapan bersifat efemeral (*in-memory React state*) dan terhapus total begitu tab peramban dimuat ulang (*refresh*) atau ditutup.

---

## Alternatif yang Ditolak

1. **WebSocket Kustom Terpisah dari WebRTC:**
   - *Alasan ditolak:* Menambah port/koneksi jaringan baru, membutuhkan server HTTP tambahan, serta memecah sinkronisasi state antara audio WebRTC dan data keranjang. Data channel bawaan LiveKit menjamin multiplexing pada koneksi PeerConnection yang sudah ada.
2. **Menggabungkan Semua Data ke dalam Satu Event Monolitik `state_change`:**
   - *Alasan ditolak:* Menghalangi pengiriman transkrip parsial berfrekuensi tinggi (low latency) secara independen dari snapshot keranjang yang berukuran lebih besar.
3. **Server-Sent Events (SSE):**
   - *Alasan ditolak:* Komunikasi satu arah, tidak dapat menangani pesan upstream seperti `ping` dan `user_transcript` fallback.

---

## Konsekuensi

### Positif
- **Sinkronisasi Visual Instan:** Klien dapat menampilkan transkrip dan status keranjang seketika, mengompensasi latensi suara cascaded cloud.
- **Dukungan Replay Mode Murni:** Replay player dapat menggunakan skema yang sama persis tanpa adapter data tambahan.
- **Type-Safety End-to-End:** Didefinisikan dalam TypeScript (`apps/web/src/types/protocol.ts`) dan JSON Schema (`packages/cart/web-protocol.schema.json`).

### Negatif / Mitigasi
- Overhead penguraian JSON pada perangkat low-end. *Mitigasi:* Ukuran payload setiap event dijaga sangat ringkas (< 2 KB).
