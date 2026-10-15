# ADR-0004: Isolasi Provider Vendor STT/LLM/TTS di Balik Adapter Interface

## Status
Accepted

## Konteks
Lanskap penyedia layanan AI (Speech-to-Text, Large Language Models, dan Text-to-Speech) berkembang sangat pesat. Vendor kerap mengubah skema harga, model usang didepresiasi (seperti `gemini-2.0-flash` yang dipensiunkan), performa bahasa lokal berbeda-beda antar-region, dan beberapa vendor berisiko mengalami kendala kuota atau downtime mendadak. 

Jika kode inti logika percakapan mengimpor SDK vendor secara langsung, migrasi vendor atau pengujian benchmark multi-vendor akan memerlukan *refactoring* masif.

## Keputusan
Menerapkan pola desain **Adapter (Ports and Adapters / Hexagonal Architecture)** untuk seluruh komponen vendor AI:
1. `STTProvider`: Interface streaming transkripsi audio &rarr; teks dengan event callback (`on_interim_transcript`, `on_final_transcript`). Implementasi: `DeepgramAdapter`, `SonioxAdapter`, `GladiaAdapter`, `GroqWhisperAdapter`.
2. `LLMProvider`: Interface inferensi chat & function-calling &rarr; intent JSON. Implementasi: `GeminiAdapter`, `OpenAIAdapter`.
3. `TTSProvider`: Interface sintesis teks &rarr; audio chunk streaming. Implementasi: `AzureTTSAdapter`, `CartesiaAdapter`, `ElevenLabsAdapter`.

Pilihan provider diatur secara dinamis melalui konfigurasi environment variable tanpa mengubah kode orkestrasi pipeline.

## Alternatif yang Ditolak
- **Mengikat Langsung ke SDK Vendor Tertentu**: Ditolak karena menciptakan *vendor lock-in* dan mempersulit pengujian *mocking* dalam CI/CD.
- **Menggunakan Abstraksi All-in-One Global yang Terlalu Kaku**: Ditolak karena menghilangkan akses ke parameter khusus vendor (misal pengaturan `keyterms` pada Deepgram atau parameter aksen pada Azure Speech).

## Konsekuensi
- **Positif:**
  - Kemudahan menjalankan uji benchmark Gerbang G1 (Minggu 2) pada dataset yang sama secara adil.
  - Mitigasi cepat jika vendor mengalami downtime atau perubahan ketentuan harga (cukup ganti environment flag).
  - Memungkinkan penggunaan *Mock Provider* untuk unit/integration testing offline tanpa biaya API.
- **Negatif / Mitigasi:**
  - Diperlukan penulisan antarmuka wrapper per vendor. Namun cakupan interface sangat sempit dan dapat diuji dengan contract test sederhana.
