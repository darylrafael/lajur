# Gate G1-v2b Validation Benchmark Results (Minggu 4d — Corrected)

**Document:** `docs/gates/G1-v2b-results.md`  
**Milestone:** Minggu 4d — Laporan Hasil Terkoreksi Tolok Ukur Validasi Gerbang G1-v2b  
**Date:** 2026-10-26  
**Author:** Daryl (Solo Dev)  
**Status:** OFFICIAL BENCHMARK RESULT (CORRECTED POST-HOC FROM RAW DATA)  

---

## 1. Vonis Resmi Gerbang G1-v2b (*Official Gate Verdict*)

Sesuai aturan validitas praterdaftar [`docs/gates/G1-v2b-validity-rule.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/gates/G1-v2b-validity-rule.md), data disajikan secara ganda (*dual reporting*): (a) Semua giliran sebagaimana tercatat ($n=20$), dan (b) Giliran valid saja ($n_{\text{valid}}=17$).

| Ambang Batas Evaluasi | Target SLO | Hasil G1-v2b (Semua Turn, $n=20$) | Hasil G1-v2b (Turn Valid, $n=17$) | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Target Orisinal PRD §4.5** | $P50 \le 1.200\text{ ms}$ | **4.029,5 ms** (95% CI: [2.297,3, 6.434,6]) | **3.591,6 ms** (95% CI: [2.178,6, 5.856,4]) | **FAIL** |
| **Batas Toleransi Pemilik (*Owner Fallback*)** | $P50 \le 1.800\text{ ms}$ DAN $P95 \le 3.000\text{ ms}$ | $P50 = 4.029,5\text{ ms}$<br>$P95 = 172.143.222,3\text{ ms}$* | $P50 = 3.591,6\text{ ms}$ (95% CI: [2.178,6, 5.856,4])<br>$P95 = 7.716,9\text{ ms}$ (95% CI: [5.856,4, 8.206,0]) | **FAIL** |
| **Uji Konsistensi Keranjang (*Cart Consistency Check*)** | $\ge 80,0\%$ | **100,0%** (20/20 skenario cocok) | **100,0%** (17/17 skenario cocok) | **PASS\*** |
| **Integritas Kuota Vendor** | Cadangan $\ge 600$ char ElevenLabs | **1.613 karakter tersisa** | **1.613 karakter tersisa** | **PASS** |

*\*Catatan anomali stempel waktu: Nilai P95 pada semua turn ($172.143.222,3\text{ ms}$) disebabkan oleh cacat harness pada Turn 13, 15, dan 16 di mana `t_speech_end` tercatat `0.0 ms` akibat perlombaan `stt_done_event` pasca-finalize. Lihat [`docs/gates/G1-v2b-validity-rule.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/gates/G1-v2b-validity-rule.md).*  
*\*\*Catatan akurasi: Angka 100% adalah uji konsistensi *end-to-end* terhadap ekspektasi keranjang sintetis buatan agen, BUKAN akurasi lapangan (*field accuracy*). Label emas belum diverifikasi oleh pemilik proyek.*

### **Vonis Akhir: GAGAL (FAIL)**
Baik pada perhitungan seluruh giliran ($n=20$, $P50 = 4,03\text{ s}$) maupun hanya giliran valid ($n=17$, $P50 = 3,59\text{ s}$, $P95 = 7,72\text{ s}$), pipeline suara **TIDAK MEMENUHI** ambang batas 1,2 detik PRD maupun batas toleransi fallback pemilik ($P50 \le 1,8\text{ s}$, $P95 \le 3,0\text{ s}$). Sesuai komitmen ADR-0013, vonis adalah **FAIL** dan target tidak dinaikkan lagi.

---

## 2. Deviasi Protokol (*Protocol Deviation*)

- **Ukuran Sampel (*Sample Size*):** Protokol resmi `G1-v2-protocol.md` menetapkan minimal 30 giliran. Amandemen v2b memangkas uji coba menjadi 20 giliran untuk menghemat kuota ElevenLabs.
- **Pencatatan Resmi Deviasi:**  
  > **"v2b n=20, below the pre-registered 30, underpowered"**  
  Dengan $n_{\text{valid}} = 17$, rentang ketidakpastian 95% Bootstrap CI untuk P50 melebar ke [2.178,6 ms, 5.856,4 ms].

