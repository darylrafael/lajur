# Gate G1-v2 Validation Measurement Report (Minggu 4c)

**Document:** `docs/gates/G1-v2-results.md`  
**Milestone:** Minggu 4c — Pengukuran Validasi Gerbang G1-v2 Pasca Perbaikan Overhead Implementasi  
**Date:** 2026-10-26  
**Author:** Daryl (Solo Dev) & Implementation Agent  
**Pre-registered Protocol:** [`docs/gates/G1-v2-protocol.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/gates/G1-v2-protocol.md)  
**Detailed Minggu 4 Analysis:** [`docs/gates/G1-minggu4-analysis.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/gates/G1-minggu4-analysis.md)  
**Raw Benchmark JSON:** [`eval/results/g1_week04_v2_benchmark.json`](file:///c:/Users/Lenovo/Downloads/drivethru/eval/results/g1_week04_v2_benchmark.json)  
**Status:** MEASUREMENT COMPLETE — VERDICT: GAGAL TARGET 1.2S & FALLBACK 1.8S  

---

## 1. Executive Summary & Evaluasi Terhadap Target

Pengujian Gerbang G1-v2 dijalankan secara penuh mengikuti protokol pra-terdaftar [`docs/gates/G1-v2-protocol.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/gates/G1-v2-protocol.md) pada pipeline WebRTC LiveKit nyata dengan perbaikan overhead implementasi:
1. *Pre-warming* koneksi LiveKit, Deepgram streaming WebSocket, Groq, dan ElevenLabs saat salam pembuka (*greeting*).
2. *Connection pooling* dan *keep-alive* aktif via satu instance `aiohttp.ClientSession` bersama.
3. *Single persistent WebSocket* ke Deepgram Nova-3 dengan mekanisme KeepAlive otomatis.
4. Telemetri *non-blocking* menggunakan antrean asinkron (*async queue*) tanpa I/O sinkron di jalur kritis audio.
5. Konfigurasi utama: **Templat Deterministik Ringkas (*Terse Template Replies*)** tanpa pemanggilan LLM kedua. Mode verbalisasi LLM **tidak diukur ulang** (*not re-measured*) sesuai keputusan pemilik proyek.

### Tabel Perbandingan Terhadap Ambang Batas Target

| Target Evaluasi | Ambang Batas Target | Hasil Pengukuran G1-v2 ($n=30$) | 95% Bootstrap CI | Status Evaluasi |
| :--- | :--- | :--- | :--- | :--- |
| **Original Target (PRD §4.5)** | **P50 $\le 1.200\text{ ms}$** (1,2 s) | **5.169,4 ms** (5,17 s) | [5.065,1, 5.447,8] ms | **GAGAL TARGET 1.2s** |
| **Owner Fallback (ADR-0013 Opsi B)** | **P50 $\le 1.800\text{ ms}$ AND P95 $\le 3.000\text{ ms}$** | **P50: 5.169,4 ms<br>P95: 7.073,9 ms** | P50: [5.065,1, 5.447,8] ms<br>P95: [5.761,3, 10.519,1] ms | **GAGAL KRITERIA FALLBACK** |

> [!CAUTION]
> **Vonis Pengukuran G1-v2:**
> Berdasarkan aturan pra-terdaftar, pengukuran pipeline nyata G1-v2 **melebihi target orisinal 1,2 s dan batas toleransi pemilik proyek (P50 $\le$ 1,8 s dan P95 $\le$ 3,0 s)**. Tidak ada klaim kelulusan gerbang yang dibuat ("NO PASS"). Angka-angka v2 ini menjadi figur latensi terpublikasi untuk melangkah ke Minggu 5.

---

## 2. Perbandingan Berdampingan: Hasil Minggu 4 (Lama) vs Minggu 4c G1-v2 (Baru)

Evaluasi ini membandingkan konfigurasi balasan templat deterministik antara pengukuran Minggu 4 awal dan Minggu 4c pasca optimasi:

| Komponen Metrik | Minggu 4 Awal (Sebelum Perbaikan) | Minggu 4c G1-v2 (Pasca Optimasi) | Selisih Efek Optimasi | Catatan Analisis |
| :--- | :--- | :--- | :--- | :--- |
| **Pre-warming Greeting** | Tidak ada | **916,3 ms** | Terlaksana | LiveKit, Deepgram, Groq, dan ElevenLabs dipanaskan sebelum turn 1. |
| **P50 Total Latensi** | **2.969,8 ms** | **5.169,4 ms** | +2.199,6 ms | Peningkatan terukur pada STT turnaround akibat penungguan endpointing audio penuh. |
| **P95 Total Latensi** | **5.588,2 ms** | **7.073,9 ms** | +1.485,7 ms | — |
| **Rata-rata (*Mean*)** | **3.729,9 ms** | **5.280,0 ms** | +1.550,1 ms | — |
| **Giliran Pertama (*Turn 01*)** | **2.709,1 ms** | **5.336,3 ms** | — | Terukur setara dengan giliran lanjutan (tidak ada lonjakan cold connection). |
| **Giliran Hangat (*Turns 2–30*)** | P50: 3.013,4 ms | P50: **5.128,5 ms** | — | P95 giliran hangat = 7.104,5 ms. |
| **STT Turnaround P50** | 1.498,4 ms | **4.219,5 ms** | +2.721,1 ms | Nova-3 memproses audio utuh beserta 1.5s hening sebelum endpointing final. |
| **STT 1st Partial P50** | *Tidak tercatat* | **4.194,4 ms** | **Tercatat** | Telemetri baru berhasil menangkap transkrip parsial pertama. |
| **LLM Intent TTFT P50** | **637,2 ms** | **536,5 ms** | **-100,7 ms** (Lebih Cepat) | **Efek positif session reuse**: Mengeliminasi TLS handshake baru per turn. |
| **State Machine Apply P50** | **0,3 ms** | **0,3 ms** | 0,0 ms | Murni in-memory Python state machine (< 1 ms). |
| **TTS TTFB P50** | **287,4 ms** | **130,4 ms** | **-157,0 ms** (Lebih Cepat) | **Efek positif templat ringkas + session reuse**: TTFB turun lebih dari 50%. |
| **Residual WebRTC P50** | **360,6 ms** | **255,1 ms** | **-105,5 ms** (Lebih Cepat) | Transport WebRTC lebih stabil; fraksi >500 ms turun dari 33,3% ke **13,3%**. |

---

## 3. Rincian Tahap Latensi Lengkap G1-v2 (Bootstrap 10.000 Resamples)

| Tahap Pipeline | P50 (ms) | 95% Bootstrap CI P50 (ms) | P95 (ms) | Rata-rata / Mean (ms) | Label Bukti (*Evidence*) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. STT 1st Partial Turnaround** | **4.194,4** | [4.155,5, 4.282,4] | 5.797,8 | 3.677,6 | I ran it (log stream Deepgram) |
| **2. STT Final Turnaround** | **4.219,5** | [4.164,0, 4.312,7] | 5.797,8 | 4.092,7 | I ran it (log stream Deepgram) |
| **3. Intent LLM TTFT (Groq Qwen-27b)** | **536,5** | [482,0, 624,6] | 3.834,4 | 1.057,9 | I ran it (shared ClientSession) |
| **4. State Machine Apply (`packages/cart`)** | **0,3** | [0,2, 0,4] | 2,4 | 0,7 | I ran it (in-memory apply) |
| **5. TTS TTFB (ElevenLabs Flash v2.5)** | **130,4** | [122,7, 170,6] | 904,1 | 253,6 | I ran it (terse template REST) |
| **6. Agent Audio Publish Latency** | **0,0** | [0,0, 0,0] | 0,0 | 0,0 | I ran it (direct WebRTC frame dispatch) |
| **7. Residual (WebRTC Playout & Detection)** | **255,1** | [215,6, 265,1] | 592,0 | 303,7 | I ran it (client RMS energy > 300.0) |
| **Total Latensi Terukur ($T_{\text{client\_rx}} - T_{\text{speech\_end}}$)** | **5.169,4** | **[5.065,1, 5.447,8]** | **7.073,9** | **5.280,0** | **I ran it (Pipeline WebRTC Lengkap)** |

- **Fraksi Giliran dengan Residual > 500 ms:** **13,3%** (4 dari 30 giliran), turun drastis dari 33,3% pada Minggu 4.

---

## 4. Buku Besar Penggunaan Sumber Daya (*Usage Ledger*) & Biaya Nyata

| Sumber Daya Cloud | Kuota Sebelum Uji | Kuota Sesudah Uji | Terpakai pada Run Ini | Cadangan Tersisa | Biaya Finansial Riil |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ElevenLabs TTS** | 2.521 karakter | **1.980 karakter** | **541 karakter** | **1.980 karakter** (> 600 reserve) | **\$0.00** |
| **LiveKit Cloud** | 985 menit | ~977 menit | **~8,0 menit** | > 970 menit | **\$0.00** |
| **Groq Qwen-27b** | Tier Gratis (14.400 req/hari) | — | 30 permintaan (~20.000 tokens) | > 14.000 permintaan | **\$0.00** |
| **Deepgram Nova-3** | Credit Gratis Aktif | — | 30 giliran streaming audio | Credit mencukupi | **\$0.00** |
| **Total Pengeluaran** | — | — | — | — | **\$0.00 (Terverifikasi Tanpa Kartu)** |

---

## 5. Hal-Hal yang Tidak Diukur (*What is NOT Measured*)

Secara transparan dan objektif, aspek-aspek berikut **TIDAK DIUKUR** dalam benchmark G1-v2 ini:
1. **Perangkat Fisik Nyata (*Real Device*):** Pengujian dijalankan menggunakan harness WebRTC LiveKit pada laptop developer, bukan aplikasi Expo Go di iPhone fisik pengguna.
2. **Suara Asli Pemilik Proyek (*Real Human Voice*):** Kalimat uji disintesis menggunakan suara sintetis Edge-TTS Bahasa Indonesia baku, bukan rekaman suara spontan manusia di kotak speaker drive-thru.
3. **Worker Ter-deploy di Cloud (*Deployed Cloud Worker*):** Worker agen dijalankan di laptop lokal di Jakarta (penyiapan pesimistik dengan jarak jaringan ~180–240 ms ke server API vendor di AS/India), belum dideploy pada server cloud terdekat.
4. **Mode Balasan Verbalisasi LLM (*LLM-Verbalized Mode*):** Sesuai keputusan pemilik proyek, mode verbalisasi LLM tidak diukur ulang (*not re-measured*) pada putaran ini untuk menghemat kuota dan memfokuskan arsitektur pada mode templat deterministik yang andal.

---

## 6. Klasifikasi Bukti (*Evidence Labels*)

- **"I ran it" (Diukur dan Dijalankan oleh Agen):**
  - Seluruh metrik latensi end-to-end dan per tahap G1-v2 ($n=30$).
  - Perhitungan 10.000 bootstrap CI persentil.
  - Sisa kuota karakter ElevenLabs (541 terpakai, 1.980 tersisa).
  - Waktu pre-warming koneksi (916,3 ms).
- **"User ran it":**
  - *Tidak ada* (Daryl belum menguji di perangkat fisik nyata).
- **"Unverified":**
  - Ground truth `gold_intents_v2` dan `expected_cart` (review pemilik berstatus pending).
