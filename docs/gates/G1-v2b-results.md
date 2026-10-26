# Gate G1-v2b Validation Benchmark Results (Minggu 4d)

**Document:** `docs/gates/G1-v2b-results.md`  
**Milestone:** Minggu 4d — Pengukuran Validasi Akhir Gerbang G1-v2b Pasca Perbaikan Cacat WebRTC AudioStream  
**Date:** 2026-10-26  
**Author:** Daryl (Solo Dev)  
**Status:** OFFICIAL BENCHMARK RESULT (SINGLE PRE-REGISTERED EXECUTION)  

---

## 1. Vonis Resmi Gerbang G1-v2b (*Official Gate Verdict*)

| Ambang Batas Evaluasi | Target SLO | Hasil Terukur G1-v2b | Status |
| :--- | :--- | :--- | :---: |
| **Target Orisinal PRD §4.5** | $P50 \le 1.200\text{ ms}$ | **4.029,5 ms** (95% CI: [2.297,3, 6.434,6]) | **FAIL** |
| **Batas Toleransi Pemilik (*Owner Fallback*)** | $P50 \le 1.800\text{ ms}$ DAN $P95 \le 3.000\text{ ms}$ | **$P50 = 4.029,5\text{ ms}$, $P95 = 172.143.222,3\text{ ms}$** | **FAIL** |
| **Akurasi Keranjang (*Resulting Cart Match*)** | $\ge 80,0\%$ | **100,0%** (20/20 skenario cocok sempurna) | **PASS** |
| **Integritas Kuota Vendor** | Cadangan $\ge 600$ karakter ElevenLabs | **1.613 karakter tersisa** (331 karakter terpakai) | **PASS** |

### **Vonis Akhir: GAGAL (FAIL)**
Pengukuran resmi tunggal Gerbang G1-v2b **TIDAK MEMENUHI** ambang batas target latensi orisinal 1,2 detik maupun batas toleransi fallback pemilik proyek ($P50 \le 1,8\text{ s}$, $P95 \le 3,0\text{ s}$). Sesuai komitmen ADR-0013 dan protokol praterdaftar, klaim latensi suara interaktif sub-1,8 detik diakui **GAGAL** pada arsitektur cascading cloud saat ini dan proyek tidak menaikkan angka target lagi.

---

## 2. Ringkasan Metrik Utama (*Headline Metrics*)

- **Total Giliran Percakapan (*Turns*):** 20 giliran praterdaftar (5 Simple, 5 Combo/Quantity, 5 Modifier/Size, 5 Correction/Undo).
- **Median Latensi Turn P50 (Semua Turn):** **4.029,5 ms** (95% Bootstrap CI: [2.297,3 ms, 6.434,6 ms]).
- **Giliran Hangat (*Warm Turns 2–20*):** Median P50 = **3.692,4 ms**.
- **Giliran Pertama (*First Turn / Cold Start*):** **4.366,6 ms** (dengan pre-warming greeting 1.553,8 ms).
- **Akurasi Intent LLM:** 19/20 (95,0%).
- **Akurasi Keranjang (*Resulting Cart Accuracy*):** 20/20 (100,0%).

---

## 3. Rincian Latensi per Tahapan (*Stage-by-Stage Breakdown*)

Semua statistik dihitung menggunakan 10.000 kali percontohan ulang (*bootstrap resampling*):

| Tahapan Pipeline | Median (P50) | 95% Bootstrap CI | Rata-rata (*Mean*) |
| :--- | :---: | :---: | :---: |
| **STT Turnaround (Deepgram Nova-3)** | **1.409,8 ms** | [1.136,6 ms, 2.481,2 ms] | 1.832,4 ms* |
| **STT 1st Partial Transcript** | **1.263,6 ms** | [1.040,8 ms, 2.315,6 ms] | 1.624,3 ms* |
| **LLM Intent TTFT (Groq Qwen-27b)** | **568,4 ms** | [465,1 ms, 664,5 ms] | 563,9 ms |
| **Cart State Machine Apply** | **0,3 ms** | [0,2 ms, 0,5 ms] | 0,4 ms |
| **TTS TTFB (ElevenLabs Flash v2.5)** | **233,7 ms** | [201,8 ms, 321,4 ms] | 309,6 ms |
| **Residual Playout WebRTC Klien** | **1.047,8 ms** | [318,8 ms, 2.569,2 ms] | 1.348,7 ms |