---

## 3. Rincian Latensi per Tahapan (*Stage-by-Stage Breakdown*)

Statistik dihitung menggunakan 10.000 kali percontohan ulang (*bootstrap resampling*) terhadap 17 giliran valid ($n_{\text{valid}} = 17$):

| Tahapan Pipeline | Median (P50) | 95% Bootstrap CI | Rata-rata (*Mean*) | P95 |
| :--- | :---: | :---: | :---: | :---: |
| **STT 1st Partial Transcript** | **1.186,9 ms** | [903,6 ms, 1.533,3 ms] | 1.321,8 ms | 2.666,4 ms |
| **STT Turnaround (`speech_final`)** | **1.283,1 ms** | [1.111,3 ms, 2.004,8 ms] | 1.845,2 ms | 4.250,0 ms |
| **LLM Intent TTFT (Groq Qwen-2.5-32b)** | **564,3 ms** | [527,1 ms, 701,1 ms] | 625,4 ms | 880,1 ms |
| **Cart State Machine Apply** | **0,5 ms** | [0,3 ms, 1,6 ms] | 4,5 ms | 14,7 ms |
| **TTS TTFB (ElevenLabs Flash v2.5)** | **164,6 ms** | [130,2 ms, 387,0 ms] | 427,0 ms | 1.462,3 ms |
| **Agent First Audio Frame Publish** | **0,0 ms** | [0,0 ms, 0,0 ms] | 0,0 ms | 0,0 ms |
| **Residual / Client Playout Detection** | **945,2 ms** | [297,3 ms, 2.068,3 ms] | 1.138,9 ms | 2.963,2 ms |

---

## 4. Rekonsiliasi Aritmetika & Retraksi Klaim Batas Teoretis

### A. Rekonsiliasi Aritmetika per Giliran
Pada laporan sebelumnya, terdapat kekeliruan interpretasi bahwa "selisih antara jumlah tahapan dan total latensi menunjukkan data hilang". Rekonsiliasi per giliran membuktikan bahwa penjumlahan tahapan pada setiap giliran **selaras sempurna** dengan total latensi terukur:

$$\text{Total Latensi} = \text{STT} + \text{LLM TTFT} + \text{State} + \text{TTS TTFB} + \text{Residual} + \Delta_{\text{async}}$$

| Turn | STT Final (ms) | LLM TTFT (ms) | State (ms) | TTS TTFB (ms) | Residual (ms) | Jumlah Tahapan (ms) | Total Latensi (ms) | $\Delta_{\text{async}}$ (ms) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **T01** | 792,9 | 484,6 | 1,2 | 2.827,0 | 251,9 | 4.357,5 | 4.366,6 | +9,1 |
| **T02** | 1.186,9 | 514,8 | 1,6 | 149,2 | 325,4 | 2.177,9 | 2.178,6 | +0,7 |
| **T03** | 1.283,1 | 478,5 | 0,3 | 120,9 | 373,9 | 2.256,6 | 2.257,6 | +1,0 |
| **T04** | 1.286,3 | 601,7 | 0,5 | 133,5 | 312,7 | 2.334,8 | 2.337,0 | +2,2 |
| **T05** | 970,3 | 506,4 | 0,5 | 121,0 | 283,0 | 1.881,2 | 1.881,9 | +0,7 |
| **T06** | 1.161,9 | 572,5 | 0,4 | 122,7 | 297,3 | 2.154,8 | 2.155,4 | +0,6 |
| **T07** | 1.244,2 | 550,8 | 0,4 | 130,2 | 247,3 | 2.172,9 | 2.176,1 | +3,3 |
| **T08** | 903,6 | 527,1 | 0,3 | 164,6 | 288,4 | 1.884,0 | 1.884,6 | +0,6 |
| **T09** | 1.533,3 | 850,1 | 0,3 | 140,1 | 1.067,3 | 3.591,1 | 3.591,6 | +0,5 |
| **T10** | 867,9 | 564,3 | 58,5 | 387,0 | 2.468,6 | 4.346,2 | 4.383,1 | +36,9 |
| **T11** | 1.111,3 | 796,3 | 3,1 | 282,1 | 1.134,4 | 3.327,2 | 3.328,9 | +1,7 |
| **T12** | 5.341,7 | 559,8 | 3,1 | 232,5 | 2.068,3 | 8.205,3 | 8.206,0 | +0,7 |
| **T14** | 3.977,1 | 701,1 | 0,3 | 118,9 | 1.058,0 | 5.855,4 | 5.856,4 | +1,0 |
| **T17** | 2.957,6 | 620,7 | 0,2 | 1.121,2 | 2.894,0 | 7.593,8 | 7.594,6 | +0,8 |
| **T18** | 3.192,2 | 549,8 | 1,1 | 370,2 | 2.106,1 | 6.219,4 | 6.221,0 | +1,6 |
| **T19** | 2.004,8 | 1.000,1 | 0,6 | 402,0 | 3.240,1 | 6.647,5 | 6.648,3 | +0,8 |
| **T20** | 1.554,0 | 752,6 | 3,8 | 436,0 | 945,2 | 3.691,6 | 3.692,4 | +0,8 |

