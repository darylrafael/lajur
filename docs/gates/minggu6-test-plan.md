# Minggu 6 Robustness & Pipeline Hardening Test Plan (Pre-Registered)

**Dokumen:** `docs/gates/minggu6-test-plan.md`  
**Milestone:** Minggu 6 — Robustness + Validasi Pasar Dimulai  
**Branch:** `feat/minggu-6-robustness`  
**Status:** PRE-REGISTERED (COMMITTED BEFORE IMPLEMENTATION)  
**Aturan Utama:** Single run, no tuning after seeing results. Seluruh kriteria, skenario, dan metrik ditetapkan di sini sebelum implementasi kode.

---

## 1. Verbatim Target Rencana Proyek (PROJECT_PLAN.md §13)

Sesuai `docs/PROJECT_PLAN.md` baris 421–425 (git hash-object: `a2edfabcb69ec87b674488a474533b3d0b329998`):

```markdown
### Minggu 6 — Robustness + Validasi Pasar Dimulai
- VAD/turn detection adaptif, barge-in, undo/koreksi, handoff kru, upsell.
- Preset noise (4) di sisi klien.
- Mulai wawancara Mom Test (target 8–10 sampai Minggu 10).
- **Target:** skenario barge-in dan koreksi lulus; wawancara ≥ 3 selesai.
```

### 1.1 Status Uji Pengguna / Manusia (Pending Delegation)
Sesuai kesepakatan delegasi pemilik proyek (*owner-delegated defaults*):
- Pengecekan order perangkat nyata (Minggu 4) dan uji kebergunaan 3 orang awam (Minggu 5) berstatus **PENDING** (ditunda ke akhir Minggu 6 setelah kuota ElevenLabs reset pada 20 November 2026).
- Wawancara Mom Test (target $\ge 3$ selesai) adalah tugas manusia pemilik proyek; instrumen dan panduan disediakan pada Minggu 6.
- Kriteria kelulusan teknis minggu ini yang dapat diotomasi dievaluasi menggunakan data sintetis dan fakes terisolasi tanpa biaya vendor ($0.00).

---

## 2. Pernyataan Integritas & Sumber Audio Sintetis

> [!IMPORTANT]
> **Pemberitahuan Sumber Data:** Seluruh pengujian audio dalam suite evaluasi otomatis ini menggunakan audio sintetis (*synthetic audio* yang digenerasi melalui Edge-TTS untuk input suara pelanggan dan WAV stub lokal). Tidak ada rekaman audio pelanggan nyata yang digunakan, dan audio tidak pernah disimpan secara persisten. Edge-TTS hanya digunakan untuk membuat sampel audio uji input, bukan untuk TTS produk layanan (TTS produk menggunakan ElevenLabs atau fallback teks).

---

## 3. Matriks Skenario, Kondisi, dan Kriteria Kelulusan

### 3.1 Fitur 1: Adaptive Endpointing & Hesitation Handling
- **Tujuan:** Mencegah pemotongan dini (*false cutoff*) saat pelanggan menjeda bicara di tengah kalimat (*hesitation* / jeda berpikir / partikel gantung seperti "anu", "sebentar", "sama...").
- **Baseline Konfigurasi:** Deepgram Nova-3 static base endpointing tetap 300 ms (tidak mengubah file G1).
- **Mekanisme Adaptif:** Heuristik berbasis token/partikel di akhir partial transcript. Jika transkrip berakhir dengan partikel ragu (*fillers*, konjungsi gantung, kuantitas gantung), sistem memberikan toleransi perpanjangan waktu tunggu bounded (+500 ms) sebelum memfinalisasi turn.
- **Kumpulan Skenario:**
  1. *Hesitation Set:* 7 skenario dari `eval/datasets/v0/scenarios.jsonl` (`scen_081`, `scen_082`, `scen_083`, `scen_084`, `scen_085`, `scen_118`, `scen_131`).
  2. *Synthetic Hesitation Pauses:* 3 variasi kondisi jeda sintetis (`source: generated-for-minggu6`) pada $n = 10$ sampel ujicoba per kondisi:
     - Kondisi A: Jeda 300 ms mid-thought.
     - Kondisi B: Jeda 500 ms mid-thought.
     - Kondisi C: Jeda 800 ms mid-thought.
  3. *Clean / Non-Hesitation Set:* $n = 20$ turn ucapan bersih tanpa partikel ragu dari `eval/datasets/v0/scenarios.jsonl` (`scen_001` hingga `scen_020`).