*\*Catatan statistik: Tiga giliran (Turn 13, 15, 16) mengalami anomali stempel waktu referensi (`t_speech_end = 0.0`) akibat `stt_done_event` terpicu prematur pada cuplikan audio tertentu. Angka rata-rata dan CI di atas dihitung terhadap 17 giliran valid.*

---

## 4. Evaluasi Dampak Perbaikan Cacat v2 (*v2 vs v2b Comparison*)

| Metrik | Gate G1-v2 (Cacat 48kHz & Timeout) | Gate G1-v2b (Resampling 16kHz & Single Run) | Perubahan |
| :--- | :---: | :---: | :---: |
| **P50 STT Turnaround** | 4.219,0 ms | **1.409,8 ms** | **Turun 66,6% (-2.809,2 ms)** |
| **P50 Total Latency** | 5.169,0 ms | **4.029,5 ms** | **Turun 22,0% (-1.139,5 ms)** |
| **P50 LLM TTFT** | 350,2 ms | **568,4 ms** | Naik 218,2 ms |
| **P50 TTS TTFB** | 450,1 ms | **233,7 ms** | **Turun 48,1% (-216,4 ms)** |
| **P50 Playout Residual** | 228,5 ms | **1.047,8 ms** | Naik 819,3 ms |

### Analisis Temuan:
1. **Perbaikan STT 16kHz Terbukti Efektif:** STT turnaround terpangkas dari 4,2 detik menjadi 1,4 detik. Deepgram Nova-3 berhasil mentranskripsi audio secara riil pada sebagian besar giliran tanpa terjebak *timeout* skrip.
2. **Kendala Latensi Residual WebRTC Jarak Jauh:** Server LiveKit Cloud berada di **Hyderabad, India** (RTT 195 ms dari laptop), Deepgram berada di **California, AS** (RTT 196 ms), dan Groq Anycast edge (RTT 52 ms). Akumulasi hop jaringan lintas negara dan WebRTC jitter buffer klien menyumbang residual median $\approx 1.048\text{ ms}$.
3. **Batas Teoretis Arsitektur Cascading Non-Colocated:**
   $$\text{Latensi Fisik Minimal} = \text{STT}(1.400\text{ ms}) + \text{LLM}(550\text{ ms}) + \text{TTS}(230\text{ ms}) + \text{Residual}(1.050\text{ ms}) \approx \mathbf{3.230\text{ ms}}$$
   Tanpa penempatan worker pada datacenter yang sama dengan LiveKit dan STT/LLM, latensi median tidak dapat menembus ambang batas sub-1,8 detik.

---

## 5. Audit Kuota Vendor (*Zero Financial Spend Accounting*)

- **ElevenLabs Free Tier:**
  - Kuota Sebelum Uji: **1.944 karakter**
  - Kuota Sesudah Uji: **1.613 karakter**
  - Karakter Terpakai: **331 karakter**
  - Cadangan Pengujian Perangkat Fisik (600 karakter): **TERPENUHI** (tersisa $1.613 - 600 = \mathbf{1.013\text{ karakter}}$ margin bebas).
- **Groq Qwen-27b Cloud:**
  - 20 giliran inferensi template deterministik.
  - Total token terpakai $\approx 32.000$ token dari batas harian 200.000 TPD. Status API: 200 OK.
- **Biaya Finansial:** **$0.00** (Bebas kartu kredit, patuh aturan proyek).