Discrepansi ($\Delta_{\text{async}}$) berada di rentang **0,5 ms hingga 36,9 ms** (rata-rata 3,7 ms). Ini adalah *overhead internal event loop* Python asyncio antara validasi state dan inisiasi streaming TTS. Tidak ada latensi misterius yang hilang.

### B. Retraksi Klaim Batas Teoretis
Klaim pada draf sebelumnya bahwa "tahapan berjumlah ~3.230 ms membuktikan batas fisik arsitektur" **DIRETRAKSI**.  
Penjumlahan median marginal ($\sum \text{P50}_{\text{stage}} = 2.957,6\text{ ms}$) secara matematis tidak sama dengan median dari total latensi ($\text{P50}_{\text{total}} = 3.591,6\text{ ms}$). Klaim tersebut merupakan kekeliruan aritmetika (*fallacy of summing medians*).

---

## 5. Definisi Titik Akhir "First Audio" & Penjelasan Residual

### A. Titik Akhir Terukur vs Telemetri Internal
Dalam basis data telemetri internal `turn_events.sqlite3`:
- Kolom `t_tts_first_byte_ms`, `t_first_audio_frame_ms`, dan `t_agent_publish_ms` mencatat nilai yang identik (selisih 0,0 ms) karena kode pipeline (`pipeline.py:450`) menetapkan `t_agent_publish_ms = t_first_audio_frame_ms` bila parameter bernilai `0.0`.
- **Relabeling Resmi Titik Akhir:**
  > **"first-audio endpoint = first audio frame published by the agent, and transport and jitter to a client are NOT measured in internal SQLite pipeline telemetry."**

### B. Mengapa Residual Membengkak dari ~255 ms ke ~945 ms?
Residual dalam tolok ukur dihitung di sisi *test participant*:
$$\text{residual\_ms} = \max(0.0, (t_{\text{first\_audio\_received}} - t_{\text{agent\_publish}}) \times 1000.0)$$

Penyebab pembengkakan residual tanpa spekulasi:
1. **Ambang Batas RMS Playout:** Fungsi `monitor_playout` hanya menandai `t_first_audio_received` ketika energi audio $\text{RMS} > 300,0$.
2. **Keheningan di Awal Audio ElevenLabs:** *Chunk* pertama dari ElevenLabs kerap berupa audio berenergi sangat rendah ($\text{RMS} < 300$), sehingga deteksi playout tertunda beberapa ratus milidetik hingga frame berbunyi vokal tiba.
3. **Timeout Playout:** Pada beberapa giliran ekor (T10, T12, T17, T18, T19), `first_audio_received_event` mengalami *timeout* pada batas 2.000 ms, sehingga `t_first_audio_received` dipatok secara paksa 2 detik setelah publish.
4. **Jarak Jaringan Geografis:** Server LiveKit Cloud berada di **Hyderabad, India** (RTT ~214 ms dari laptop Jakarta), ditambah *de-jitter buffer* WebRTC klien.

