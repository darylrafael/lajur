# Gate G1 Definitive Final Statement & Project Milestone Record

**Document:** `docs/gates/G1-final-statement.md`  
**Milestone:** Gate G1 (Minggu 4 / Minggu 4d Closing Statement)  
**Date:** 2026-10-26  
**Author:** Daryl (Solo Dev) & Assistant  
**Status:** DEFINITIVE GATE G1 RECORD — CLOSED FOR MINGGU 4  

---

## 1. Vonis Definitif Gerbang G1 (*Definitive Gate G1 Verdict*)

### Status Target: **TIDAK TERBUKTI (NOT DEMONSTRATED / FAIL)**
- **Target Orisinal PRD §4.5 ($P50 \le 1.200\text{ ms}$):** **GAGAL (FAIL)**. Tidak tercapai pada iterasi v1 (Minggu 4), v2, maupun validasi v2b.
- **Batas Toleransi Pemilik Proyek ($P50 \le 1.800\text{ ms}$ dan $P95 \le 3.000\text{ ms}$):** **GAGAL (FAIL)**. Median terukur berada di rentang 3,6–4,0 detik. Proyek mematuhi komitmen ADR-0013: angka target tidak dinaikkan lagi, dan iterasi latensi dihentikan sementara hingga Minggu 8.
- **Status Tolok Ukur G1-v2:** **TIDAK VALID (INVALID)** karena cacat integrasi WebRTC (konfigurasi audio chunk 48 kHz vs frame header 16 kHz yang memicu timeout sistematis).
- **Hasil Tolok Ukur G1-v2b:** Diakui sebagai hasil pengukuran resmi Minggu 4 dengan keterbatasan ukuran sampel ($n=20$, $n_{\text{valid}}=17$, deviasi protokol: *underpowered*).

---

## 2. Angka Jujur Terverifikasi (*Honest Figures — Dual Reporting*)

Sesuai aturan validitas [`docs/gates/G1-v2b-validity-rule.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/gates/G1-v2b-validity-rule.md), berikut adalah hasil pengukuran Gerbang G1-v2b yang disajikan secara berdampingan tanpa penghapusan data sepihak:

| Metrik Latensi Turn | Semua Giliran Tercatat ($n=20$) | Giliran Valid Saja ($n_{\text{valid}}=17$) |
| :--- | :--- | :--- |
| **Median (P50)** | **4.029,5 ms** (95% CI: [2.297,3 ms, 6.434,6 ms]) | **3.591,6 ms** (95% CI: [2.178,6 ms, 5.856,4 ms]) |
| **Persentil 95 (P95)** | **172.143.222,3 ms** (terdistorsi anomali jam)* | **7.716,9 ms** (95% CI: [5.856,4 ms, 8.206,0 ms]) |
| **Rata-rata (*Mean*)** | **25.824.227,9 ms** | **4.044,7 ms** (95% CI: [3.094,5 ms, 5.070,4 ms]) |
| **Giliran Hangat P50 (Turn 2+)** | **3.692,4 ms** | **3.460,0 ms** |
| **Uji Konsistensi Keranjang** | **100,0%** (20/20 skenario cocok)*\* | **100,0%** (17/17 skenario cocok)*\* |

*\*Anomali jam: Pada Turn 13, 15, dan 16, nilai `t_speech_end` tercatat `0.0 ms` akibat perlombaan `stt_done_event` pasca-finalize, sehingga latensi mencerminkan uptime sistem Windows (~47,8 jam).*  
*\*\*Uji konsistensi: 100% adalah perbandingan terhadap ekspektasi keranjang sintetis buatan agen, bukan akurasi lapangan (*field accuracy*).*

---

## 3. Apa yang Diketahui vs Apa yang Belum Diketahui (*Knowns vs Unknowns*)

### Yang Diketahui Secara Pasti (*What is Known*):
1. **Fisika Pipeline Non-Colocated:** Menjalankan pipeline suara cascading di mana audio mengalir dari laptop pengembang di Indonesia melalui server WebRTC LiveKit di Hyderabad (India), transkripsi Deepgram di California (AS), inferensi Groq LPU di AS, dan sintesis suara ElevenLabs menghasilkan latensi interaktif ujung-ke-ujung sebesar **P50 ~3,6–4,0 detik**.
2. **Ketiadaan *Bottleneck* Logika Bisnis:** *State machine* keranjang dan validasi skema Pydantic hanya membutuhkan waktu **$\approx 0,5\text{ ms}$** (P50), membuktikan bahwa logika bisnis tidak berkontribusi terhadap keterlambatan respon.
3. **Rekonsiliasi Aritmetika Selesai:** Selisih antara penjumlahan tahapan individu dan total latensi per giliran terbukti konsisten pada rentang **0,5–36,9 ms** (rata-rata 3,7 ms), yang mencerminkan *overhead event loop* Python asyncio. Tidak ada latensi misterius yang tidak tercatat.
4. **Integritas Biaya:** Seluruh fase pengujian diselesaikan dengan biaya finansial **$0.00** dan menyisakan **1.613 karakter ElevenLabs** (di atas batas aman 600 karakter).

### Yang Belum Diketahui (*What is NOT Known*):
1. **Akurasi Lapangan (*Field Accuracy*):** Angka konsistensi keranjang 100% belum diuji terhadap data suara manusia riil di lingkungan bising (*drive-thru noise*). Label emas pada dataset evaluasi belum diverifikasi secara independen oleh pemilik proyek.
2. **Latensi dengan Worker Terlokalisasi / Colocated:** Belum diketahui berapa latensi yang dapat dicapai bila worker di-deploy di pusat data yang sama dengan LiveKit atau di kawasan Asia Tenggara (misal Singapura).
3. **Dampak Subjektif UX Antarmuka:** Belum diuji apakah keterlambatan 3,6 detik dapat diterima pengguna bila antarmuka visual menampilkan transkrip langsung (*live transcript*) dan animasi keranjang secara instan saat berbicara.

---

## 4. Catatan Wajib untuk Minggu 5 (*Requirement for Week 5*)

Sesuai arahan pemilik proyek:
> **Syarat Wajib Antarmuka Web (Minggu 5):**  
> Web UI **WAJIB** menampilkan transkrip langsung (*live partial transcript*) saat pengguna sedang berbicara, dan memperbarui tampilan keranjang di layar secara instan begitu *intent* selesai diaplikasikan oleh state machine.  
> *Rasional UX:* Pengguna di speaker drive-thru bersedia mentoleransi jeda respon suara asalkan mereka melihat bukti visual instan bahwa suara mereka terdengar dan pesanan mereka tercatat.

---

## 5. Status Milestone Perangkat Fisik Minggu 4 (*Real Device Target*)

- **Target Minggu 4:** *"One full order by voice works on a real device"*
- **Status Saat Ini:** **BELUM TERPENUHI (PENDING ON DARYL)**.
- **Rincian:** Pengujian otomatis telah selesai dijalankan pada laptop, namun pengujian end-to-end pada perangkat fisik iPhone (via browser Safari / WebRTC) sesuai panduan [`docs/demos/week-04-test-checklist.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/demos/week-04-test-checklist.md) adalah tugas manual yang tertunda pada Daryl (pemilik proyek). Cadangan 1.613 karakter ElevenLabs telah diamankan untuk keperluan ini.

