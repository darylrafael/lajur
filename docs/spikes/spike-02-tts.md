# Spike 02 Report: Text-to-Speech (TTS) Streaming & Latency Benchmark Results

**Document:** `docs/spikes/spike-02-tts.md`  
**Milestone:** Minggu 2 — Gate G1  
**Status:** Executed (Prototype Spike; Vendor Decision OPEN)  
**Author:** Daryl (Solo Dev) & Implementation Agent  
**Execution Date:** 2026-10-19  

---

## 1. Goal and Questions

**Core Question:** Which TTS engine produces high naturalness for Indonesian-English food terms while keeping Time to First Audio (TTFB) responsive, maintaining a Real-Time Factor (RTF) $< 1.0$, and conforming to product production standards?

**Engine Evaluated in Prototype:**
1. **Edge-TTS (`id-ID-GadisNeural` & `id-ID-ArdiNeural`):** Evaluated strictly as a local prototype harness.  
   > [!WARNING]
   > **Edge-TTS adalah wrapper tidak resmi (*unofficial reverse-engineered wrapper*) terhadap layanan browser Microsoft Edge.** Audio yang dihasilkan **BUKAN dari Azure Cognitive Services Speech API resmi**. Layanan ini tidak memiliki jaminan SLA, dapat diblokir atau di-throttle oleh Microsoft kapan saja tanpa pemberitahuan, dan **TIDAK DISETUJUI UNTUK PRODUK (PROTOTYPE ONLY, NOT APPROVED FOR PRODUCT)**.

---

## 2. Test Utterances & Evaluation Methodology

Korpus pengujian terdiri dari **18 respons kasir drive-thru realistis** yang diuji pada kedua suara (total 36 iterasi streaming) terbagi dalam 4 tier kompleksitas:
- **Tier 1: Short Acknowledgment (1–5 kata, 15–35 karakter):** *"Baik kak, satu burger sapi."*, *"Siap, tanpa es ya kak."*
- **Tier 2: Medium Confirmation & Upsell (8–15 kata, 50–95 karakter):** *"Baik kak, 1 Paket Hemat Burger Sapi. Mau sekalian upgrade minumannya ke ukuran besar?"*
- **Tier 3: Long Multi-item & Total Bill (18–30 kata, 110–190 karakter):** *"Baik kak, total pesanannya: 1 Double Cheeseburger, 1 Ice Cream Sundae, dan 1 Chicken Nuggets 6 pieces. Totalnya tiga puluh sembilan ribu rupiah."*
- **Tier 4: Bilingual / Code-switching Terms (10–22 kata, 60–140 karakter):** *"Baik kak, 1 triple cheeseburger no onions with french fries and iced lemon tea."*

---

## 3. Results Summary Table

| Evaluated Voice | TTFB P50 (ms) | TTFB P95 (ms) | Mean Total Latency (ms) | Mean Real-Time Factor (RTF) | Status Layanan |
|---|:---:|:---:|:---:|:---:|:---:|
| **GadisNeural (Female)** | **1,938.8 ms** | **3,154.0 ms** | **2,969.2 ms** | **0.44x** | Prototipe tidak resmi (Unapproved) |
| **ArdiNeural (Male)** | 1,951.8 ms | 3,381.7 ms | 3,005.0 ms | 0.54x | Prototipe tidak resmi (Unapproved) |

### Rincian Performa per Tier Kalimat (GadisNeural)

| Kategori Kalimat Kasir | Rata-rata TTFB (ms) | Rata-rata Total Latensi (ms) | Durasi Audio Bicara (detik) | Real-Time Factor (RTF) |
|---|:---:|:---:|:---:|:---:|
| **Tier 1: Acknowledgment Pendek (1–5 kata)** | **1,406.0 ms** | **1,753.7 ms** | 3.48 detik | 0.51x |
| **Tier 2: Konfirmasi Sedang & Upsell (8–15 kata)** | **2,102.5 ms** | **3,129.4 ms** | 7.15 detik | 0.43x |
| **Tier 3: Ringkasan Panjang & Total Bayar (18–30 kata)**| **2,635.9 ms** | **4,766.9 ms** | 12.35 detik | 0.38x |
| **Tier 4: Istilah Campur Indo–Inggris (Code-Switching)** | **2,106.4 ms** | **2,490.8 ms** | 6.18 detik | 0.41x |

---

## 4. Analisis Teknis (What & Why)

### 4.1 Real-Time Factor (RTF 0.44x) & Kecepatan Sintesis
- **Nilai RTF 0.44x** menunjukkan bahwa engine menyintesis audio 2.3x lebih cepat daripada durasi pemutaran audio.
- Begitu chunk audio pertama tiba di speaker, buffer audio berikutnya masuk lebih cepat daripada laju konsumsi pemutaran suara.

### 4.2 Analisis Latensi TTFB (~1.4s – 2.6s)
- **Faktor Overhead**:
  1. *Handshake TLS & WebSocket Baru*: Setiap permintaan membuka koneksi WebSocket baru ke endpoint browser gateway, memakan waktu ~800–1,200 ms.
  2. *Buffer Frame Audio Awal*: Menunggu header sinkronisasi frame MP3 pertama.
- Latensi TTFB 1.4s – 2.6s ini menjadi penyumbang terbesar kegagalan batas latensi turn Gate G1 ($\le 1.2$s) jika digabungkan dengan STT dan LLM.

---

## 5. What the Data Cannot Tell Us

1. **Keandalan Akses Tanpa Pemblokiran:** Pengujian lokal berjalan untuk 36 panggilan terpisah. Data ini tidak menjamin apakah Microsoft akan memblokir alamat IP (HTTP 403/429) ketika sistem di-deploy ke server cloud publik dengan lonjakan trafik.
2. **Kinerja Audio Azure Resmi:** Data ini berasal dari layanan browser read-aloud, bukan Azure Cognitive Services Speech SDK resmi dengan endpoint region Asia Tenggara (mis. Southeast Asia / East Asia). Latensi resmi Azure Speech dengan persistent connection belum terukur.
3. **Alternatif Vendor Rendah Latensi Belum Diuji:** Vendor streaming TTS ultra-rendah latensi seperti Cartesia Sonic (est. TTFB < 100 ms) atau ElevenLabs Flash belum diukur pada korpus respons kasir ini karena ketiadaan kunci API.
4. **Sampel Terbatas:** 18 teks respons tidak mencakup seluruh variasi nama menu dan kombinasi harga rupiah yang mungkin terjadi dalam sesi dialog panjang.

---

## 6. Status Keputusan Vendor TTS: OPEN

Keputusan arsitektur untuk TTS dicatat dalam **ADR-0011 dengan status "Proposed / OPEN"**.

### Syarat untuk Menutup Keputusan TTS:
Keputusan pemilihan komponen TTS resmi baru dapat ditutup jika salah satu dari dua kondisi berikut terpenuhi:
1. **Pilihan Resmi:** Disediakannya kunci API resmi Azure Cognitive Services Speech (tier S0 Pay-As-You-Go) atau kunci API vendor alternatif (Cartesia / ElevenLabs) untuk integrasi resmi; **ATAU**
2. **Pilihan Tak Resmi:** Keputusan tertulis eksplisit dari Daryl untuk secara sadar menerima risiko penggunaan wrapper tidak resmi (*Edge-TTS*) untuk demo publik.

*Agen pengembang tidak berwenang memutuskan atau mengunci pilihan ini tanpa instruksi langsung dari Daryl.*
