# Laporan Verifikasi Fakta Vendor (Oktober 2026)

**Dokumen:** `docs/spikes/vendor-facts-2026-10.md`  
**Tanggal Verifikasi:** 2026-10-15  
**Verifikator:** Implementation Agent (Lajur)  
**Tujuan:** Memvalidasi seluruh klaim vendor di `docs/PROJECT_PLAN.md` §7.1 terhadap dokumentasi dan registri resmi, menghitung ulang model biaya §11.1, serta menetapkan batas operasional demo.

---

## 1. Tabel Verifikasi Klaim Vendor (§7.1)

| Vendor / Komponen | Klaim Awal di Plan (§7.1) | Nilai Terverifikasi Resmi | Sumber URL Resmi | Tanggal Cek | Status |
|---|---|---|---|:---:|:---:|
| **LiveKit Cloud (Build Plan)** | 1.000 mnt agent/bln (hard cap), 5.000 mnt partisipan, maks 5 agent bersamaan | **Terkonfirmasi:** 1.000 mnt agent session/bln, maks 5 concurrent agent sessions, 5 concurrent LiveKit inference sessions. Perilaku hard cap: koneksi baru ditolak (hard stop) saat limit tercapai, tanpa penagihan kartu kredit otomatis. Server open-source mendukung *self-host* penuh (Apache-2.0). | [docs.livekit.io/cloud/billing](https://docs.livekit.io/cloud/billing) / [livekit.io/pricing](https://livekit.io/pricing) | 2026-10-15 | **Confirmed** |
| **livekit-agents (PyPI)** | v1.8.7, Python ≥ 3.10 < 3.15; plugin `deepgram`, `azure`, `google` | **Terkonfirmasi & Diperluas:** Versi Python didukung `Requires-Python: >=3.10, <3.15`. Plugin resmi modular tersedia di PyPI: `livekit-plugins-deepgram`, `livekit-plugins-azure`, `livekit-plugins-google`, `livekit-plugins-cartesia`, `livekit-plugins-elevenlabs`. | [pypi.org/project/livekit-agents](https://pypi.org/project/livekit-agents/) | 2026-10-15 | **Confirmed** |
| **Deepgram Nova-3** | Indonesia (`id`) didukung streaming; `language=multi` TIDAK mencakup Indonesia; keyterm didukung (maks 100); $0,0077/mnt; kredit $200 | **Diperbarui:** Indonesia (`id`) didukung streaming. Pada Nova-3, parameter `language=multi` kini mendukung code-switching bahasa regional termasuk Indonesia. Keyterm boosting mendukung s.d. 100 istilah. Harga streaming $0,0077/mnt ($0,46/jam). Kredit uji coba baru Pay-As-You-Go: $200 (tanpa kedaluwarsa). | [developers.deepgram.com/documentation](https://developers.deepgram.com) / [deepgram.com/pricing](https://deepgram.com/pricing) | 2026-10-15 | **Changed** (kemampuan `language=multi` mencakup Indonesia) |
| **Soniox** | Indonesia didukung; $0,002/mnt | **Diperbarui:** Streaming didukung dengan native code-switching ID–EN. Skema harga token-based: $2,00/1M audio input token, setara ~$0,12/jam (~$0,002/menit). **PENTING:** Soniox telah MENGHAPUS kredit gratis $200 untuk pendaftaran API baru karena isu abuse/spam; pengguna baru wajib pay-as-you-go langsung. | [soniox.com/pricing](https://soniox.com/pricing) / [soniox.com/docs](https://soniox.com/docs) | 2026-10-15 | **Changed** (tidak ada free credit API) |
| **Gladia** | Indonesia + code-switching; ±$0,0125/mnt; kredit ~€50 | **Terkonfirmasi:** Mendukung native intra-sentential code-switching ID–EN (Solaria-1 model). Harga real-time streaming WebSocket: $0,75/jam ($0,0125/menit). Kredit gratis pendaftaran baru: €50. Concurrency starter: 30 real-time streams. | [gladia.io/pricing](https://www.gladia.io/pricing) / [docs.gladia.io](https://docs.gladia.io) | 2026-10-15 | **Confirmed** |
| **Azure Speech TTS** | Gadis/Ardi aktif; F0: 500 rb karakter/bln, hanya 1 request bersamaan; S0: $16/1 jt karakter | **Terkonfirmasi:** Suara Neural aktif: `id-ID-GadisNeural`, `id-ID-ArdiNeural`. F0 gratis 500.000 karakter/bulan dengan batas ketat 20 transaksi/60 detik (HTTP 429 jika paralel). S0 Pay-As-You-Go: $15–$16 per 1 juta karakter Neural voice. | [azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/) | 2026-10-15 | **Confirmed** |
| **Cartesia (Sonic)** | Indonesia didukung; free tier non-komersial; berbayar mulai $5/bln | **Terkonfirmasi:** Sonic 3.x mendukung Bahasa Indonesia (latensi < 90ms). Konsumsi ~1 credit/karakter. Tier berbayar mulai dari $5/bulan. Estimasi harga efektif ~$24–$40 per 1M karakter. | [cartesia.ai/pricing](https://cartesia.ai/pricing) | 2026-10-15 | **Confirmed** |
| **ElevenLabs (Flash v2.5)** | Alternatif TTS | **Terkonfirmasi:** Model `eleven_flash_v2_5` mendukung Bahasa Indonesia (latensi < 75ms). Skema Flash mengenakan diskon 50% (0,5 kredit per karakter). Tier berbayar starter mulai $5/bulan. Estimasi harga API ~$0,04 per 1.000 karakter ($40 per 1M karakter). | [elevenlabs.io/pricing](https://elevenlabs.io/pricing) | 2026-10-15 | **Confirmed** |
| **Google Gemini** | `gemini-2.0-flash` sudah pensiun (1 Jun 2026); free tier melatih dengan data prompt; nama model terbaru harus dicek | **Terkonfirmasi & Diperbarui:** Varian aktif: `gemini-2.5-flash-lite` ($0,10/1M input, $0,40/1M output), `gemini-2.5-flash` ($0,30/1M input, $2,50/1M output). **Ketentuan Data:** Free tier Google AI Studio menggunakan data prompt untuk training produk Google. Tier berbayar (Pay-as-you-go dengan billing Cloud tertaut) **TIDAK MENGGUNAKAN** data prompt/respons untuk training model. | [ai.google.dev/pricing](https://ai.google.dev/pricing) / [ai.google.dev/terms](https://ai.google.dev/gemini-api/terms) | 2026-10-15 | **Changed** (nama model spesifik 2.5 Flash-Lite) |
| **OpenAI GPT-4o-mini** | $0,15 / $0,60 per 1M token; function calling andal | **Terkonfirmasi:** $0,15 per 1M input token, $0,60 per 1M output token. Cached input $0,075 per 1M token. Function calling JSON mode sangat stabil. | [openai.com/api/pricing](https://openai.com/api/pricing/) | 2026-10-15 | **Confirmed** |
| **Groq Whisper** | Baseline STT open pembanding | **Terkonfirmasi:** `whisper-large-v3` seharga ~$0,111/jam (~$0,00185/menit), `whisper-large-v3-turbo` seharga ~$0,04/jam (~$0,00067/menit). Free tier rate limit: 20 RPM, 2.000 RPD. | [groq.com/pricing](https://groq.com/pricing/) | 2026-10-15 | **Confirmed** |
| **Cloudflare Turnstile** | Free tier captcha demo | **Terkonfirmasi:** $0 (Free) tanpa batas kuota permintaan harian (unlimited requests), maksimal 20 widget sitekey per akun. | [cloudflare.com/products/turnstile](https://www.cloudflare.com/products/turnstile/) | 2026-10-15 | **Confirmed** |
| **Sentry** | Free tier monitoring | **Terkonfirmasi:** Developer plan ($0/bulan) mencakup 5.000 error/bulan, 10.000 transaction/bulan, retensi 30 hari, 1 kursi pengguna. | [sentry.io/pricing](https://sentry.io/pricing/) | 2026-10-15 | **Confirmed** |
| **Hosting (Vercel vs Cloudflare Pages)** | Frontend hosting | **PENTING (Perubahan Kebijakan):** Vercel Hobby Plan secara tegas **melarang penggunaan komersial / bisnis**. Sebaliknya, **Cloudflare Pages Free Tier sepenuhnya mengizinkan penggunaan komersial** (unlimited requests, 500 build/bulan). Rekomendasi: Frontend di-deploy di Cloudflare Pages agar aman dari pelanggaran lisensi jika berkembang ke tahap startup. | [vercel.com/legal/terms](https://vercel.com/legal/terms) / [cloudflare.com/pages](https://pages.cloudflare.com/) | 2026-10-15 | **Changed** (pilih Cloudflare Pages) |
| **Lisensi Dataset: MUSAN** | Sumber noise CC0/CC-BY | **Terkonfirmasi:** OpenSLR SLR17 dirilis seragam di bawah lisensi **Creative Commons Attribution 4.0 International (CC BY 4.0)**. | [openslr.org/17](https://www.openslr.org/17/) | 2026-10-15 | **Confirmed** |
| **Lisensi Dataset: FSD50K** | Sumber noise CC-BY | **Terkonfirmasi:** **Per-clip licenses** (setiap file audio memiliki lisensinya sendiri dari uploader Freesound: CC0, CC-BY, CC-BY-NC). Untuk rilis publik dataset Lajur, hanya klip dengan metadata CC0 atau CC-BY yang boleh diekstrak. Klip bertag NC (Non-Commercial) atau Sampling+ dilarang dipakai. | [zenodo.org/records/4060432](https://zenodo.org/records/4060432) | 2026-10-15 | **Confirmed** (wajib filter metadata lisensi per klip) |

---

## 2. Kalkulasi Ulang Model Biaya (§11.1)

### Parameter Sesi Baku (Durasi 3 Menit)
- **Durasi Sesi:** 3 menit audio streaming.
- **Turn Percakapan:** Rata-rata 6–8 turns.
- **Konsumsi Token LLM:** ~5.000 token input (system prompt + riwayat), ~600 token output (intent JSON ringkas).
- **Karakter Respons TTS:** ~600 karakter audio balasan kasir.

### Rincian Biaya per Sesi (Varian Baseline Utama):
1. **STT (Soniox Streaming):** 3 menit × $0,002/menit = **$0,0060**
2. **LLM (Gemini 2.5 Flash-Lite Paid Tier):**
   - Input: 5.000 / 1.000.000 × $0,10 = $0,0005
   - Output: 600 / 1.000.000 × $0,40 = $0,00024
   - Subtotal LLM = **$0,00074**
3. **TTS (Azure Speech S0 `id-ID-GadisNeural`):**
   - 600 karakter / 1.000.000 × $16,00 = **$0,0096**
4. **Total Biaya Variabel per Sesi = $0,01634 (~$0,016)**

### Rincian Biaya Varian Alternatif:
- **Varian Deepgram + GPT-4o-mini + Azure S0:**
  $0,0231 (STT Deepgram) + $0,00111 (LLM 4o-mini) + $0,0096 (TTS) = **$0,0338 (~$0,034)**
- **Varian Gladia + Gemini 2.5 Flash-Lite + Azure S0:**
  $0,0375 (STT Gladia) + $0,00074 (LLM) + $0,0096 (TTS) = **$0,0478 (~$0,048)**

---

## 3. Kapasitas & Batas Operasional LiveKit Build Plan

- **Batas Bulanan:** 1.000 menit sesi agen / bulan.
- **Estimasi Sesi Bulanan (Durasi 3 Menit):** 1.000 / 3 = **333 sesi per bulan**.
- **Estimasi Sesi Bulanan jika Durasi Dibatasi 2,5 Menit (150 detik):** 1.000 / 2,5 = **400 sesi per bulan**.
- **Kuota Harian yang Disarankan:** Maksimal **11 sesi / hari** (untuk durasi 3 menit) atau **13 sesi / hari** (untuk durasi 2,5 menit).
- **Perilaku Overage:** Tidak ada kejutan tagihan pada kartu kredit. Sesi ke-1.001 akan langsung ditolak sistem (*hard stop*).
