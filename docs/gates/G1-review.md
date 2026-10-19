# Gate G1 Review: Speech Viability Decision Record

**Document:** `docs/gates/G1-review.md`  
**Milestone:** End of Minggu 2 (Gerbang G1)  
**Status:** FAIL / NOT PASS (Latency Threshold Not Met; STT Accuracy Provisional)  
**Date:** 2026-10-19  
**Reviewer:** Daryl (Solo Dev) & Implementation Agent  

---

## 1. Exact Gate G1 Criteria (PROJECT_PLAN.md §3.2 Verbatim)

> **Kondisi Kegagalan (Kill / Pivot Trigger):**  
> *"Tidak ada vendor STT dengan KER ≤ 15% pada set ucapan ID–EN bersih dan latensi turn estimasi ≤ 1,2s"*
> 
> **Tindakan jika Gagal:**  
> *"Pivot ke normalisasi LLM pasca-STT atau turunkan klaim (\"mostly Indonesian + English item names\") dan perluas menu dengan alias. Jika tetap gagal: pindah ke bahasa Inggris saja + ID parsial, dan ubah narasi portofolio"*

---

## 2. Evaluation Evidence & Turn Latency Computation

### 2.1 Formula Latensi Turn Estimasi
Sesuai arsitektur *cascade pipeline* (ADR-0001), latensi satu *turn* percakapan dihitung dari akhir pelanggan berbicara hingga audio respons kasir mulai terdengar:

$$\text{Estimated Turn Latency} = \text{STT Time to Final Transcript (incl. VAD/endpointing)} + \text{LLM Time to First Token (TTFT)} + \text{TTS Time to First Audio (TTFB)}$$

### 2.2 Komponen Latensi Terukur (Data Empiris)

1. **STT Time to Final Transcript:**
   - **Groq Whisper Turbo (`whisper-large-v3-turbo`):**
     - Rata-rata inferensi file batch sintetis ($n=20$): **484.1 ms**.
     - Pengujian mikrofon langsung nyata ($n=3$): **749 ms – 946 ms**.
   - **VAD / Endpointing Delay (Wajib untuk vendor berbasis file/batch seperti Groq):**
     - Dalam pipeline percakapan langsung, sistem tidak bisa langsung mengirim audio saat pelanggan berhenti bicara. Dibutuhkan deteksi hening (*silence threshold*) VAD sebesar **+300 ms s.d. 500 ms** (rata-rata ~400 ms) untuk memastikan pelanggan benar-benar selesai berbicara sebelum memotong file audio dan mengirimkannya ke Groq API.
     - Subtotal STT aktual di pipeline langsung: $484\text{ ms} + 400\text{ ms} = \mathbf{884\text{ ms}}$.
   - **Deepgram Nova-2 (`model=nova-2`, REST non-streaming, bukan Nova-3 kandidat plan):**
     - Rata-rata REST sintetis: **2,741.1 ms** (mic nyata: **2,939 ms – 4,276 ms**).

2. **LLM Time to First Token (TTFT):**
   - **Status Pengukuran:** **NOT MEASURED (Belum diukur secara streaming).**
   - Yang terukur sejauh ini adalah inferensi batch REST non-streaming Google Gemini Flash-Lite (`gemini-flash-lite-latest` / `gemini-3.1-flash-lite`) dari pengiriman transkrip hingga seluruh JSON intent selesai terbentuk: rata-rata **1,072.9 ms**.
   - Nilai 1,072.9 ms ini digunakan sebagai batas atas (*upper bound*) hingga pengukuran streaming TTFT dilakukan.

3. **TTS Time to First Audio (TTFB):**
   - **Edge-TTS (`id-ID-GadisNeural`, prototype browser wrapper, unapproved):**
     - Tier 1 (Acknowledgment pendek 1–5 kata): **1,406.0 ms**.
     - Tier 2 (Konfirmasi sedang 8–15 kata): **2,102.5 ms**.
     - Tier 3 (Ringkasan panjang 18–30 kata): **2,635.9 ms**.
     - Median keseluruhan (P50): **1,938.8 ms** (P95: 3,154.0 ms).

### 2.3 Total Estimasi Latensi Turn vs Ambang Batas Plan

