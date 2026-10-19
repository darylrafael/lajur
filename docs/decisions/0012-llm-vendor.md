# ADR-0012: Pemilihan Vendor Large Language Model (LLM) untuk Parsing Intent

## Status
Proposed

## Konteks
Sistem voice ordering Lajur membutuhkan Large Language Model (LLM) berkecepatan tinggi yang mampu memetakan ucapan pelanggan ke format intent JSON terstruktur, menangani koreksi pesanan (*undo / ganti item*) secara tepat, menolak injeksi prompt, dan merespons dalam latensi rendah tanpa melanggar kebijakan privasi data pengguna (ADR-0005).

Pada Spike Minggu 2, dilakukan pengujian terhadap varian Google Gemini:
1. **Google Gemini 2.5 Flash:** Mengalami kegagalan HTTP 429 (`RESOURCE_EXHAUSTED`) pada seluruh 20 panggilan pengujian karena batas ketat tier gratis (20 permintaan per hari).
2. **Google Gemini Flash-Lite (`gemini-flash-lite-latest` / `gemini-3.1-flash-lite`):** Berhasil memproses 20 skenario sintetis dengan akurasi intent 100.0%, kepatuhan skema JSON 100.0%, penolakan injeksi harga 100.0%, dan rata-rata latensi REST 1,072.9 ms.

## Usulan Keputusan
Diusulkan **Google Gemini Flash-Lite** sebagai vendor LLM primer untuk dialog dan ekstraksi intent, dengan **persyaratan mutlak arsitektur**:
1. **Wajib Tier Berbayar (Pay-As-You-Go):** Untuk demo publik maupun rilis produk, Gemini **DILARANG MENGGUNAKAN FREE TIER**. Sesuai Terms of Service Google AI Studio, Free Tier menggunakan prompt dan output untuk melatih model AI Google serta dapat ditinjau oleh reviewer manusia—hal ini melanggar secara fatal kebijakan privasi biometrik/percakapan pada **ADR-0005 (Zero Audio/Transcript Persistence)**. Penggunaan tier berbayar menjamin data percakapan pelanggan tidak disimpan atau digunakan untuk pelatihan.
2. **Implementasi Streaming:** Wajib menerapkan streaming SSE (`stream_generate_content`) pada implementasi agen untuk memangkas dan mengukur Time to First Token (TTFT), yang belum terukur pada Spike Minggu 2.

## Alternatif yang Dipertimbangkan
- **OpenAI GPT-4o-mini:** Alternatif baseline terpercaya ($0.15 / $0.60 per 1M token) dengan jaminan kepatuhan privasi API komersial.

## Konsekuensi
- **Positif:**
  - Biaya operasional Gemini Flash-Lite sangat murah ($0.10 input / $0.40 output per 1M token).
  - Penalaran temporal pada koreksi kalimat (*speech correction*) dan ketahanan injeksi prompt terbukti baik pada 20 skenario uji.
- **Negatif / Mitigasi:**
  - Membutuhkan penautan kartu kredit / Google Cloud Billing aktif untuk mengaktifkan pay-as-you-go dan menonaktifkan data training Google.
  - Perlu memonitor kuota TPM/RPM dan menyiapkan failover adapter ke OpenAI GPT-4o-mini jika terjadi downtime.
