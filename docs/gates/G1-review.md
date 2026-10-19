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

## 8. Bagian G1b: Hasil Audit Pengukuran Ulang Representatif (Measurement Audit)

Berdasarkan audit teknis terhadap pengukuran G1b pada 30 skenario baku dari `eval/datasets/v0/scenarios.jsonl` (mencakup 10 kondisi percakapan), dilakukan pengujian ulang berstandar ketat: pengaliran audio *real-time paced* ($1.0\times$), pemisahan jeda hening akhir (*trailing silence*), audit kode sumber endpointing LiveKit Agents, pengukuran RTT jaringan langsung dari Indonesia, serta bootstrapping berpasangan (*paired bootstrap*).

---

### 8.1 Rekonsiliasi & Hasil Empiris Terukur per Komponen

#### A. Speech-to-Text (STT)

1. **Deepgram Nova-3 Streaming (WebSocket + Keyterm Boosting):**
   - **Parameter:** `model=nova-3`, `language=id`, `smart_format=true`, `keyterm` (30 istilah menu utama).
   - **Penjelasan Diskrepansi Latensi (1.820 ms vs 63 ms):**
     - Angka **1.820 ms** pada laporan awal adalah **KELIRU**. Pada skrip awal, pengiriman chunk audio menggunakan `asyncio.sleep(0.01)` (10x lebih cepat dari durasi audio nyata), sehingga klip audio berdurasi 3,5 detik tuntas dikirim dalam ~350 ms. Karena model ASR Deepgram memproses audio secara berurutan, selisih waktu antara chunk terakhir terkirim dan respons final diterima sebetulnya mengukur sisa durasi pemutaran audio, bukan latensi *turnaround* server setelah akhir ucapan.
     - Angka **63 ms** pada file mikrofon tunggal (`mic_session_03.wav`) juga merupakan artefak teknis: file tersebut berdurasi 31 detik (bukan satu *single turn* pesanan), sehingga proses pengenalan ucapan telah selesai untuk bagian awal ketika sinyal `CloseStream` dikirim, dan paket transkrip yang kebetulan tiba berikutnya langsung tercatat. File 31 detik ini **didrop** dari analisis latensi turn tunggal.
   - **Hasil Audit dengan Pacing Real-Time ($1.0\times$):**
     - Pengiriman chunk 100 ms dilakukan tepat tiap 100 ms waktu nyata.
     - Deteksi batas akhir ucapan (*true speech end*) dihitung berdasarkan amplop energi RMS (memisahkan rata-rata 0,92 detik *trailing silence* bawaan file sintesis).
     - Deepgram secara native memancarkan event `speech_final` begitu mendeteksi jeda hening setelah ucapan.
     - **Latensi dari Akhir Ucapan Nyata (*True Speech End*) ke Transkrip Final (`speech_final`):**
       - P50: **524.4 ms**
       - P95: **856.2 ms**
       - Mean: **549.4 ms** (Bootstrap 95% CI: `[485.0 ms, 625.0 ms]`)
   - **Akurasi STT pada 30 Skenario Sintetis Bersih:**
     - Clean KER Mean: **3.89%** (Bootstrap 95% CI: `[0.00%, 8.33%]`)
     - Clean WER Mean: **6.56%**

2. **Groq Whisper Turbo (`whisper-large-v3-turbo`):**
   - **Raw Inference Latency (REST):**
     - P50: **490.2 ms** (P95: 769.3 ms, Mean: 520.1 ms)
   - **Akurasi pada 30 Skenario Sintetis Bersih:**
     - Clean KER Mean: **11.11%** (Bootstrap 95% CI: `[4.99%, 18.33%]`)
     - Clean WER Mean: **10.09%**

3. **Audit Endpointing & Deteksi Hening (VAD):**
   - **Asal Angka 500 ms:** Nilai 500 ms berasal dari konstanta resmi `livekit-agents` v1.8.8 (`_ENDPOINTING_DEFAULTS["min_delay"] = 0.5`).
   - **Audit Kode Sumber (`livekit/agents/voice/audio_recognition.py` baris 1462–1463 & 1741–1745):**
     ```python
     speech_end_time = time.time() - ev.silence_duration - ev.inference_duration
     self._last_speaking_time = speech_end_time
     ...
     extra_sleep = endpointing_delay
     if last_speaking_time:
         extra_sleep += last_speaking_time - time.time()
     ```
     Karena `last_speaking_time - time.time()` bernilai negatif sebesar durasi hening yang telah berlalu, maka:
     $$\text{extra\_sleep} \approx \text{endpointing\_delay} - (\text{silence\_duration} + \text{inference\_duration})$$
   - **Kesimpulan Kritis:** Jeda VAD dan `min_delay` **TIDAK BERTAMBAH SECARA KUMULATIF/LINEAR**. Nilai `min_delay` bertindak sebagai batas waktu total (*clamped ceiling*) sejak ucapan nyata berakhir.
   - **Pengukuran VAD Offline Nyata pada 30 Audio:**
     - Waktu deteksi hening Silero VAD (P50): **386.0 ms** (Mean: 296.8 ms, 95% CI: `[229.6 ms, 356.9 ms]`).
     - Jika `min_delay = 500 ms`: VAD mendeteksi pada 386 ms, sistem tidur tambahan 114 ms $\to$ total jeda = **500 ms**.
     - Jika `min_delay` diturunkan ke 400 ms (*tuned config, projection*): total jeda = **400 ms**.
     - Jika diturunkan ke 300 ms (*aggressive config, projection*): jeda tertahan oleh deteksi hening VAD fisik di ~**386 ms**.
     - **Risiko Penurunan Ambang Batas:** Jeda hening ragu (*hesitation pauses*) penutur bahasa Indonesia berkisar 300–600 ms ("saya mau... burger satu, eh... sama cola"). Menyetel `min_delay` di bawah 400 ms berisiko memotong kalimat pelanggan di tengah jalan (*false turn cutoff*).