| Skenario Turn | STT + VAD Delay | LLM TTFT (Unmeasured, Total REST) | TTS TTFB | Total Turn Latency Estimasi | Ambang Batas Plan (§3.2) | Selisih / Status |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Kandidat Terbaik (Tier 1 Pendek)** | $484\text{ ms} + 300\text{ ms} = 784\text{ ms}$ | $1,072.9\text{ ms}$ | $1,406.0\text{ ms}$ | **3,262.9 ms (~3.26 detik)** | **$\le 1,200\text{ ms}$ (1.2 detik)** | **+2,063 ms (FAIL)** |
| **Median (Tier 2 Konfirmasi)** | $484\text{ ms} + 400\text{ ms} = 884\text{ ms}$ | $1,072.9\text{ ms}$ | $2,102.5\text{ ms}$ | **4,059.4 ms (~4.06 detik)** | **$\le 1,200\text{ ms}$ (1.2 detik)** | **+2,859 ms (FAIL)** |
| **Rentang Paling Lambat (Tier 3 Panjang)** | $946\text{ ms} + 500\text{ ms} = 1,446\text{ ms}$ | $2,611.2\text{ ms}$ | $2,635.9\text{ ms}$ | **6,693.1 ms (~6.69 detik)** | **$\le 1,200\text{ ms}$ (1.2 detik)** | **+5,493 ms (FAIL)** |

**Kesimpulan Latensi:** Latensi *turn-around* estimasi saat ini berada di rentang **3,263 ms – 6,693 ms**, melampaui ambang batas rencana proyek ($\le 1,200\text{ ms}$) sebesar **2.7x hingga 5.5x**.

### 2.4 Faktor yang BELUM Termasuk dalam Perhitungan di Atas
1. **Network RTT dari Browser Pelanggan ke Server:** Latensi WebRTC internet publik Indonesia ke gateway cloud (est. 50–150 ms).
2. **Cart State Machine Processing:** Waktu komputasi deterministik validasi menu, kalkulasi harga, diskon, stok bahan, dan aturan combo.
3. **Barge-in Interruption Handling:** Waktu deteksi suara pelanggan saat bot sedang berbicara, pembatalan audio playback, dan pembersihan buffer pipeline.

---

## 3. Status Evaluasi per Kriteria Gate G1

| No | Kriteria Gate G1 (§3.2) | Target | Hasil Terukur | Status | Alasan Evaluasi |
|:---:|---|:---:|:---:|:---:|---|
| 1 | **Akurasi STT ID–EN Bersih (KER)** | $\le 15.0\%$ | Groq Whisper Turbo: **11.66%** | **PROVISIONAL** | Hasil 11.66% diperoleh dari dataset sintetis $n=20$ skenario (bukan 100 skenario sesuai plan). Pengujian mic nyata baru $n=3$ tanpa transkrip referensi user. Deepgram yang diuji adalah Nova-2 (bukan Nova-3 dengan keyterm boosting). Gold label belum melalui spot-check manusia. |
| 2 | **Latensi Turn Estimasi** | $\le 1,200\text{ ms}$ | Best case: **3,262.9 ms**; Range: **3.3s – 6.7s** | **FAIL** | Latensi melampaui batas toleransi 1.2 detik secara signifikan (2.7x–5.5x lebih lambat dari target). |
| **TOTAL** | **STATUS GERBANG G1** | **PASS ALL** | **1 Provisional, 1 Fail** | **FAIL / NOT PASS** | **Kriteria latensi gagal dipenuhi.** Sesuai tata kelola, gerbang TIDAK LOLOS. |

---

## 4. Opsi Tindakan Fallback Sesuai §3.2 & Rekomendasi

Teks §3.2 menetapkan tindakan berikut saat kriteria G1 tidak terpenuhi:
> *"Pivot ke normalisasi LLM pasca-STT atau turunkan klaim (\"mostly Indonesian + English item names\") dan perluas menu dengan alias. Jika tetap gagal: pindah ke bahasa Inggris saja + ID parsial, dan ubah narasi portofolio"*