- **Metrik:**
  - *False-cutoff rate:* Persentase pemotongan sebelum kalimat tuntas (pada jeda 300 ms, 500 ms, dan 800 ms).
  - *Added latency on non-hesitation turns:* Tambahan latensi pada kalimat normal (harus 0 ms).
  - Bootstrap 95% Confidence Interval untuk setiap estimasi.
- **Kriteria Lulus (Pass Criteria):**
  - Pada jeda $\le 500$ ms dengan partikel ragu, *false-cutoff rate* $\le 20\%$ (turun signifikan dari baseline statis 300 ms yang $100\%$ terpotong).
  - Pada kalimat bersih non-hesitation, *added latency* $= 0.0$ ms (tidak ada penundaan tambahan).

### 3.2 Fitur 2: Barge-in & Echo Bleed Protection
- **Tujuan:** Saat pelanggan berbicara ketika bot sedang memperdengarkan audio balasan, audio output bot harus segera dihentikan, tugas generasi in-flight dibatalkan, dan keranjang belanja tetap konsisten. Proteksi *echo bleed* mencegah audio bot yang bocor ke mikrofon memicu *false barge-in*.
- **Mekanisme Proteksi:** Minimum speech duration guard (150 ms sustain energy / $\ge 2$ frame audio) untuk memfilter transient echo / klik akustik sebelum memutuskan barge-in.
- **Kumpulan Skenario (`source: generated-for-minggu6`):**
  1. *Valid Barge-in Trials:* $n = 10$ percobaan interupsi suara pengguna yang disengaja saat audio bot sedang diputar.
  2. *Echo Bleed / Spike Trials:* $n = 10$ lonjakan audio singkat ($< 150$ ms, simulasi pantulan speaker ke mic).
- **Metrik:**
  - *Barge-in stop latency:* Waktu (ms) dari deteksi frame suara pengguna valid hingga penghentian stream audio bot.
  - *Echo-bleed false barge-in rate:* Persentase lonjakan singkat $< 150$ ms yang secara keliru menghentikan bot (harus $0\%$).
  - *Cart state consistency:* Konsistensi keranjang setelah interupsi ($100\%$, tidak ada mutasi parsial).
- **Kriteria Lulus (Pass Criteria):**
  - Stop latency $\le 150$ ms.
  - Echo-bleed false barge-in rate $= 0\%$.
  - Cart consistency $= 100\%$.

### 3.3 Fitur 3: Koreksi, Undo, dan Konsistensi Keranjang (Pipeline E2E)
- **Tujuan:** Memvalidasi bahwa intent koreksi dan undo bekerja mulus melewati seluruh pipeline orkestrasi suara tanpa merusak integritas keranjang belanja.
- **Batasan Ketat:** Menggunakan `packages/cart` State Machine dan intent schema v1 tanpa perubahan skema.
- **Kumpulan Skenario:** Seluruh 11 skenario koreksi & undo dari `eval/datasets/v0/scenarios.jsonl`:
  - `scen_071`, `scen_072`, `scen_073`, `scen_074`, `scen_075`, `scen_076`, `scen_077`, `scen_078`, `scen_079`, `scen_080`, `scen_134`.
- **Transparansi Evaluasi:** Label target (*gold labels*) dibuat secara sintetis oleh agen sebelumnya dan belum diverifikasi manusia (*agent-authored and unverified*).
- **Metrik:**
  - *Scenario Pass Rate:* Jumlah skenario yang menghasilkan state keranjang akhir dan item yang identik dengan `expected_cart`.
- **Kriteria Lulus (Pass Criteria):**
  - Scenario pass rate $\ge 80\%$ (minimal 9 dari 11 skenario lulus).

