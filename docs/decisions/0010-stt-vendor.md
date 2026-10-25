# ADR-0010: Pemilihan Vendor Speech-to-Text (STT)

## Status
Accepted as candidate, subject to Minggu 4 measurement

## Konteks
Sistem voice ordering Lajur membutuhkan mesin Speech-to-Text (STT) yang mampu mentranskripsikan percakapan bahasa Indonesia bercampur istilah menu bahasa Inggris (*code-switching*) di lingkungan restoran drive-thru dengan akurasi tinggi (Keyterm Error Rate $\le 15\%$) dan latensi rendah.

Pada Spike Minggu 2 (dan audit pengukuran ulang G1b pada 30 skenario representatif), dilakukan pengujian terhadap dua kandidat utama:
1. **Deepgram Nova-3 Streaming (WebSocket + `keyterm` boosting):**
   - Clean KER Mean: **3.89%** (Bootstrap 95% CI: `[0.00%, 8.33%]`).
   - P50 Streaming Latency (diukur dari *true speech end* dengan pacing real-time $1.0\times$): **524.4 ms** (P95: 856.2 ms, Mean: 549.4 ms).
   - Parameter query yang didukung adalah `keyterm` (parameter `keywords` tidak didukung / error 400).
2. **Groq Whisper Turbo (`whisper-large-v3-turbo`):**
   - Clean KER Mean: **11.11%** (Bootstrap 95% CI: `[4.99%, 18.33%]`).
   - Raw Inference Latency P50: **490.2 ms** (P95: 769.3 ms).
   - Effective Pipeline Latency (+500 ms LiveKit endpointing clamp): P50 **990.2 ms**.

Uji paired bootstrap pada selisih KER per-utterance menghasilkan $\bar{\Delta} = -7.22\%$ dengan 95% CI `[-15.0%, 0.0%]`. Karena selang menyentuh 0.0%, keunggulan statistik belum signifikan mutlak pada $n=30$.

## Keputusan
**Deepgram Nova-3 Streaming diterima sebagai kandidat utama (*primary candidate*)**, dengan status kelulusan akhir bergantung pada pengukuran end-to-end pada pipeline nyata di Minggu 4 ([`docs/gates/G1-minggu4-measurement.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/gates/G1-minggu4-measurement.md)):
- Deepgram Nova-3 Streaming unggul dalam akurasi istilah menu (*code-switching*) dengan KER 3.89% dan beroperasi native streaming via WebSocket tanpa membutuhkan akumulasi rekaman audio utuh sebelum pengiriman.
- Groq Whisper Turbo dipertahankan sebagai kandidat fallback offline/batch jika terjadi kendala pada koneksi WebSocket Deepgram.

## Alternatif yang Dipertimbangkan
- **Soniox:** Dikeluarkan dari pertimbangan (*excluded: card required*) karena mewajibkan kartu kredit untuk aktivasi API.
- **Gladia:** Menyediakan kredit uji coba €50 tanpa kartu, dicadangkan untuk pengujian komparatif lanjutan jika diperlukan.

## Konsekuensi & Hal yang Belum Dapat Diputuskan
- **Akurasi Suara Manusia Nyata:** Masih berstatus *provisional* karena pengujian representatif baru dilakukan pada audio sintetis ($n=30$); pengujian audio manusia nyata baru $n=1$ (hanya latensi, akurasi belum diukur).
- **Keputusan Arsitektur:** Menunggu keputusan Daryl mengenai apakah sistem akan memprioritaskan latensi pipeline (Groq Whisper Turbo + optimasi VAD) atau memprioritaskan native streaming WebSocket (Deepgram Nova-3).

## Hasil Pengukuran Pipeline Nyata Minggu 4 (docs/gates/G1-minggu4-results.md)
Pada benchmark pra-registrasi Gate G1 di Minggu 4 yang dijalankan pada pipeline LiveKit WebRTC riil (30 skenario × 2 mode balasan = 60 turns):
1. **Endpointing & Turnaround STT:** Konfigurasi `endpointing=500` menghasilkan median turnaround STT (diukur dari akhir ucapan fisik skrip hingga `speech_final=True`) sebesar **P50 = 1.393,5 ms**.
2. **False Cutoff Rate:** Terukur **0,0%** (tidak ada pemotongan ucapan prematur di tengah kalimat).
3. **Akurasi Pengenalan Intent:** Mencapai **96,7%** (Mode 2: Templat) dan **93,3%** (Mode 1: LLM Verbalization). Akurasi keranjang akhir (*resulting cart*) mencapai 100,0% pada kategori kuantitas/kombo dan 87,5% pada kategori sederhana serta modifier.
4. **Keandalan Koneksi:** Deepgram WebSocket diinisialisasi per-turn dalam sesi WebRTC, menghasilkan deteksi batas ucapan yang bersih tanpa kebocoran state antar-giliran.