### Rekomendasi Teknis untuk Pertimbangan Pengembang (TIDAK DITERAPKAN OTOMATIS):
1. **Mitigasi Latensi STT:** Pindah dari model file-based batch (Groq REST yang membutuhkan VAD silence delay 400ms) ke native streaming WebSocket STT (LiveKit plugin deepgram / Soniox streaming).
2. **Mitigasi Latensi LLM:** Mengaktifkan Server-Sent Events (SSE) streaming pada Gemini Flash-Lite untuk menangkap First Token secara instan (target TTFT < 300 ms) daripada menunggu seluruh JSON selesai.
3. **Mitigasi Latensi TTS:** Menghentikan penggunaan file download buffer; gunakan token-streaming chunking (begitu frasa pertama *"Baik kak,"* selesai di LLM, langsung tembakkan ke TTS).
4. **Keputusan Vendor TTS:** Menutup status TTS dengan kunci API resmi Azure Cognitive Services (S0 Pay-As-You-Go) atau memutuskan opsi alternatif berlisensi resmi.

*Catatan: Seluruh tindakan fallback di atas berstatus REKOMENDASI dan TIDAK DITERAPKAN sebelum ada keputusan tertulis dari Daryl.*

---

## 5. Status Komponen & Vendor Saat Ini (Proposed ADRs)

Seluruh keputusan vendor berstatus **"Proposed"** (bukan definitif) dan dicatat pada dokumen ADR terpisah:
- **STT (ADR-0010 - Status: Proposed):** Groq Whisper Turbo kandidat sementara untuk evaluasi batch, namun terkendala arsitektur file-based (perlu VAD delay) dan free tier rate limit (20 RPM). Deepgram Nova-3 dengan keyterm boosting belum diuji.
- **TTS (ADR-0011 - Status: Proposed / OPEN):** Edge-TTS berstatus **prototipe saja, tidak disetujui untuk produk**. Audio berasal dari layanan browser tidak resmi, bukan Azure Cognitive Services API resmi. Keputusan TTS berstatus OPEN.
- **LLM (ADR-0012 - Status: Proposed):** Google Gemini Flash-Lite (`gemini-flash-lite-latest` / `gemini-3.1-flash-lite`) berkinerja baik pada ekstraksi intent 20 skenario, namun Free Tier melanggar prinsip privasi ADR-0005 karena Google merekam dan melatih model dari data prompt/audio pengguna. Wajib menggunakan Tier Berbayar (Pay-as-you-go) untuk kepatuhan privasi.

---

## 6. What the Data Cannot Tell Us

1. **Ukuran Sampel Sangat Terbatas ($n=20$ dan $n=3$):** Benchmark sintetis hanya menggunakan 20 skenario (dari 100 skenario yang direncanakan di v0). Pengujian mic fisik hanya berjalan 3 putaran ($n=3$). Sampel sekecil ini tidak memiliki signifikansi statistik untuk menetapkan peringkat vendor definitif.
2. **Audio Sintetis vs Manusia Nyata:** Pengujian sintetis menggunakan vokal jernih Edge-TTS dengan variasi kecepatan buatan ($0.9x - 1.1x$). Data ini tidak merefleksikan variasi akustik nyata: tarikan napas, gumaman (*filler words*), aksen lokal, artikulasi tidak sempurna, clipping mikrofon, dan dinamika jarak mic.
3. **Derau Putih Buatan (Gaussian Noise) vs Derau Drive-Thru Nyata:** Derau SNR 10 dB yang diuji adalah white Gaussian noise aditif sederhana. Kondisi ini tidak mencerminkan karakteristik frekuensi derau lapangan sebenarnya: gemuruh knalpot motor idle (low-frequency rumble), suara hujan lebat di atas atap seng, gema helm tertutup (*muffled reverberation*), atau distorsi speaker interkom drive-thru.
4. **Gold Labels Belum Tervalidasi Manusia:** Target transkrip dan intent untuk 20 skenario dihasilkan secara otomatis oleh generator skenario awal dan belum melalui spot-check menyeluruh oleh manusia.
5. **Keterbatasan dan Risiko Free Tier:** Performa pada free tier tidak mencerminkan keandalan sistem produksi. Free tier rentan terhadap *rate limiting* mendadak (HTTP 429), ketiadaan SLA ketersediaan, serta pelanggaran privasi data (Gemini Free Tier melatih model dari input pengguna).

---

## 7. Instruksi Lanjutan & Batasan Cabang

- **Branch:** `feat/minggu-2-spikes`.
- **TIDAK ADA MERGE KE `main`.**
- **TIDAK MEMULAI MINGGU 3.**
- Menunggu keputusan dan arahan dari pengembang terkait tindakan fallback §3.2 dan penyelesaian checklist status manusia.
