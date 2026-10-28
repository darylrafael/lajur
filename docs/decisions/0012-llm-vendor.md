# ADR-0012: Pemilihan Vendor Large Language Model (LLM) untuk Parsing Intent

## Status
Accepted as candidate, subject to Minggu 4 measurement

## Konteks
Sistem voice ordering Lajur membutuhkan Large Language Model (LLM) berkecepatan tinggi yang mampu memetakan ucapan pelanggan ke format intent JSON terstruktur, menangani koreksi pesanan (*undo / ganti item*) secara tepat, menolak injeksi prompt, dan merespons dalam latensi rendah tanpa melanggar kebijakan privasi data pengguna (ADR-0005).

Pada pengukuran ulang G1b (30 skenario representatif) dan addendum G1f (60 skenario baku), dilakukan pengujian streaming Time to First Token (TTFT) dan akurasi pada beberapa model card-free:
1. **Groq-Hosted LLM (`qwen/qwen3.8-27b`, Non-Reasoning):**
   - Model ID Eksak: `qwen/qwen3.8-27b`.
   - Warm TTFT: P50 = **258.5 ms** (G1c burst) / **419.1 ms** (G1f 60 turns, P95 = 574.2 ms).
   - Akurasi Intent: **73.3%**, Akurasi Keranjang Akhir (*Resulting Cart*): **76.7%** (Simple orders: 80.0%, Modifiers: 100.0%).
   - Ketentuan Data Groq: Tidak melatih model pada data API pelanggan (bebas risiko privasi dasar).
2. **Groq-Hosted LLM (`openai/gpt-oss-20b`, Reasoning Effort Low):**
   - Warm TTFT: P50 = **616.6 ms**, Akurasi Keranjang: **56.7%**.
3. **Google Gemini Flash-Lite (Free Tier):**
   - Model ID Eksak: `models/gemini-3.5-flash-lite`.
   - Warm TTFT: P50 = **794.2 ms** (burst) s.d. **7.303 ms** (beban antrean 60 giliran).
   - Akurasi Intent: **73.3%**, Akurasi Keranjang Akhir: **76.7%**.
   - Ketentuan Data Google: Google Free Tier melatih model AI dari input pengguna (melanggar ADR-0005 untuk data pengunjung nyata).

## Keputusan Pemilik Proyek (Owner Decision - Minggu 2g)
1. **Kandidat Utama Diterima:** **Groq-Hosted `qwen/qwen3.8-27b` (Non-Reasoning)** diterima sebagai kandidat utama model LLM (*Accepted as candidate, subject to Minggu 4 measurement*).
2. **Gemini Free Tier Dikeluarkan untuk Data Pengunjung:** Google Gemini Free Tier **eksplisit dilarang menerima data pengunjung riil** karena klausul pelatihan data melanggar ADR-0005. Gemini Free Tier hanya diizinkan untuk data sintetis/skrip internal developer.
3. **Penyelidikan Akurasi & Baseline State Machine:** Akurasi keranjang baseline 76.7% dan intent 73.3% (termasuk penanganan koreksi/undo) diserahkan ke siklus Minggu 3 (Cart State Machine) dan evaluasi komprehensif Minggu 8.

## Alternatif yang Dipertimbangkan
- **OpenAI GPT-4o-mini:** Memerlukan kartu kredit / saldo berbayar (`excluded: card required`).
- **Gemini 2.5 Flash:** Mengalami batas kuota ketat 20 RPD (HTTP 429) pada proyek non-billing.
- **Groq GPT-OSS-20b:** Akurasi keranjang lebih rendah (56.7%) dan TTFT lebih lambat (~616–885 ms).

## Konsekuensi
- Groq API key digunakan sebagai variabel primer di `.env` untuk inferensi intent.
- Model `qwen/qwen3.8-27b` beroperasi dalam mode non-reasoning sehingga menghemat token pemikiran dan merespons dalam < 420 ms.
- Keputusan definitif performa pipeline end-to-end akan diuji pada real pipeline di Minggu 4 sesuai pra-registrasi `docs/gates/G1-minggu4-measurement.md`.

## Hasil Pengukuran Pipeline Nyata Minggu 4 (docs/gates/G1-minggu4-results.md)
Pada pengujian pipeline nyata di Minggu 4:
1. **Performa Parsing Intent:** Groq Qwen-27b berhasil memetakan ucapan pelanggan menjadi intent tervalidasi dengan akurasi 96,7% (Mode 2) dan 93,3% (Mode 1).
2. **Efisiensi Token Prompt:** Pengurangan konteks menu menjadi alias yang relevan dengan ucapan (<20 alias) berhasil menjaga payload inferensi di bawah 600 token per request, menghindari rate limit ITPM 7.000 Groq Free Tier.
3. **Beban Verbalisasi LLM (Mode 1):** Mode verbalisasi menghasilkan tambahan latensi rata-rata +395,5 ms dibandingkan templat deterministik (P50 3.365,3 ms vs 2.969,8 ms) dan menghasilkan balasan kasir percakapan alami yang ringkas tanpa mendeteksi halusinasi menu yang tidak terdapat dalam `SpeechFacts`.

