# Gate G1c Protocol Addendum: Measurement Audit & Final Verification Round

**Document:** `docs/gates/G1c-addendum.md`  
**Milestone:** Minggu 2f — Gerbang G1c Audit & Final Measurement Round  
**Status:** Pre-registered (Committed prior to audit execution)  
**Date:** 2026-10-20  
**Author:** Daryl (Solo Dev) & Implementation Agent  
**Rigidity Clause:** *Protokol addendum ini dikomit ke repositori git sebelum eksekusi pengujian baru dijalankan. Dokumen protokol terdahulu (`G1b-protocol.md` dan `G1c-protocol.md`) tetap dipertahankan tanpa perubahan.*

---

## 1. Konteks & Alasan Addendum

Berdasarkan audit hasil pengujian fase G1c terdahulu, ditemukan sejumlah anomali metodologis dan temuan baru yang memerlukan verifikasi terarah:
1. **Anomali Skor Akurasi Intent E1 (Konstan 50.0%):**
   Hasil 50.0% yang identik di keempat konfigurasi model terbukti berasal dari kesalahan pada skrip evaluasi (`benchmark_g1c.py`), di mana nama item dicocokkan langsung terhadap `item_id` (underscore vs spasi) dengan nilai fallback `0.5` bila tidak cocok, sehingga menghasilkan 50.0% semu. Evaluasi perlu diaudit secara terbuka (menampilkan perbandingan 10 ujaran berdampingan), diperbaiki, dan diuji ulang pada minimal 60 skenario baku yang dinilai pada tingkat intent dan keranjang akhir (*resulting cart*).
2. **Anomali Latensi Endpointing E2 (63 ms pada Jeda 500 ms):**
   Nilai 63 ms terjadi karena klip audio dipotong tepat pada akhir ujaran tanpa menyertakan keheningan ekor (*trailing silence*), lalu skrip langsung mengirim sinyal `CloseStream`. Deepgram langsung melakukan *stream flush* tanpa menunggu jendela keheningan endpointing. Pengujian ulang wajib menyertakan keheningan ekor minimal 1.200 ms agar jeda endpointing 150, 300, dan 500 ms terpicu secara wajar dari audio hening sebelum koneksi ditutup.
3. **Ketersediaan Kunci ElevenLabs di `.env`:**
   Ditemukan kunci API ElevenLabs free tier pada environment lokal. Hal ini memerlukan audit resmi terhadap ketentuan lisensi (komersial/non-komersial, atribusi, pelatihan data/retensi) serta pengukuran empiris TTFB pada 30 frasa balasan bot baku (5 pengulangan interleaved) dan verifikasi kapabilitas streaming.
4. **Pengukuran Risiko Hosting Lokal (Docker Constraint):**
   Menguji ketahanan pemrosesan VAD dan deteksi giliran (*turn detection*) pada lingkungan Docker lokal yang dibatasi secara ketat pada 0.1 vCPU dan 512 MB RAM guna mengukur apakah agen mampu memproses audio real-time (Real-Time Factor, RTF < 1.0).

---

## 2. Batasan Mutlak (*Hard Constraints*)

1. **Aturan Kartu Kredit (*Card-Free Constraint*):** Sistem tidak akan menggunakan layanan apa pun yang mewajibkan kartu pembayaran/kredit.
2. **Klausul Netralitas:** Agen tidak boleh merekomendasikan pilihan antara Opsi A, B, atau C pada ADR-0013.
3. **Klausul Penghentian Wajib (*Stop and Ask Me*):**
   Agen wajib berhenti dan meminta konfirmasi pengguna jika:
   - Perbaikan bug skoring atau timing mengubah angka kunci lebih dari 30%.
   - Suatu layanan ternyata mewajibkan kartu kredit.
   - Perilaku API vendor berbeda dari dokumentasi resminya.

---

## 3. Rincian Metodologi Pengujian Addendum

### Task 1: Audit & Pengujian Ulang Akurasi Intent (E1 Redo)
- **Dataset:** Minimal 60 skenario dari `eval/datasets/v0/scenarios.jsonl` (mencakup kategori `simple`, `multi_item`, `correction_undo`, `modifiers_size`).
- **Audit Terbuka (10 Turns):** Menampilkan perbandingan berdampingan untuk 10 ujaran pertama:
  - Teks masukan pengguna (*user utterance*).
  - Output teks/JSON mentah dari model.
  - Intent emas (*gold intent*) dan keranjang yang diharapkan (*expected cart*).
  - Hasil perbandingan detail (tipe intent, item id/name, quantity, modifier).
