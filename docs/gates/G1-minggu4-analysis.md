# Post-Hoc Analysis: Gate G1 Minggu 4 Measurement

**Document:** `docs/gates/G1-minggu4-analysis.md`  
**Milestone:** Minggu 4b — Analisis Post-Hoc terhadap Hasil Pengukuran Gerbang G1  
**Date:** 2026-10-25  
**Author:** Daryl (Solo Dev) & Implementation Agent  
**Status:** POST-HOC ANALYSIS — VERDICT FIXED  

---

> [!CAUTION]
> ### VONIS RESMI (TETAP DAN TIDAK BERUBAH)
> Berdasarkan aturan dan kriteria yang telah didaftarkan sebelumnya (*pre-registered protocol* pada [`docs/gates/G1-minggu4-measurement.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/gates/G1-minggu4-measurement.md)), pengukuran Gerbang G1 pada Minggu 4 **DINYATAKAN GAGAL (*MISSED*)** memenuhi:
> 1. Target Orisinal PRD §4.5 ($P50 \le 1.200\text{ ms}$).
> 2. Batas Toleransi Pemilik Proyek (*Owner Fallback*, $P50 \le 1.800\text{ ms}$ DAN $P95 \le 3.000\text{ ms}$).
>
> Analisis dalam dokumen ini berstatus **eksplisit *post-hoc*** (setelah fakta) dan **TIDAK MENGUBAH VONIS KEGAGALAN TERSEBUT**. Setiap klaim latensi yang lebih baik di masa depan wajib dibuktikan melalui eksekusi pengukuran pra-terdaftar yang **BARU** (*new pre-registered run*) dengan ambang batas yang sama, dan hasil pengukuran Minggu 4 ini tetap tercatat permanen dalam repositori.

---

## 1. Rincian Per Tahap (*Per-Stage Breakdown*) & Bootstrap 95% CI

Data berikut dihitung dari 60 baris data giliran (*turns*) valid pada jendela pengujian benchmark resmi (30 giliran Mode 2 Templat Deterministik dan 30 giliran Mode 1 Verbalisasi LLM) yang tersimpan di `data/turn_events.sqlite3` dan `eval/results/g1_week04_benchmark.json`. Setiap metrik dihitung menggunakan 10.000 sampel *bootstrap resampling* untuk menghasilkan *confidence interval* 95% persentil.

> [!NOTE]
> **Catatan Telemetri STT First Partial:**
> Timestamp untuk *interim partial* pertama Deepgram **tidak dicatat (*not persisted*)** ke dalam SQLite selama eksekusi benchmark Minggu 4 (hanya timestamp `speech_final` yang dicatat pada `t_stt_final_ms`). Ketiadaan data ini dinyatakan secara terbuka (*stated plainly*). Untuk menangkap metrik ini pada pengujian berikutnya, listener `Results` Deepgram perlu mencatat `monotonic_ns()` pada kemunculan objek transkrip pertama sebelum `is_final=True`.

### Tabel Rincian Tahap Latensi Pipeline (Bootstrap 10.000 Resamples)

| Tahap Pipeline | Mode 2: Templat Deterministik ($n=30$) | Mode 1: Verbalisasi LLM ($n=30$) | Catatan & Klasifikasi |
| :--- | :--- | :--- | :--- |
| **1. STT Turnaround ($T_{\text{stt\_final}} - T_{\text{speech\_end}}$)** | **P50: 1.498,4 ms** [1378.8, 1666.5]<br>**P95: 2.830,3 ms** [2507.8, 4296.7]<br>Mean: 1.778,2 ms [1551.9, 2046.7] | **P50: 1.529,2 ms** [1393.4, 1683.8]<br>**P95: 3.012,0 ms** [2518.4, 4402.6]<br>Mean: 1.812,9 ms [1572.0, 2094.8] | *Inherent to stack/location*: Terdiri dari 500 ms *silence floor* Deepgram + RTT transpasifik ke US server + pemrosesan audio Nova-3. |
| **2. Intent LLM TTFT (Groq Qwen-27b)** | **P50: 637,2 ms** [545.1, 732.2]<br>**P95: 1.088,0 ms** [879.8, 1245.0]<br>Mean: 678,7 ms [593.4, 763.3] | **P50: 573,4 ms** [536.3, 615.7]<br>**P95: 845,1 ms** [711.9, 918.6]<br>Mean: 575,5 ms [501.6, 639.3] | *Implementation artifact (fixable)*: Handshake TLS/TCP dingin per panggilan HTTP REST di Groq. |
| **3. Intent LLM JSON Complete & Valid** | **P50: 2,2 ms** [1.8, 2.8]<br>**P95: 5,8 ms** [3.4, 55.1]<br>Mean: 4,2 ms [2.1, 7.9] | **P50: 1,9 ms** [1.8, 2.6]<br>**P95: 8,3 ms** [3.3, 17.2]<br>Mean: 3,0 ms [2.0, 4.3] | Streaming JSON validator + Pydantic v1 Discriminated Union. Retries: 0 (100% valid pada token pertama). |
| **4. State Machine Apply (`packages/cart`)** | **P50: 0,3 ms** [0.3, 0.4]<br>**P95: 1,8 ms** [0.6, 2.5]<br>Mean: 0,5 ms [0.4, 0.8] | **P50: 0,3 ms** [0.3, 0.3]<br>**P95: 0,7 ms** [0.4, 3.5]<br>Mean: 0,4 ms [0.3, 0.7] | Eksekusi murni Python in-memory state machine. |
| **5. Balasan & TTS TTFB** | **P50: 287,4 ms** [248.7, 353.5]<br>**P95: 1.339,3 ms** [365.8, 12097.2]<br>Mean: 747,4 ms [285.5, 1596.3] | **P50: 585,0 ms** [530.1, 708.1]<br>**P95: 1.466,5 ms** [891.1, 2706.5]<br>Mean: 746,7 ms [615.3, 927.9] | Mode 2: Murni ElevenLabs TTFB.<br>Mode 1: Termasuk Groq Verbalizer (+297,6 ms) + ElevenLabs TTFB. |
| **6. Agent Audio Frame Publish** | **P50: 0,0 ms** [0.0, 0.0]<br>**P95: 0,0 ms** [0.0, 0.0]<br>Mean: 0,0 ms [0.0, 0.0] | **P50: 0,0 ms** [0.0, 0.0]<br>**P95: 0,0 ms** [0.0, 0.0]<br>Mean: 0,0 ms [0.0, 0.0] | *Instantaneous dispatch* ke LiveKit `AudioSource`. |
| **7. Residual (WebRTC Transport & Playout)** | **P50: 360,6 ms** [335.4, 493.7]<br>**P95: 1.369,0 ms** [613.5, 1863.8]<br>Mean: 520,8 ms [404.2, 670.7] | **P50: 347,8 ms** [309.2, 488.6]<br>**P95: 824,4 ms** [604.0, 1327.0]<br>Mean: 455,8 ms [381.3, 545.4] | Transmisi WebRTC transpasifik ke LiveKit Cloud AS + Jitter Buffer + Window RMS klien. |
| **Total Latensi Terukur ($T_{\text{client\_rx}} - T_{\text{speech\_end}}$)** | **P50: 2.969,8 ms** [2735.2, 3376.5]<br>**P95: 5.588,2 ms** [4023.0, 18258.1]<br>Mean: 3.729,9 ms [3006.4, 4930.7] | **P50: 3.365,3 ms** [2986.8, 3618.8]<br>**P95: 5.946,9 ms** [4184.1, 7436.5]<br>Mean: 3.594,2 ms [3244.8, 4020.5] | **Kedua mode gagal ambang batas 1.2s dan fallback 1.8s.** |

### Ringkasan Residual (Selisih Total Terukur vs Jumlah Tahap)
- **P50 Residual:** **360,6 ms** (Templat) dan **347,8 ms** (LLM).
- **Fraksi Giliran dengan Residual > 500 ms:** **33,3%** pada Mode Templat (10 dari 30 giliran) dan **30,0%** pada Mode LLM (9 dari 30 giliran).

---

## 2. Investigasi & Klasifikasi Masalah (Tasks 2a – 2f)

### 2a. Pembuatan Koneksi Deepgram WebSocket per Giliran
- **Bukti Kode:** `eval/scripts/spikes/benchmark_week04_g1.py` baris 386–387:
  ```python
  async with http_sess.ws_connect(
      dg_url, headers={"Authorization": f"Token {dg_api_key}"}
  ) as dg_ws:
  ```
- **Analisis Dampak:** Pada script benchmark, koneksi WebSocket dibuka di dalam loop setiap giliran (`execute_turn`). Handshake WebSocket ke server Deepgram di AS membutuhkan 1 RTT TCP + TLS 1.3 handshake + HTTP Upgrade (~200–350 ms). Meskipun script benchmark membuka WebSocket ini *sebelum* audio disintesis dan diputar, pembukaan per-turn ini merupakan *overhead* jika diadopsi dalam sesi percakapan nyata.
- **Klasifikasi:** `"implementation artifact (fixable)"`.

### 2b. Koneksi Baru untuk ElevenLabs dan Groq per Giliran
- **Bukti Kode:**
  - `packages/voice-pipeline/src/drivethru_voice/groq.py` baris 224 & 324:
    ```python
    async with aiohttp.ClientSession() as session:
        async with session.post(...) as resp:
    ```
  - `packages/voice-pipeline/src/drivethru_voice/elevenlabs.py` baris 118:
    ```python
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
    ```
- **Analisis Dampak:** Ketiadaan *connection pooling* (`aiohttp.ClientSession` dibuat dan dihancurkan pada setiap *call* tunggal). Di Indonesia, latensi fisik ke server Groq/ElevenLabs adalah ~180–220 ms RTT. Setiap pembuatan `ClientSession` baru membayar DNS query + TCP 3-way handshake + TLS 1.3 negotiation = minimal 1,5–2 RTT (~300–400 ms) sebelum byte payload terkirim. Pada Mode 1 (LLM verbalization), terjadi 2 panggilan Groq berurutan + 1 panggilan ElevenLabs = total 3x handshake = **~900–1.200 ms terbuang murni pada negosiasi koneksi**.
- **Klasifikasi:** `"implementation artifact (fixable)"`.

### 2c. Apakah Penundaan Endpointing Menumpuk (*Stacking Delays*)?
- **Bukti Konfigurasi & Kode:**
  - Deepgram STT: `endpointing=500` ms (dikonfigurasi pada URL parameter `endpointing=500`).
  - LiveKit Turn Detection: Pada tracer bullet `benchmark_week04_g1.py`, audio dialirkan secara *raw* dari WebRTC audio frame langsung ke Deepgram WebSocket tanpa VAD terpisah di sisi LiveKit (`min_delay` atau Silero VAD tidak dijalankan di depan Deepgram).
- **Analisis Dampak:** Penundaan endpointing **TIDAK menumpuk** (*did not stack*) dari dua layer VAD yang berbeda. Namun, parameter `endpointing=500` pada Deepgram menciptakan **lantai hening (*silence floor*) mutlak sebesar 500 ms**. Artinya, Deepgram Nova-3 secara matematis tidak akan pernah mengirimkan event `speech_final` sebelum mendeteksi 500 ms keheningan berturut-turut setelah pengguna berhenti berbicara. Latensi STT turnaround P50 sebesar ~1.500 ms terdiri dari: 500 ms *silence floor* + 200 ms transit transpasifik + pemrosesan server STT + *packetization*.
- **Klasifikasi:** `"inherent to this stack or location"` (Lantai hening 500 ms adalah batasan desain konfigurasi, sedangkan 180–200 ms adalah jarak fisik jaringan ke AS).

### 2d. Wilayah LiveKit Cloud, RTT Transpasifik, & Buffer Playout Klien
- **Bukti & Data Jaringan:**
  - Host server: `lajur-6xsjb7dn.livekit.cloud` (ter-resolve ke IP `143.223.94.99`, geolokasi AS).
  - Pengukuran RTT TCP dari laptop dev (Jakarta) ke server LiveKit Cloud:
    - Minimum: **181,0 ms**
    - Median: **197,9 ms**
    - Maksimum: **403,8 ms**
- **Analisis Dampak:**
  1. *Clock Stop Point*: Pencatatan $T_{\text{first\_audio}}$ dihentikan pada saat klien menerima frame audio WebRTC dan mendeteksi level energi suara (*client-side RMS energy* $\text{rms} > 300,0$), **BUKAN** saat worker agen mem-publish audio.
  2. *Residual Playout*: Selisih sebesar ~350–360 ms (P50) antara `t_agent_publish` dan `t_client_rx` sepenuhnya disebabkan oleh transmisi WebRTC RTP paket melintasi Samudra Pasifik (~200 ms RTT) ditambah buffer de-jitter WebRTC dan jendela analisa frame RMS (20 ms chunk).
- **Klasifikasi:** `"inherent to this stack or location"`.

### 2e. Eksekusi Sekuensial Intent & Verbalisasi vs Pemblokiran Event Loop
- **Bukti Kode:**
  - `packages/voice-pipeline/src/drivethru_voice/pipeline.py` baris 299 & 362:
    ```python
    # Sekuensial: Intent Parser -> State Machine -> Verbalizer
    intent = await self.intent_parser.parse(transcript)
    result = self.cart_service.apply_intent(self.session_id, intent)
    spoken_text = await self.reply_generator.verbalize(result.facts)
    ```
  - Logging SQLite (`log_turn()`): Pemanggilan SQLite `cur.execute(...)` bersifat sinkron (*synchronous*), namun dieksekusi **SETELAH** seluruh pemrosesan dan pengiriman audio selesai (`t_first_audio_frame_ms` dicatat sebelum logging dipanggil).
- **Analisis Dampak:**
  - Eksekusi sekuensial antara LLM Intent dan LLM Verbalizer menambah beban latensi sebesar **+297,6 ms** (TTFB verbalizer) pada Mode 1. Ini terjadi karena verbalisasi bergantung secara fundamental pada keluaran state machine (`SpeechFacts`).
  - Penulisan SQLite sinkron tidak memblokir jalur kritis audio frame pertama karena dijalankan di akhir siklus giliran.
- **Klasifikasi:**
  - Ketergantungan sekuensial Intent $\to$ State Machine $\to$ Verbalizer: `"inherent to cascade architecture"`.
  - Penulisan SQLite sinkron pada thread utama: `"implementation artifact (fixable)"` (dapat dipindahkan ke *thread pool* / *async queue*).

### 2f. Karakteristik Giliran Pertama (*Cold*) vs Giliran Lanjutan (*Warm*)
- **Bukti Data Benchmark:**
  - Skenario Pertama (`scen_001` - Dingin):
    - Mode Templat: **2.709,1 ms**
    - Mode LLM: **6.658,4 ms** (sangat lambat akibat inisialisasi sesi LiveKit room, alokasi ICE candidates, dan TLS handshake Groq pertama).
  - Skenario 2 hingga 30 (*Warm Room*):
    - Mode Templat P50: **3.013,4 ms**
    - Mode LLM P50: **3.365,2 ms**
  - Rincian per Kuadran Giliran:
    - Giliran 1–10: P50 Templat = 3.463,4 ms; P50 LLM = 3.375,8 ms.
    - Giliran 11–20: P50 Templat = 3.229,9 ms; P50 LLM = 3.494,4 ms.
    - Giliran 21–30: P50 Templat = 2.819,4 ms; P50 LLM = 2.986,8 ms.
- **Analisis Dampak:** Terdapat lonjakan latensi ekstrim pada turn pertama di Mode LLM akibat kompilasi internal, TLS cold start, dan alokasi WebRTC peer connection.
- **Klasifikasi:** `"measurement artifact"`.

---

## 3. Daftar Kandidat Perbaikan & Estimasi Hipotesis

Semua angka di bawah ini berstatus **HIPOTESIS (BELUM DIUKUR)** dan **BUKAN KLAIM HASIL**:

| Kandidat Perbaikan | Klasifikasi Masalah | Mekanisme Teknis | Estimasi Reduksi Latensi (Hipotesis) |
| :--- | :--- | :--- | :--- |
| **H1: Persistent `aiohttp.ClientSession` dengan Keep-Alive** | *Implementation Artifact* | Menggunakan sesi HTTP bersama (*shared pool*) untuk Groq dan ElevenLabs guna menghilangkan 3x negosiasi TLS/TCP transpasifik per giliran. | **-300 ms s.d. -600 ms** pada P50 |
| **H2: Penyesuaian Deepgram Endpointing ke 300 ms** | *Inherent/Config* | Menurunkan `endpointing=500` menjadi `endpointing=300`. Mengurangi batas deteksi hening sebesar 200 ms. Risiko: potensi kenaikan *false cut-off* pada jeda bicara lambat. | **-200 ms** pada P50 STT turnaround |
| **H3: Templat Balasan Ringkas (*Terse Template Replies*)** | *Architecture* | Menggunakan templat deterministik pendek (contoh: "Baik, 1 burger dicatat. Mau minumnya?") alih-alih kalimat panjang, mengurangi ukuran buffer chunk pertama ElevenLabs. | **-50 ms s.d. -150 ms** pada P50 TTS TTFB |
| **H4: Persistent LiveKit Room & Pre-warmed Audio Track** | *Measurement Artifact* | Mempertahankan koneksi kamar WebRTC tetap aktif antar giliran alih-alih alokasi berulang. | **-500 ms s.d. -2.000 ms** pada P95 tail (menghilangkan lonjakan *cold turn*) |
| **Total Estimasi Akumulatif Hipotesis** | — | Penerapan H1 + H2 + H3 + H4 secara simultan pada Mode Templat. | **P50 diharapkan turun dari ~2.970 ms ke kisaran ~1.900 – 2.200 ms** |

> [!WARNING]
> Sekalipun seluruh perbaikan implementasi (H1, H3, H4) dan konfigurasi endpointing (H2) diterapkan, perkiraan P50 masih berada di atas ambang batas 1.200 ms dan beririsan ketat dengan batas fallback 1.800 ms. Hal ini membuktikan bahwa **jarak fisik jaringan transpasifik (~200 ms RTT) dan lantai hening wicara manusia (~300 ms) merupakan batasan inheren sistem berbasis cloud di AS**.
