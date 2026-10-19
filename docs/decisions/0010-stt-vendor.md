# ADR-0010: Pemilihan Vendor Speech-to-Text (STT)

## Status
Proposed

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

## Usulan Keputusan
Status pemilihan vendor STT tetap berstatus **Proposed** (belum definitif):
- **Deepgram Nova-3 Streaming** unggul dalam akurasi pengenalan istilah menu (*code-switching*) dengan KER 3.89% dan beroperasi native streaming via WebSocket dengan latensi dari akhir bicara ~524 ms.
- **Groq Whisper Turbo** beroperasi berbasis batch file/REST dengan latensi inferensi ~490 ms, tetapi membutuhkan jeda endpointing VAD (~500 ms) sebelum file dapat dipotong dan dikirim ke server.

## Alternatif yang Dipertimbangkan
- **Soniox:** Dikeluarkan dari pertimbangan (*excluded: card required*) karena mewajibkan kartu kredit untuk aktivasi API.
- **Gladia:** Menyediakan kredit uji coba €50 tanpa kartu, dicadangkan untuk pengujian komparatif lanjutan jika diperlukan.

## Konsekuensi & Hal yang Belum Dapat Diputuskan
- **Akurasi Suara Manusia Nyata:** Masih berstatus *provisional* karena pengujian representatif baru dilakukan pada audio sintetis ($n=30$); pengujian audio manusia nyata baru $n=1$ (hanya latensi, akurasi belum diukur).
- **Keputusan Arsitektur:** Menunggu keputusan Daryl mengenai apakah sistem akan memprioritaskan latensi pipeline (Groq Whisper Turbo + optimasi VAD) atau memprioritaskan native streaming WebSocket (Deepgram Nova-3).