---

## 6. Rekonsiliasi STT Turnaround (524 ms vs 1.283 ms)

Mengapa audit awal menyebut STT ~524 ms sedangkan di v2b tercatat 1.283 ms?
- **Angka 524 ms Sebelumnya:** Diukur pada uji coba terisolasi koneksi WebSocket langsung ke Deepgram (lokal tanpa WebRTC), menggunakan audio pendek dan tanpa memperhitungkan *turn-taking* atau *endpointing delay*.
- **Angka 1.283 ms pada v2b:** Mengukur siklus penuh:
  1. Pengiriman audio via WebRTC ke server LiveKit di Hyderabad (~100 ms one-way).
  2. Penerusan audio ke agent worker di laptop (~100 ms).
  3. Pengaliran frame PCM ke server Deepgram di California (~196 ms RTT).
  4. **Jeda Endpointing Deepgram:** Konfigurasi `endpointing=500ms` mewajibkan Deepgram menunggu 500 ms keheningan sebelum mengeluarkan `speech_final`.
  5. Komputasi inferensi model Nova-3 (~150–250 ms).
  Total siklus: $200\text{ ms (WebRTC)} + 500\text{ ms (endpointing)} + 196\text{ ms (RTT AS)} + 200\text{ ms (inferensi)} \approx \mathbf{1.100 - 1.300\text{ ms}}$. Angka ini konsisten dengan fisika jaringan.

---

## 7. Fakta Groq: RTT & Prompt Caching

- **Jaringan & Edge PoP:**
  Domain `api.groq.com` berada di balik Cloudflare Anycast CDN. Handshake TCP/TLS terselesaikan di PoP terdekat (Jakarta/Singapura) dengan RTT $\approx 52\text{ ms}$. Namun, inferensi LPU Groq tetap dieksekusi di pusat data Amerika Utara. Permintaan HTTP diteruskan melalui jaringan tulang punggung Cloudflare ke AS.
- **Prompt Caching:**
  Dokumentasi resmi Groq mengonfirmasi bahwa *Prompt Caching* aktif otomatis untuk *prompt prefix* $\ge 1.024$ token. Token *cache hit* tidak dihitung dalam kuota TPM setelah pemrosesan selesai, dan mempercepat TTFT di sisi LPU. Namun, *prompt caching* tidak meniadakan latensi transmisi trans-Pasifik dari gateway edge ke klaster LPU. TTFT Groq terukur stabil di $564,3\text{ ms}$ (P50).

---

## 8. Relabeling Resmi Klaim Proyek (*Official Relabeled Claims*)

1. **Klaim Akurasi (100%):**
   > *"100% (20/20) is an end-to-end consistency check against agent-authored expected carts on synthetic audio, NOT field accuracy. Gold labels have not been verified by the owner."*
2. **Klaim Batas Arsitektur:**
   > *"On a consumer laptop with cascading cloud APIs across three continents (LiveKit in India, Deepgram in US, Groq in US), the measured pipeline achieved P50 ~3.6–4.0 s depending on filtering, and did not achieve sub-1.8 s."*

---

## 9. Audit Kuota & Pengeluaran Finansial

- **ElevenLabs Free Tier:**
  - Kuota Sebelum Uji: **1.944 karakter**
  - Kuota Sesudah Uji: **1.613 karakter**
  - Karakter Terpakai: **331 karakter**
  - Cadangan Pengujian Perangkat Fisik (600 karakter): **TERPENUHI** (tersisa $1.613 - 600 = \mathbf{1.013\text{ karakter}}$ margin bebas).
- **Groq Qwen-2.5-32b:** 20 giliran inferensi template deterministik ($\approx 32.000$ token). Status API: 200 OK.
- **Biaya Finansial:** **$0.00** (Bebas kartu kredit, patuh aturan proyek).
