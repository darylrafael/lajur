# Gate G1-v2 Amendment: Invalidation & Repair Protocol (Minggu 4d)

**Document:** `docs/gates/G1-v2-amendment.md`  
**Milestone:** Minggu 4d — Audit Integritas G1-v2, Pembatalan Resmi, dan Protokol Perbaikan v2b  
**Date:** 2026-10-26  
**Author:** Daryl (Solo Dev)  
**Status:** FORMAL AMENDMENT — COMMITTED BEFORE CODE CHANGES  

---

## 1. Vonis Pembatalan Resmi (*Formal Invalidation Verdict*)

Berdasarkan aturan objektif pembatalan pada instruksi Minggu 4d (Aturan 4), hasil pengukuran **Gate G1-v2** yang tercatat pada [`docs/gates/G1-v2-results.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/gates/G1-v2-results.md) dengan angka P50 5.169 ms secara resmi dinyatakan **BATAL / TIDAK VALID (*INVALID*)**.

### Pembuktian Kondisi Pembatalan (Aturan 4):

1. **Kondisi (a): Selisih Waktu STT Terukur vs Ekspektasi Fisik $> 1.000\text{ ms}$ pada Mayoritas Giliran (TERBUKTI)**
   - **Ekspektasi Fisik:** Dengan `endpointing=500` ms pada Deepgram Nova-3 dan estimasi RTT jaringan ke Deepgram ~195 ms, waktu deteksi `speech_final` yang diharapkan secara fisik dari akhir ucapan aktif adalah:
     $$T_{\text{expected}} \approx 500\text{ ms (endpointing)} + 195\text{ ms (RTT)} + \approx 100\text{ ms (compute)} \approx \mathbf{795 - 850\text{ ms}}$$
     Bahkan jika dihitung sejak seluruh berkas audio selesai diputar (termasuk jeda hening 1,5 detik):
     $$T_{\text{expected, total}} \approx 1.500\text{ ms (playback)} + 500\text{ ms (endpointing)} + 195\text{ ms} \approx \mathbf{2.195\text{ ms}}$$
   - **Hasil Terukur pada G1-v2:** Median turnaround STT terukur adalah **4.219 ms** (rentang 4.136 – 4.482 ms pada 25 giliran).
   - **Selisih Terukur:**
     $$\Delta T = 4.219\text{ ms} - 850\text{ ms} = \mathbf{3.369\text{ ms}} \gg 1.000\text{ ms}$$
     Selisih melampaui 1.000 ms pada 27 dari 30 giliran (**90% giliran**). Maka **Kondisi (a) Terpenuhi**.

2. **Kondisi (b): Ditemukan Cacat Konkret pada Kode, Pemberian Audio, dan Penanganan Stream (TERBUKTI)**
   - Berdasarkan audit stempel waktu mentah SQLite (`data/turn_events.sqlite3`) dan log eksekusi worker (`task-5639.log` vs `task-5595.log`), selisih ~4,2 detik terbukti bukan latensi inferensi vendor, melainkan akumulasi jeda *timeout* terprogram pada skrip benchmark. Maka **Kondisi (b) Terpenuhi**.

Karena **Kondisi (a)** dan **Kondisi (b)** keduanya terpenuhi secara mutlak, maka sesuai aturan: **v2 DINYATAKAN INVALID**.

---

## 2. Investigasi Cacat Konkret (*Defect Diagnosis*)

Audit mendalam terhadap berkas sumber mengungkap tiga cacat berantai yang menyebabkan angka 4.219 ms:

### Cacat 1: Ketidaksesuaian Frekuensi Cuplikan AudioStream WebRTC
- **Lokasi Kode:** [`eval/scripts/spikes/benchmark_week04_g1_v2.py:352`](file:///c:/Users/Lenovo/Downloads/drivethru/eval/scripts/spikes/benchmark_week04_g1_v2.py#L352)
  ```python
  audio_stream = lk_rtc.AudioStream(track)
  ```
- **Masalah:** Pada SDK LiveKit Python, `lk_rtc.AudioStream(track)` tanpa parameter eksplisit menghasilkan audio terdekode pada frekuensi **48.000 Hz**. Sementara itu, `DeepgramSTTAdapter` diinisialisasi dan membuka WebSocket dengan parameter `sample_rate=16000` (linear PCM 16-bit).
- **Akibat:** Frame audio 48kHz dikirimkan mentah ke WebSocket Deepgram yang mengira formatnya 16kHz. Audio terdistorsi 3x lipat (*chipmunk effect*), sehingga algoritma VAD/endpointing Nova-3 tidak mendeteksi ucapan manusia secara wajar dan tidak pernah memicu event `speech_final`.

### Cacat 2: Akumulasi Waktu Timeout dan Fallback Palsu
- **Lokasi Kode:** [`eval/scripts/spikes/benchmark_week04_g1_v2.py:465-496`](file:///c:/Users/Lenovo/Downloads/drivethru/eval/scripts/spikes/benchmark_week04_g1_v2.py#L465-L496)
  ```python
  # 1. Loop audio memutar 1.5 detik trailing silence pasca t_speech_end:
  if t_speech_end == 0.0 and samples_sent >= active_samples:
      t_speech_end = time.perf_counter()
  # ... loop berlanjut mengirimkan 1.500 ms sisa chunk hening ...

  # 2. Skrip menunggu endpointing:
  if not stt_done_event.is_set():
      try:
          await asyncio.wait_for(stt_done_event.wait(), timeout=1.5)  # Timeout 1: 1.5s
      except asyncio.TimeoutError:
          await dg_stream.finalize()
          try:
              await asyncio.wait_for(stt_done_event.wait(), timeout=1.5)  # Timeout 2: 1.5s
          except asyncio.TimeoutError:
              print("[Warning] Deepgram STT endpointing timed out...")

  # 3. Fallback timestamp:
  if t_stt_final_captured is None:
      t_stt_final_captured = time.perf_counter()
  ```
- **Kronologi Waktu:**
  1. $T = 0$: `t_speech_end` dicatat saat cuplikan aktif selesai.
  2. $T = +1.500\text{ ms}$: Loop selesai memutar sisa jeda hening 1,5 detik.
  3. $T = +3.000\text{ ms}$: `asyncio.wait_for` pertama (timeout 1,5s) habis karena Deepgram tidak mengirimkan `speech_final`.
  4. $T = +4.220\text{ ms}$: `asyncio.wait_for` kedua (pasca-finalize) habis atau terhenti pada ~1,22 detik.
  5. $T = +4.220\text{ ms}$: Skrip mengeksekusi fallback `t_stt_final_captured = time.perf_counter()`.
- **Hasil:** Nilai `t_stt_final_captured - t_speech_end` selalu menghasilkan tepat $\approx \mathbf{4.220\text{ ms}}$ di setiap giliran! Angka ini adalah durasi tunggu timeout skrip, bukan performa jaringan maupun model STT.

### Cacat 3: Penyamaran Transkrip (*Transcript Masking*)
- **Lokasi Kode:** [`eval/scripts/spikes/benchmark_week04_g1_v2.py:498`](file:///c:/Users/Lenovo/Downloads/drivethru/eval/scripts/spikes/benchmark_week04_g1_v2.py#L498)
  ```python
  transcript = turn_transcript_captured or dg_stream.last_transcript or clip["utterance"]
  ```
- **Masalah:** Karena STT timeout dan menghasilkan string kosong, skrip diam-diam mengambil teks skenario `clip["utterance"]` sebagai fallback, menyamarkan kegagalan total STT dan meneruskannya ke Groq & ElevenLabs seolah-olah transkripsi berhasil.

---

## 3. Spesifikasi Perbaikan Minimal (*Minimal Fix*)

Perbaikan dibatasi secara ketat hanya pada tiga titik berikut tanpa mengubah arsitektur atau parameter model:

1. **Konfigurasi Eksplisit Resampling WebRTC AudioStream:**
   Ubah instansiasi `AudioStream` di sisi penerima worker agar meresample frame WebRTC menjadi 16kHz mono 16-bit:
   ```python
   audio_stream = lk_rtc.AudioStream(track, sample_rate=16000, num_channels=1)
   ```
2. **Pendaftaran Listener Sebelum Publikasi Track:**
   Daftarkan listener `room_agent.on("track_subscribed")` sebelum memanggil `room_client.local_participant.publish_track()` untuk mengeliminasi *race condition* penerimaan track audio WebRTC.
3. **Penyelarasan Siklus Pengiriman Audio dan Deteksi Endpointing:**
   - Hentikan pemutaran trailing silence berlebih jika `stt_done_event` telah terpicu.
   - Hilangkan penundaan ganda 1,5s + 1,5s yang menjebak fallback pada 4,2 detik.
   - Larang penyamaran transkrip kosong: jika STT gagal mentranskripsi, catat secara eksplisit sebagai kegagalan turn tanpa memalsukan latensi.
4. **Verifikasi Unit Test:**
   Tambahkan unit test verifikasi format audio PCM 16kHz dan penanganan stempel waktu turn.

---

## 4. Protokol Eksekusi G1-v2b (*Pre-Registered Execution*)

1. **Jumlah Giliran:** **20 giliran percakapan terdaftar (*20 pre-registered turns*)** mencakup 4 kategori inti (Simple, Combo/Quantity, Modifier/Size, Correction/Undo).
2. **Ambang Batas Latensi (SAMA PERSIS, TIDAK DIUBAH):**
   - **Target Utama (PRD §4.5):** $P50 \le 1.200\text{ ms}$
   - **Owner Fallback (ADR-0013 Opsi B):** $P50 \le 1.800\text{ ms}$ DAN $P95 \le 3.000\text{ ms}$
3. **Batasan Kuota:**
   - ElevenLabs saat ini: **1.944 karakter**. Cadangan wajib: **600 karakter**. Kuota maksimal yang boleh dipakai: **1.344 karakter**. (20 giliran templat deterministik $\times \approx 25$ karakter $\approx 500$ karakter, aman).
   - Groq Qwen-27b: Status 200 OK.
4. **Aturan Eksekusi:**
   - Dijalankan tepat **SATU KALI (*single run*)**.
   - Dilarang mengubah parameter setelah melihat hasil.
   - Hasil dicatat di [`docs/gates/G1-v2b-results.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/gates/G1-v2b-results.md). Jika meleset, tulis **FAIL**, jangan tulis PASS.
