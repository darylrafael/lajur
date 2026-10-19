# ADR-0012: Pemilihan Vendor Large Language Model (LLM) untuk Parsing Intent

## Status
Proposed

## Konteks
Sistem voice ordering Lajur membutuhkan Large Language Model (LLM) berkecepatan tinggi yang mampu memetakan ucapan pelanggan ke format intent JSON terstruktur, menangani koreksi pesanan (*undo / ganti item*) secara tepat, menolak injeksi prompt, dan merespons dalam latensi rendah tanpa melanggar kebijakan privasi data pengguna (ADR-0005).

Pada pengukuran ulang G1b (30 skenario representatif), dilakukan pengujian streaming Time to First Token (TTFT) dan Time to First Complete Sentence pada dua kandidat card-free:
1. **Google Gemini Flash-Lite (Free Tier):**
   - Model ID Eksak yang Melayani: `models/gemini-3.5-flash-lite` (via alias `gemini-flash-lite-latest`).
   - Time to First Token (TTFT): P50 = **840.1 ms** (Mean = 876.3 ms, P95 = 1,071.1 ms).
   - Time to First Sentence: P50 = **841.4 ms**.
   - Total Response Time: P50 = **952.9 ms**.
2. **Groq-Hosted LLM (`openai/gpt-oss-20b`):**
   - Model ID Eksak yang Melayani: `openai/gpt-oss-20b`.
   - Time to First Token (TTFT): P50 = **748.3 ms** (Mean = 750.1 ms, P95 = 879.0 ms).
   - Time to First Sentence: P50 = **748.3 ms**.
   - Total Response Time: P50 = **750.5 ms**.
   - Ketentuan Data Groq: Tidak melatih model pada data API pelanggan (bebas risiko privasi dasar).

## Usulan Keputusan
Diusulkan dua kandidat berstatus **Proposed**:
1. **Groq-Hosted LLM (`openai/gpt-oss-20b`):** Kandidat kuat untuk mode card-free yang aman dari risiko pelatihan data pelanggan (Groq terms exclude training on API inputs) dengan TTFT 748 ms.
2. **Google Gemini Flash-Lite:** Berkinerja baik untuk inferensi intent pada teks skrip/sintetis (TTFT 840 ms). Namun, karena pengembang menetapkan batasan mutlak tanpa kartu kredit (tidak mengaktifkan Pay-as-You-Go), **Gemini Free Tier hanya diizinkan untuk data sintetis/skrip internal**. Data pengunjung riil dilarang dikirim ke Gemini Free Tier karena klausul pelatihan data Google melanggar ADR-0005.

## Alternatif yang Dipertimbangkan
- **OpenAI GPT-4o-mini:** Memerlukan kartu kredit / saldo berbayar (`excluded: card required`).
- **Gemini 2.5 Flash:** Mengalami batas kuota ketat 20 RPD (HTTP 429) pada proyek non-billing.

## Konsekuensi
- **Positif:**
  - Keduanya beroperasi 100% tanpa kewajiban kartu kredit (*card-free*) untuk tahap evaluasi.
  - Streaming First Sentence memungkinkan pemotongan kalimat pertama (~750–840 ms) untuk langsung dialirkan ke TTS sebelum JSON lengkap selesai.
- **Negatif / Mitigasi:**
  - Untuk demo publik dengan pengunjung nyata, hanya model yang ketentuannya secara tegas mengecualikan pelatihan data (seperti Groq API) yang boleh menerima transkrip pengguna.