---

## 6. Usulan Teks README (*Proposed README Section*)

Berikut adalah usulan rumusan teks untuk bagian "Measured Latency" pada `README.md` (ditandai secara eksplisit sebagai **PROPOSED** untuk ditinjau oleh pemilik):

```markdown
### Measured Latency (Gate G1-v2b Benchmark — 2026-10-26) [PROPOSED]

Measured on a consumer laptop in Jakarta, Indonesia over residential Wi-Fi, interacting with LiveKit Cloud (Hyderabad, India), Deepgram Nova-3 (California, US), Groq Qwen-2.5-32b (US via Anycast edge), and ElevenLabs Flash v2.5:

- **End-to-End Voice Turn Latency (Valid Turns, n=17):**
  - **Median (P50):** 3.59 s (95% Bootstrap CI: [2.18 s, 5.86 s])
  - **95th Percentile (P95):** 7.72 s (95% Bootstrap CI: [5.86 s, 8.21 s])
  - **Mean:** 4.04 s (95% Bootstrap CI: [3.09 s, 5.07 s])
- **All Recorded Turns (n=20, includes 3 clock-reference anomalies):**
  - **P50:** 4.03 s | **P95:** Distorted by harness timer artifact (see `docs/gates/G1-v2b-validity-rule.md`)
- **Stage Breakdown (Valid Turns P50):**
  - STT turnaround (`speech_final` with 500ms endpointing): 1.28 s
  - Intent classification LLM (TTFT): 0.56 s
  - Cart state machine transition: 0.0005 s (0.5 ms)
  - TTS TTFB (ElevenLabs Flash): 0.16 s
  - Client playout detection / network residual: 0.95 s
- **Gate G1 Verdict:** The 1.2 s PRD target and the 1.8 s owner fallback target are **NOT DEMONSTRATED** on this distributed cloud topology. Per project rules, targets are acknowledged as failed and are not adjusted upward. Optimization is deferred to post-MVP hosting co-location.
```
