# ADR-0010: Pemilihan Vendor Speech-to-Text (STT)

## Status
Proposed

## Konteks
Sistem voice ordering Lajur membutuhkan mesin Speech-to-Text (STT) yang mampu mentranskripsikan percakapan bahasa Indonesia bercampur istilah menu bahasa Inggris (*code-switching*) di lingkungan restoran drive-thru dengan akurasi tinggi (Keyterm Error Rate $\le 15\%$) dan latensi rendah.

Pada Spike Minggu 2, dilakukan pengujian terhadap dua kandidat awal:
1. **Groq Whisper Turbo (`whisper-large-v3-turbo`):** Mentranskripsikan audio file batch 20 skenario sintetis dengan Clean KER 11.66%, Noisy KER 13.33%, dan latensi inferensi rata-rata 484.1 ms.
2. **Deepgram Nova-2 (`model=nova-2`, `language=id`, REST baseline):** Menghasilkan Clean KER 15.17%, Noisy KER 20.16%, dan latensi 2,741.1 ms via REST non-streaming.

## Usulan Keputusan
Diusulkan **Groq Whisper Turbo** sebagai kandidat STT primer untuk mode pemrosesan per giliran (turn-based file transcription), dengan catatan:
1. Implementasi pipeline langsung memerlukan penambahan delay deteksi hening VAD (+300–500 ms) sebelum audio file dipotong dan dikirim ke Groq.
2. Pengujian perbandingan definitif terhadap Deepgram belum selesai karena yang diuji adalah model Nova-2 lama tanpa keyterm boosting, bukan Nova-3 dengan `language=id` / `language=multi` dan keyterm boosting seperti yang dispesifikasikan dalam rencana proyek.

## Alternatif yang Dipertimbangkan
- **Deepgram Nova-3 (Streaming WebSocket dengan Keyterm Boosting):** Kandidat kuat yang direncanakan di `PROJECT_PLAN.md` §7.1. Belum diuji secara menyeluruh di Spike Minggu 2.
- **Soniox / Gladia:** Alternatif streaming dengan dukungan native code-switching bahasa Indonesia, dicadangkan untuk pengujian lanjutan.

## Konsekuensi
- **Positif:**
  - Groq Whisper Turbo menunjukkan ketahanan yang baik pada data sintetis berderau Gaussian (KER 13.33%).
  - Kecepatan inferensi file Groq sangat cepat (~484 ms).
- **Negatif / Mitigasi:**
  - Arsitektur berbasis file membutuhkan VAD silence threshold buffer (~400 ms), sehingga menaikkan latensi turn riil.
  - Free Tier Groq dibatasi pada 20 RPM dan 2,000 RPD tanpa SLA ketersediaan komersial.
  - Status keputusan tetap **Proposed** hingga benchmark 100 skenario dan perbandingan streaming Nova-3 dieksekusi.