- **Metrik Skoring Ganda:**
  1. *Intent-level Accuracy:* Persentase pencocokan intent yang diekstrak (tipe aksi, entitas item, jumlah, modifier).
  2. *Resulting-cart Accuracy:* Menerapkan intent ke Cart State Machine (`packages/cart`) deterministik dan membandingkan keranjang akhir terhadap `expected_cart` (items, quantities, modifiers, status).
- **Aturan Pelaporan:** Angka kecepatan (TTFT/Total) wajib dilaporkan berdampingan langsung dengan angka akurasinya. Menyertakan catatan eksplisit mengenai status *gold label* (draft otomatis v0 oleh agen, 20 dari 135 di-spot check manusia).

### Task 2: Pemeriksaan Model ID & Konfigurasi Berpikir
- Mengambil respon mentah JSON dari endpoint daftar model Groq (`/models`) untuk model yang digunakan (`openai/gpt-oss-20b` dan `qwen/qwen3.8-27b`) dengan stempel waktu UTC.
- Mengutip dokumentasi resmi Qwen 27B di Groq terkait mode reasoning dan cara konfigurasinya.
- Menguji parameter resmi Google Gemini untuk meminimalkan/menonaktifkan proses berpikir (*minimal thinking*) pada model Flash-Lite dan mencatat respon/error secara verbatim.

### Task 3: Pengujian Ulang Latensi Endpointing & False Cutoff (E2 Redo)
- **Audio Sintesis:** 10 frasa ujaran ragu-ragu (*hesitation*) dengan jeda hening tengah 300 ms, 500 ms, dan 800 ms.
- **Koreksi Timing Ekor:** Setiap audio ditambahkan keheningan ekor minimal 1.200 ms setelah kata terakhir, sehingga server mendeteksi keheningan alami sebelum skrip mengirim `CloseStream`.
- **Pengaturan Pacing:** Pacing real-time $1.0\times$ (audio dikirim bertahap per 100 ms).
- **Pencatatan Stempel Waktu Eksak:**
  - `t_speech_start`: Waktu audio mulai dikirim.
  - `true_speech_end`: Waktu pengucapan kata terakhir selesai (berdasarkan durasi teks audio sebelum jeda ekor).
  - `t_speech_final`: Waktu event `speech_final=True` diterima dari Deepgram.
  - Latensi Turnaround = `t_speech_final - true_speech_end`.
- **Tabel Tunggal:** Menyajikan hasil pengujian parameter 150 ms, 300 ms, dan 500 ms dalam satu tabel yang memuat $n$, False Cutoff Rate (%), serta Latensi Turnaround (P50, P95, Mean dengan 95% Bootstrap CI).
- Menampilkan 5 baris data mentah (*raw timestamped rows*).

### Task 4: Pengujian & Audit Ketentuan ElevenLabs Free Tier (E3 Redo)
- Mengutip syarat dan ketentuan resmi ElevenLabs Free Tier (URL, tanggal akses): status penggunaan non-komersial, kewajiban atribusi, retensi/pelatihan data pada audio input, dan batasan komersial.
- Menguji 30 frasa balasan kasir bot baku drive-thru, masing-masing diulang 5 kali secara bersilang (*interleaved*, total 150 request).
- Mengukur: Time to First Audio Byte (TTFB), kecepatan transfer, verifikasi apakah API mendukung chunked/streaming audio, dan stabilitas latensi (P50, P95, Mean, 95% Bootstrap CI).

### Task 5: Pengukuran Ketahanan Bebas Kartu pada Kontainer Docker (0.1 CPU, 512 MB RAM)
- Menjalankan pengujian beban inferensi VAD (Silero) dan agent loop lokal di dalam kontainer Docker dengan batasan:
  `--cpus="0.1" --memory="512m" --memory-swap="512m"`
- Mengukur waktu pemrosesan per detik audio input (Real-Time Factor, RTF = waktu proses / durasi audio).
- Mendokumentasikan aturan sleep/spin-down dari hosting gratis (Render / Zeabur) untuk worker WebSocket outbound tanpa HTTP traffic masuk, serta mekanisme resmi menjaga worker tetap aktif tanpa melanggar ketentuan layanan (*Terms of Service*).