### 3.4 Fitur 4: Handoff Kru (FR-09), Upsell Kontekstual (FR-10), dan Graceful Degradation
- **Tujuan & Cakupan:**
  1. *Handoff Kru (FR-09):*
     - Triggers: Permintaan eksplisit pelanggan (8 skenario `scen_098`, `scen_101`–`scen_107`), kegagalan pemahaman berulang ($\ge 3$ consecutive unknown intents), timeout sesi ($> 180$ detik), atau batas turn ($> 12$ turn).
     - Tindakan: Cart dipertahankan (*preserved*), dialog beralih ke state `handoff`, dan event data channel `handoff` dengan `crew_message` dikirimkan ke UI.
  2. *Upsell Kontekstual (FR-10):*
     - Berdasarkan `upsell_rules` pada menu combo.
     - Aturan: Maksimum 1 penawaran upsell per order, tidak pernah diulangi jika pelanggan menolak (`decline_more` / "tidak usah"), dan tidak memblokir penyelesaian order.
  3. *Vendor Graceful Degradation:*
     - Penanganan Groq 429: Parsing header/body error `Retry-After`, retry berbatas dengan exponential backoff, pesan sopan jika limit terlampaui.
     - STT Drop: Otomatis mendeteksi pemutusan koneksi WebSocket Deepgram dan melakukan re-koneksi.
     - TTS Quota Exhaustion / Failure: Fallback mulus ke mode teks (`TTS_MODE=none`), pesan balasan teks tetap tampil di UI tanpa crash/hang.
- **Kumpulan Skenario (`source: generated-for-minggu6` & `v0`):**
  - $n = 8$ skenario explicit handoff (`scen_098`, `scen_101`–`scen_107`).
  - $n = 3$ skenario trigger otomatis handoff (repeated unknown, timeout, max turns).
  - $n = 6$ skenario evaluasi aturan upsell (order combo dengan upsell, penerimaan upsell, penolakan upsell, uji penolakan ulang).
  - $n = 3$ skenario simulasi error vendor (Groq 429 rate limit, STT dropped stream, TTS quota exhausted).
- **Kriteria Lulus (Pass Criteria):**
  - $100\%$ skenario handoff sukses memicu state `handoff` dan event protokol dengan keranjang utuh.
  - $100\%$ skenario upsell mematuhi batas maks 1 kali penawaran per order dan tidak mengulang pasca penolakan.
  - $100\%$ skenario error vendor tertangani secara elegan (*graceful*) tanpa unhandled exception / crash worker.

### 3.5 Fitur 5: Preset Noise di Sisi Klien (Web Audio API)
- **Tujuan:** 4 preset audio simulasi kebisingan jalanan pada simulator web live mode sebelum audio dikirim ke WebRTC.
- **Daftar Preset:**
  1. `clean`: Passthrough mikrofon tanpa tambahan noise.
  2. `motor_idle`: Simulasi suara mesin motor stasioner / knalpot idle.
  3. `rain_traffic`: Simulasi hujan lebat bercampur desing lalu lintas jalan raya.
  4. `helmet`: Simulasi filter akustik muffled (low-pass filter helm).
- **Atribusi & Lisensi:** Seluruh berkas audio bersumber dari domain publik berlisensi CC0 atau CC-BY yang diverifikasi per-file dan didokumentasikan di `docs/NOTICE` / `ATTRIBUTION.md`.
- **Keterbatasan:** Preset hanya aktif pada mode langsung (*live mode* dengan mic), bukan mode replay. Dilabeli secara transparan sebagai *"simulated"*.
- **Kriteria Lulus (Pass Criteria):**
  - Audio graph Web Audio API terpasang pada mic stream di browser.
  - Slider volume kontrol bekerja dari 0% hingga 100%.
  - Dokumentasi atribusi lengkap untuk setiap berkas audio.

---

## 4. Eksekusi Uji & Kebijakan "No Post-Hoc Tuning"

1. Seluruh kode pengujian dijalankan tepat 1 kali (*single run*).
2. Tidak ada penyesuaian parameter (*hyperparameter / threshold tuning*) setelah melihat data hasil eksekusi uji.
3. Seluruh hasil angka dilaporkan apa adanya dalam format laporan standar, disertai *confidence intervals* dan catatan kegagalan (jika ada).
