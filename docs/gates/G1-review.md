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

---

## 8. Bagian G1b: Hasil Pengukuran Ulang Representatif (Representative Re-measurement)

Sesuai protokol pra-registrasi [`docs/gates/G1b-protocol.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/gates/G1b-protocol.md), telah dilakukan pengukuran ulang representatif pada 30 skenario baku dari `eval/datasets/v0/scenarios.jsonl` mencakup 10 kondisi operasional (simple, code-switching, quantity, modifiers, combos, corrections, undo, hesitation, out-of-stock, handoff, prompt injection).

### 8.1 Data Empiris Terukur per Komponen

#### A. Speech-to-Text (STT)
1. **Deepgram Nova-3 Streaming (WebSocket + Keyterm Boosting):**
   - **Parameter:** `model=nova-3`, `language=id`, `smart_format=true`, `keyterm` (30 istilah menu utama).
   - *Temuan Query Parameter:* Pengujian memvalidasi bahwa parameter `keywords` ditolak pada Nova-3 (HTTP 400); Nova-3 secara resmi menggunakan parameter `keyterm`.
   - **Streaming Latency (Akhir audio terkirim $\to$ transkrip final diterima):**
     - P50: **1,820.0 ms**
     - P95: **2,585.3 ms**
     - Mean: **1,765.3 ms** (Bootstrap 95% CI: `[1,568.9 ms, 1,977.1 ms]`)
   - **Akurasi pada 30 Skenario Sintetis Bersih:**
     - Clean KER Mean: **3.89%** (Bootstrap 95% CI: `[0.00%, 8.33%]`)
     - Clean WER Mean: **6.56%**
2. **Groq Whisper Turbo (`whisper-large-v3-turbo`):**
   - **Raw Inference Latency (REST):**
     - P50: **490.2 ms** (P95: 769.3 ms, Mean: 520.1 ms)
   - **Silero VAD Endpointing Delay:**
     - Diambil langsung dari nilai default resmi `livekit-agents` v1.8.8 (`_ENDPOINTING_DEFAULTS["min_delay"]`): **500.0 ms**.
   - **Effective Pipeline Latency (Inference + VAD Delay):**
     - P50: **990.2 ms**
     - P95: **1,269.3 ms**
     - Mean: **1,020.1 ms** (Bootstrap 95% CI: `[969.2 ms, 1,080.3 ms]`)
   - **Akurasi pada 30 Skenario Sintetis Bersih:**
     - Clean KER Mean: **11.11%** (Bootstrap 95% CI: `[4.99%, 18.33%]`)
     - Clean WER Mean: **10.09%**
3. **Perbandingan Statistik Akurasi (Nova-3 vs Groq):**
   - Selang kepercayaan KER Nova-3 (`[0.00%, 8.33%]`) bertumpang-tindih (*overlapping*) dengan batas bawah selang kepercayaan Groq (`[4.99%, 18.33%]`) pada rentang 5.0%–8.3%.
   - Sesuai protokol, perbedaan akurasi ini dilaporkan **berada dalam batas derau variansi statistik (*within noise*)** pada ukuran sampel $n=30$.
4. **Pengujian File Suara Manusia Asli tunggal (`eval/audio/real/mic_session_03.wav`):**
   - Deepgram Nova-3 Streaming Latency: **63.1 ms**
   - Groq Whisper Effective Pipeline Latency (+500ms VAD): **2,256.5 ms**
   - Akurasi: **Not measured** (karena transkrip referensi ground-truth dari user belum tersedia). Bukti suara nyata adalah $n=1$ (hanya latensi).

#### B. Large Language Model (LLM Streaming)
1. **Google Gemini Flash-Lite Free Tier:**
   - **Model ID Eksak yang Melayani (*Resolved Model*):** `models/gemini-3.5-flash-lite` (via alias `gemini-flash-lite-latest`).
   - Time to First Token (TTFT): P50 = **840.1 ms** (P95 = 1,071.1 ms, Mean = 876.3 ms)
   - Time to First Sentence: P50 = **841.4 ms** (P95 = 1,071.1 ms)
   - Total Response Time: P50 = **952.9 ms**
2. **Groq-Hosted LLM (`openai/gpt-oss-20b`):**
   - **Model ID Eksak yang Melayani:** `openai/gpt-oss-20b`.
   - Time to First Token (TTFT): P50 = **748.3 ms** (P95 = 879.0 ms, Mean = 750.1 ms)
   - Time to First Sentence: P50 = **748.3 ms** (P95 = 879.0 ms)
   - Total Response Time: P50 = **750.5 ms**

#### C. Text-to-Speech (TTS) — Status & Analisis Sensitivitas
- **Status Pengukuran:** **NOT MEASURED**.
- **Alasan:** Batasan mutlak proyek (*Card-free Hard Constraint*) melarang layanan berbayar yang mewajibkan kartu kredit. Tidak ada kunci API resmi card-free yang tersedia di `.env` (Azure Speech resmi butuh kartu kecuali Azure for Students; Edge-TTS dilarang digunakan untuk mengukur latensi produk).
- **Tabel Analisis Sensitivitas Alokasi Anggaran TTS (Ambang Batas Turn: $\le 1,200\text{ ms}$):**

| Pasangan Komponen | Latensi STT P50 (ms) | Latensi LLM P50 (ms) | Akumulasi STT + LLM (ms) | Sisa Alokasi Maksimal untuk TTS TTFB agar Lolos $\le 1.2$s | Status Kelayakan Latensi |
|---|:---:|:---:|:---:|:---:|:---:|
| **Nova-3 Stream + Gemini (Sequential)** | 1,820.0 ms | 952.9 ms (Total) | 2,772.9 ms | **-1,572.9 ms** (Defisit) | **FAIL** |
| **Nova-3 Stream + Gemini (Chunked)** | 1,820.0 ms | 841.4 ms (1st Sent) | 2,661.4 ms | **-1,461.4 ms** (Defisit) | **FAIL** |
| **Nova-3 Stream + Gemini (Ideal Plan)** | 1,820.0 ms | 840.1 ms (TTFT) | 2,660.1 ms | **-1,460.1 ms** (Defisit) | **FAIL** |
| **Groq (+500ms VAD) + Gemini (Sequential)**| 990.2 ms | 952.9 ms (Total) | 1,943.1 ms | **-743.1 ms** (Defisit) | **FAIL** |
| **Groq (+500ms VAD) + Gemini (Chunked)**| 990.2 ms | 841.4 ms (1st Sent) | 1,831.6 ms | **-631.6 ms** (Defisit) | **FAIL** |
| **Groq (+500ms VAD) + Gemini (Ideal Plan)**| 990.2 ms | 840.1 ms (TTFT) | 1,830.2 ms | **-630.2 ms** (Defisit) | **FAIL** |

*Temuan Kritis Sensitivitas:*  
Bahkan dengan asumsi hipotetis TTS instan (TTFB = 0 ms), kombinasi STT dan LLM saja sudah menghabiskan **1.831 ms hingga 2.773 ms**, melampaui ambang batas 1.200 ms dengan defisit antara 631 ms hingga 1.573 ms.  
Jika digabungkan dengan latensi prototipe Edge-TTS (TTFB terukur 1.406 ms pada Tier 1):
- Groq Whisper (+500ms VAD) + Gemini Chunked (841 ms) + TTS TTFB (1.406 ms) = **3.237 ms (~3.24 detik)**.
- Deepgram Nova-3 (1.820 ms) + Gemini Chunked (841 ms) + TTS TTFB (1.406 ms) = **4.067 ms (~4.07 detik)**.

---

### 8.2 Status Evaluasi Resmi Gerbang G1b

| No | Kriteria Gerbang G1b | Ambang Batas (§3.2) | Hasil Terukur G1b | Status Evaluasi | Alasan Evaluasi |
|:---:|---|:---:|:---:|:---:|---|
| 1 | **Akurasi STT ID–EN Bersih (KER)** | $\le 15.0\%$ | Nova-3: **3.89%**<br>Groq: **11.11%** | **PROVISIONAL** | Kedua kandidat memenuhi KER $\le 15\%$ pada 30 skenario sintetis. Namun data suara manusia nyata masih $n=1$ (hanya latensi, akurasi belum diukur). Status tetap Provisional sesuai protokol hingga dataset suara nyata representatif tersedia. |
| 2 | **Latensi Turn Estimasi** | $\le 1,200\text{ ms}$ | STT+LLM saja: **1,831 ms – 2,773 ms**<br>Dengan TTS: **3.2s – 4.1s** | **FAIL** | Seluruh varian formula (sequential, chunked streaming, ideal) gagal memenuhi ambang batas 1.2 detik. Alokasi tersisa untuk TTS bernilai negatif. |
| **TOTAL** | **STATUS GERBANG G1b** | **PASS ALL** | **1 Provisional, 1 Fail** | **FAIL / NOT PASS** | **Kriteria latensi tidak terpenuhi.** Keputusan gerbang tetap berada di tangan Daryl. |

---

### 8.3 Opsi Tindakan Fallback §3.2 & Pilihan Teknis Berbasis Data G1b (Tidak Diterapkan Otomatis)

1. **Opsi Fallback Verbatim dari `PROJECT_PLAN.md` §3.2:**
   - *Pivot ke normalisasi LLM pasca-STT atau turunkan klaim ("mostly Indonesian + English item names") dan perluas menu dengan alias.*
   - *Jika tetap gagal: pindah ke bahasa Inggris saja + ID parsial, dan ubah narasi portofolio.*
2. **Opsi Penyesuaian Latensi yang Didukung Bukti Data G1b:**
   - **Opsi A (Penyesuaian SLO Latensi Proyek):** Mengubah SLO latensi demo publik dari P50 < 800ms / 1.2s menjadi **P50 < 2.5s – 3.0s**. Data membuktikan bahwa *cascade pipeline* (STT streaming $\to$ LLM streaming $\to$ TTS streaming) melalui jaringan internet publik dari Indonesia ke server cloud AS/Eropa secara fisik tidak memungkinkan mencapai < 1.2 detik tanpa GPU terdistribusi lokal (*co-located edge server*).
   - **Opsi B (Optimasi Jeda VAD / Endpointing):** Mengurangi ambang batas hening (*silence threshold*) VAD pada LiveKit Agents dari 500 ms menjadi 250–300 ms jika kondisi akustik mikrofon memungkinkan.
   - **Opsi C (Peralihan ke Audio-to-Audio Realtime Multimodal API):** Beralih dari *cascade pipeline* ke API multimodal realtime (misal Gemini Multimodal Live API). Namun opsi ini memiliki trade-off: menghilangkan validasi deterministik keranjang sebelum AI berbicara (ditolak di ADR-0001).
   - **Opsi D (Eksplorasi TTS Streaming Berlisensi Resmi Tanpa Kartu):** Mencari dan memvalidasi penyedia TTS streaming resmi yang menyediakan akses gratis tanpa kewajiban kartu kredit.

*Seluruh opsi di atas dilaporkan sebagai bahan pertimbangan arsitektur dan TIDAK DITERAPKAN secara otomatis.*

---

### 8.4 What the Data Cannot Tell Us (G1b)

1. **Akurasi Suara Manusia Nyata ($n=1$, Unmeasured):** Data akurasi (KER 3.89% dan 11.11%) hanya berlaku untuk audio sintetis yang diucapkan jernih oleh Edge-TTS. Kita belum memiliki data akurasi empiris untuk suara manusia asli pengemudi drive-thru (dialek daerah, desah napas, gumaman ragu, dan interupsi penumpang).
2. **Latensi Jaringan Riil Klien Browser:** Pengukuran dilakukan dari terminal lokal Windows melalui panggilan API terisolasi. Latensi round-trip WebRTC browser pelanggan ke worker agent di cloud belum terukur.
3. **Latensi TTS Resmi Berlisensi:** Karena tidak ada kunci TTS card-free, latensi audio pertama (TTFB) dari provider resmi seperti Azure Speech S0, Cartesia Sonic, atau ElevenLabs Flash belum dapat diukur secara langsung.

