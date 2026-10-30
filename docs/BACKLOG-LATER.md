# Backlog Fitur & Usulan Lanjutan (Backlog Later)

Dokumen ini mencatat usulan fitur, perbaikan arsitektur, dan optimasi biaya yang ditunda ke fase mendatang atau pasca-Minggu 5.

---

## Usulan 1: Mode Balasan Teks-Saja (TTS_MODE=none)

- **Status:** PROPOSED (Diusulkan pada Minggu 5d, belum diimplementasikan).
- **Konsep Teknis:**
  Menambahkan variabel lingkungan `TTS_MODE="elevenlabs" | "none"` (atau adapter `NoOpTTSAdapter`). Bila disetel ke `"none"`, pipeline worker melewatkan tahap sintesis suara ElevenLabs (`audio_bytes = b""`), namun tetap memproses mutasi keranjang dan menyiarkan event `type: "bot_reply_text"` serta `intent_applied` melalui WebRTC Data Channel (`lajur-control`). Antarmuka web tetap menampilkan balasan kasir pada komponen `BotReplyCard` dan riwayat transkrip secara visual seketika.
- **Penghematan Karakter & Biaya Vendor:**
  - Konsumsi karakter ElevenLabs: **0 karakter ($0.00)** untuk setiap turn percakapan.
  - Menghemat 100% sisa kuota ElevenLabs (1.576 karakter) dan menghilangkan risiko batas kuota habis selama showcase portofolio publik.
- **Dampak terhadap Validitas Uji Usability (Trade-Off):**
  - **Penurunan Validitas Uji Ketergunaan:** Partisipan tidak dapat mendengar respon suara kasir (*auditory feedback loop* terputus). Pengalaman drive-thru yang dirancang berbasis percakapan lisan berubah menjadi interaksi visual membaca layar. Partisipan awam kemungkinan merasa canggung, tidak menyadari bot telah membalas, atau berbicara tumpang tindih (*talking over*).
  - **Strategi Pelaksanaan yang Diusulkan:** Menjalankan sesi pengujian awal dengan audio penuh (`TTS_MODE=elevenlabs`) selama kuota 1.576 karakter masih mencukupi, lalu mengaktifkan `TTS_MODE=none` sebagai mekanisme *graceful degradation* untuk showcase demo selanjutnya.