4. **Uji Statistik Berpasangan (*Paired Bootstrap Comparison*):**
   - Dihitung selisih KER per-utterance: $\Delta_i = \text{KER}_{\text{Nova-3}, i} - \text{KER}_{\text{Groq}, i}$ pada 30 skenario baku.
   - Rata-rata selisih ($\bar{\Delta}$): **-7.22%** (Nova-3 lebih rendah 7.22 poin persentase).
   - **Paired Bootstrap 95% Confidence Interval ($n=10,000$ resamples):**
     $$\text{CI}_{95\%} = [-15.00\%, 0.00\%]$$
   - **Pernyataan Hasil:** Selang kepercayaan 95% **TIDAK mengecualikan angka nol** (*does NOT exclude zero*, karena batas atas persis menyentuh 0.00% akibat performa imbang 0% KER pada 25 dari 30 skenario). Perbedaan akurasi belum memiliki signifikansi statistik mutlak pada ukuran sampel $n=30$.

---

#### B. Large Language Model (LLM Streaming & Warmth)

Pengukuran dilakukan dari laptop pengembang di Indonesia pada koneksi internet residensial:

1. **Round-Trip Time (RTT) Jaringan ke Endpoint Vendor:**
   - Google (`generativelanguage.googleapis.com`): **P50 = 42.0 ms** (Edge PoP Google Cloud Jakarta `asia-southeast2` / Singapura).
   - Deepgram (`api.deepgram.com`): **P50 = 196.9 ms** (US/Tokyo).
   - Groq (`api.groq.com`): **P50 = 241.2 ms** (US cloud).

2. **Perbandingan Cold vs Warm TTFT:**
   - **Google Gemini Flash-Lite (Resolved Model: `gemini-3.5-flash-lite`):**
     - Cold TTFT (koneksi awal): **794.2 ms** (s.d. 9.710 ms saat inisiasi DNS/TLS pertama).
     - Warm TTFT (koneksi HTTP pooled/reused): **P50 = 839.9 ms** (rentang: 603 ms – 961 ms).
     - First Complete Sentence (Warm): **P50 = 841.4 ms**.
   - **Groq-Hosted LLM (Resolved Model: `openai/gpt-oss-20b`):**
     - Cold TTFT: **8,589.6 ms**.
     - Warm TTFT: **P50 = 913.3 ms** (rentang: 593 ms – 1.002 ms).
   - **Catatan Proyeksi:** Pada sesi agent langsung, *connection pool* berstatus *warm*, sehingga angka **Warm** yang digunakan untuk proyeksi pipeline.

---

#### C. Text-to-Speech (TTS) — Status & Kepatuhan Batasan Kartu

- **Status Pengukuran:** **NOT MEASURED**.
- **Alasan Kepatuhan:** Batasan mutlak proyek (*Card-free Hard Constraint*) melarang layanan berbayar yang mewajibkan kartu pembayaran/kredit. Seluruh provider TTS resmi berbayar (Azure Speech S0, Cartesia Sonic, ElevenLabs) mewajibkan kartu saat pendaftaran. Prototipe browser Edge-TTS dilarang digunakan untuk klaim latensi produk resmi.

---

### 8.2 Tabel Proyeksi Latensi Pipeline Pre-TTS (Label: Proyeksi Berbasis Komponen Warm P50)

Ambang batas latensi turn proyek adalah **$\le 1.200\text{ ms}$**. Seluruh nilai di bawah ini adalah proyeksi berbasis data terukur komponen *warm*:

| No | Kandidat STT | Konfigurasi VAD / Endpointing | Kandidat LLM | Latensi Pre-TTS Terukur (P50) | Sisa Alokasi Maksimal untuk TTS TTFB agar Lolos $\le 1.2$s | Status Proyeksi | Asumsi Spesifik Komponen |
|:---:|---|---|---|:---:|:---:|:---:|---|
| 1 | **Deepgram Nova-3 (Stream)** | Built-in endpointing (~300ms) | Gemini Flash-Lite (Warm TTFT) | $524.4\text{ ms} + 839.9\text{ ms} = \mathbf{1,364.3\text{ ms}}$ | **-164.3 ms** (Defisit) | **FAIL** | Audio di-stream real-time; LLM koneksi warm; TTS instan (0 ms). |
| 2 | **Deepgram Nova-3 (Stream)** | Built-in endpointing (~300ms) | Gemini Flash-Lite (1st Sentence) | $524.4\text{ ms} + 841.4\text{ ms} = \mathbf{1,365.8\text{ ms}}$ | **-165.8 ms** (Defisit) | **FAIL** | Chunk kalimat pertama langsung dilempar ke TTS; TTS instan (0 ms). |
| 3 | **Groq Whisper Turbo (Batch)**| LiveKit Default (`min_delay` 500ms)| Gemini Flash-Lite (Warm TTFT) | $(490.2 + 500.0)\text{ ms} + 839.9\text{ ms} = \mathbf{1,830.1\text{ ms}}$ | **-630.1 ms** (Defisit) | **FAIL** | Inferensi file batch + 500 ms jeda hening VAD aman. |
| 4 | **Deepgram Nova-3 (Tuned)** | Aggressive endpointing (250ms) | LLM Ultra-Fast (Llama-3.1-8b est. 250ms)| $450.0\text{ ms} + 250.0\text{ ms} = \mathbf{700.0\text{ ms}}$ | **+500.0 ms** (Tersisa) | **PROJECTION ONLY** | Asumsi VAD agresif (risiko potong jeda), LLM lokal/edge sub-250ms, dan TTS streaming resmi berlisensi $\le 500$ ms. |

*Kesimpulan Proyeksi Empiris:*  
Pada tumpukan teknologi *cascade* saat ini dengan komponen resmi card-free (Nova-3 streaming + Gemini Flash-Lite warm), fase pra-TTS saja membutuhkan **~1.364 ms**, melampaui plafon 1.200 ms dengan selisih 164 ms tanpa menyisakan ruang untuk latensi sintesis suara TTS.

---

### 8.3 Status Evaluasi Gerbang G1 (Audit Update)

| No | Kriteria Gerbang G1 (§3.2) | Target | Hasil Terukur Audit | Status | Alasan Evaluasi |
|:---:|---|:---:|:---:|:---:|---|
| 1 | **Akurasi STT ID–EN Bersih (KER)** | $\le 15.0\%$ | Nova-3: **3.89%**<br>Groq: **11.11%** | **PROVISIONAL** | Memenuhi KER $\le 15\%$ pada 30 skenario sintetis. Selang kepercayaan berpasangan menyentuh 0.00% (belum eksklusif). Data suara manusia nyata belum memiliki ground-truth teks untuk diukur. |
| 2 | **Latensi Turn Estimasi** | $\le 1,200\text{ ms}$ | Pre-TTS Warm P50: **1,364 ms – 1,830 ms** | **FAIL** | Kombinasi STT + LLM warm melampaui batas 1.200 ms sebelum audio TTS mulai disintesis. |
| **TOTAL** | **STATUS GERBANG G1** | **PASS ALL** | **1 Provisional, 1 Fail** | **FAIL / NOT PASS** | **Ambang batas latensi 1.2 detik tidak terpenuhi.** Rekomendasi tindakan dituang pada ADR-0013. |

---

### 8.4 Tindakan Fallback §3.2 & Pilihan Arsitektur

Sesuai `PROJECT_PLAN.md` §3.2 dan audit empiris, pilihan keputusan resmi dicatat pada dokumen arsitektur [ADR-0013: G1 Outcome and Next Steps](file:///c:/Users/Lenovo/Downloads/drivethru/docs/decisions/0013-g1-outcome-and-next-steps.md) dengan 3 opsi:
1. **Opsi A (Pertahankan Target 1.2s):** Rekayasa teknis agresif (WebSocket streaming penuh, VAD agresif 250–300 ms, LLM mini lokal/edge < 250 ms, TTS streaming resmi sub-300 ms).
2. **Opsi B (Penyesuaian Target Latensi Berbasis UX Drive-Thru):** Menyesuaikan SLO latensi turn menjadi P50 < 1.8s–2.2s dengan justifikasi UX interkom drive-thru (umpan balik visual keranjang instan < 500 ms di layar simulator sembari audio respons kasir berbicara natural).
3. **Opsi C (Re-scoping Bahasa sesuai §3.2 Verbatim):** Pivot ke normalisasi LLM pasca-STT atau turunkan klaim ("mostly Indonesian + English item names") dengan perluasan alias menu, atau beralih ke bahasa Inggris penuh + ID parsial.

*Catatan: Alternatif API multimodal realtime audio-to-audio (misal Gemini Live API) dikesampingkan karena menghilangkan validasi keranjang deterministik sebelum berbicara (bertentangan dengan guardrail ADR-0001) dan belum diverifikasi batasan kartu kreditnya.*


