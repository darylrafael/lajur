# Gate G1c Protocol: Measuring the Levers (Speech & Latency Sensitivity)

**Document:** `docs/gates/G1c-protocol.md`  
**Milestone:** Minggu 2e — Gerbang G1c  
**Status:** Pre-registered (Committed prior to experiment execution)  
**Date:** 2026-10-19  
**Author:** Daryl (Solo Dev) & Implementation Agent  
**Rigidity Clause:** *Protokol ini dikomit ke git sebelum eksperimen dijalankan. Protokol tidak dapat diubah setelah komit tanpa persetujuan tertulis eksplisit dari pengembang (Daryl).*

---

## 1. Konteks & Tujuan

Setelah audit Minggu 2d membuktikan bahwa:
1. Deepgram Nova-3 streaming beroperasi pada latensi P50 = 524.4 ms dari *true speech end* (dengan pacing real-time $1.0\times$).
2. Silero VAD detection delay (P50 = 386 ms) dan `min_delay` tidak bertambah linear, melainkan di-clamp oleh `endpointing_delay`.
3. Latensi pra-TTS warm connection (Nova-3 + Gemini Flash-Lite) adalah ~1.364 ms, melampaui batas 1.200 ms sebelum audio TTS mulai disintesis.

Fase G1c melakukan pengukuran empiris terhadap "tuas-tuas" (*levers*) teknis yang dapat digerakkan dalam arsitektur untuk memahami trade-off secara presisi tanpa berspekulasi:
- **Tuas 1 (LLM Reasoning Overhead & Small Model):** Apakah penonaktifan *thinking/reasoning tokens* mempercepat TTFT, dan bagaimana performa model kecil non-reasoning di Groq?
- **Tuas 2 (Endpointing vs False Cutoff Trade-off):** Berapa latensi dan risiko pemotongan ucapan prematur (*false cutoff*) saat endpointing Deepgram disetel ke 150 ms, 300 ms, dan 500 ms pada audio dengan jeda ragu-ragu (*hesitation*)?
- **Tuas 3 (Survei & Pengukuran TTS Card-Free):** Apakah terdapat API TTS resmi yang benar-benar tanpa kartu kredit (*card-free*), mendukung Bahasa Indonesia, dan dapat diukur latensinya?
- **Tuas 4 (Survei Hosting Publik Worker):** Pilihan hosting publik gratis tanpa kartu untuk menjalankan LiveKit Python agent worker.
- **Tuas 5 (Opsi Arsitektur Terdokumentasi pada ADR-0013):** Formulasi metrik terpisah (Acknowledgment vs Substantive), fast-path deterministik, dan spekulasi parsial STT.

---

## 2. Batasan Mutlak (*Hard Constraints*) & Kriteria Gerbang

1. **Ambang Batas Gerbang G1 (§3.2 Verbatim):**
   > *"Tidak ada vendor STT dengan KER ≤ 15% pada set ucapan ID–EN bersih dan latensi turn estimasi ≤ 1,2s"*  
   Ambang batas latensi turn **tetap $\le 1.200\text{ ms}$ (1.2 detik)**, tidak diubah.
2. **Hard Constraint Kartu Kredit:**
   Sistem tidak akan menggunakan layanan apa pun yang mewajibkan kartu pembayaran/kredit (*card-free constraint*). Setiap vendor yang diuji wajib diverifikasi status pendaftarannya dengan URL dan tanggal. Vendor yang membutuhkan kartu langsung dieksklusi (*excluded: card required*).
3. **Penyusunan Keputusan:**
   Agen dilarang memilihkan Opsi A, B, atau C pada ADR-0013. Opsi B dilarang mengajukan angka target turunan dari hasil ukur (wajib justifikasi UX saja dan ditandai "to be decided by the owner").

---

## 3. Metodologi Pengujian & Aturan Statistik

1. **Ukuran Sampel (*Sample Size*):**
   Minimal **30 turns / skenario** per konfigurasi eksperimen.
2. **Eksekusi Bersilang (*Interleaved Execution*):**
   Untuk mengontrol variansi beban server cloud free-tier pada jam sibuk, pengujian tidak dijalankan berurutan (misal: seluruh Konfig A selesai baru Konfig B), melainkan **bersilang per giliran (interleaved)**:  
   Turn 1 diuji pada Konfig A $\to$ Konfig B $\to$ Konfig C, lalu Turn 2 diuji pada Konfig A $\to$ Konfig B $\to$ Konfig C, dan seterusnya.
3. **Statistik yang Dilaporkan:**
   - Median (P50)
   - Persentil ke-95 (P95)
   - Rata-rata (*Mean*) dengan Selang Kepercayaan Bootstrap 95% (10.000 kali percontohan ulang).
4. **Kondisi Sesi:**
   Menggunakan koneksi hangat (*warm connection*, koneksi HTTP/WebSocket yang di-reuse dalam session pool) untuk merefleksikan agent worker sesi langsung.
5. **Pencatatan Model ID Eksak:**
   Setiap panggilan API wajib mencatat *resolved model ID* dan parameter yang dikirim.

---

## 4. Desain Rinci Eksperimen (E1 – E5)

### Eksperimen E1: LLM Reasoning Overhead & Evaluasi Model Kecil
- **Tujuan:** Mengukur overhead latensi TTFT akibat proses *thinking/reasoning* pada model LLM, serta mengevaluasi model non-reasoning ringan tanpa kartu.
- **Kandidat Model & Konfigurasi:**
  1. **Google Gemini Flash-Lite Pinned (`gemini-3.5-flash-lite` via `gemini-flash-lite-latest`):**
     - Konfig A.1 (Default thinking): Panggilan standar sesuai default vendor.
     - Konfig A.2 (Minimal/Off thinking): Mengatur `thinkingConfig: {"thinkingBudget": 0}` (atau batas minimum sesuai dokumentasi resmi Google AI).
  2. **Groq-Hosted `openai/gpt-oss-20b`:**
     - Konfig B.1 (Default).
     - Konfig B.2 (Thinking minimal/off bila didukung API).
  3. **Groq Free-Tier Small Non-Reasoning (`llama-3.1-8b-instant`):**
     - Verifikasi resmi: Card-free: ya, terms data, dukungan JSON mode, kualitas bahasa Indonesia.
     - Konfig C: Pengujian streaming dengan JSON mode.
- **Metrik Terukur per Turn (Interleaved pada 30 skenario):**
  - Warm Time to First Token (TTFT)
  - Warm Time to First Sentence (tanda baca pertama: `.`, `?`, `!`, `\n`)
  - Total Response Time
  - Akurasi Intent terhadap Gold Label: Mengekstrak array intent dan mencocokkan dengan `expected_intents` skenario baku.
  - **Caveat Gold Label:** *Gold label dibuat secara otomatis oleh skrip agent v0; baru 20 dari 135 skenario yang telah di-spot-check oleh manusia.*

---

### Eksperimen E2: Trade-off Endpointing Deepgram Nova-3 vs False Cutoff
- **Tujuan:** Mengukur korelasi antara parameter jeda *endpointing* Deepgram Nova-3 terhadap latensi respon dan risiko pemotongan kalimat prematur saat pelanggan ragu-ragu (*hesitation*).
- **Nilai Parameter Acuan:**
  - Pada pengujian audit Minggu 2d (latensi 524 ms), parameter endpointing di URL tidak disetel secara eksplisit, sehingga menggunakan nilai default server Deepgram (~300 ms).
- **Variasi Nilai Endpointing yang Diuji:**
  1. `endpointing=150` (150 ms — sangat agresif)
  2. `endpointing=300` (300 ms — standar streaming)
  3. `endpointing=500` (500 ms — konservatif)
- **Dataset Uji Jeda Ragu-ragu (*Hesitation Audio Dataset*):**
  - Mengambil skenario yang memuat jeda/koreksi (misal kategori `undo_gajadi`, `hesitation_pause`, atau kalimat pesanan bertingkat).
  - Menyintesis audio menggunakan Edge-TTS (diizinkan khusus untuk audio uji) dengan menyisipkan jeda hening buatan di titik jeda alami:
    - Jeda 300 ms
    - Jeda 500 ms
    - Jeda 800 ms
  - Total: minimal 30 klip uji dengan variasi jeda hening tengah.
- **Definisi False Cutoff (Tegas):**
  *False Cutoff terjadi jika Deepgram memancarkan event transkrip final (`speech_final: True` atau `is_final: True` yang menyelesaikan ujaran) pada saat jeda tengah kalimat berlangsung, sebelum kata-kata terakhir dari pesanan pelanggan selesai diucapkan.*
- **Output:** Tabel trade-off: `Endpointing (ms)` vs `Latensi Turnaround (P50/P95)` vs `False Cutoff Rate (%)`.

---

### Eksperimen E3: Survei & Pengukuran TTS Card-Free Resmi
- **Tujuan:** Menemukan dan mengukur API TTS resmi yang memenuhi kriteria *Card-free Hard Constraint*.
- **Kandidat Survei:**
  1. **ElevenLabs Free Tier:** Cek URL pendaftaran resmi, apakah mewajibkan kartu kredit, ketentuan penggunaan non-komersial/portofolio, dukungan bahasa Indonesia, dan dukungan streaming WebSocket.
  2. **Google Gemini API TTS:** Verifikasi apakah Gemini Developer API (Google AI Studio) menyediakan endpoint text-to-speech native tanpa Google Cloud Billing.
  3. **Azure Cognitive Services Speech:** Cek apakah kredensial resmi tersedia di `.env` (hanya jika ada kunci dari pengguna).
  4. **Kandidat lain dari `vendor-facts-2026-10.md`** (Cartesia Sonic, Soniox TTS, dsb.).
- **Prosedur Pengukuran (Bila Ada yang Lolos Kualifikasi Card-Free):**
  - Menguji 30 frasa balasan bot baku, 5 kali pengulangan interleaved, mengukur Time to First Audio Byte (TTFB) streaming pada P50 dan P95.
  - Dokumentasikan klausul pelatihan data (*data training policy*).
- **Klausul Kegagalan:** Jika tidak ada satu pun vendor TTS resmi yang card-free dan mendukung Bahasa Indonesia, catat secara eksplisit: *"no card-free official TTS found"* dan pertahankan tabel analisis sensitivitas alokasi TTFB.

---

### Eksperimen E4: Survei Hosting Publik Worker (30 Menit, Tanpa Deployment)
- **Tujuan:** Mengidentifikasi penyedia hosting publik untuk LiveKit Agent Worker Python yang tidak mewajibkan kartu kredit.
- **Dimensi Survei:**
  - Nama Provider & URL Resmi
  - Kebutuhan Kartu saat Registrasi (*Card Required: Yes/No*)
  - Ketersediaan Wilayah (*Region*, misal Singapura, Jakarta, AS)
  - Perilaku Sleep / Spin-down (*cold start idle timeout*)
  - Batas Sumber Daya (*RAM, CPU, bandwidth*)
  - Ketentuan Penggunaan Portofolio / Non-komersial
- **Aturan:** Hanya riset dokumen resmi; tidak melakukan deployment atau instalasi apa pun.

---

### Eksperimen E5: Opsi Arsitektur Terdokumentasi pada ADR-0013 (Tanpa Implementasi)
Menambahkan 3 bagian arsitektur baru pada [ADR-0013](file:///c:/Users/Lenovo/Downloads/drivethru/docs/decisions/0013-g1-outcome-and-next-steps.md):
1. **Pemisahan Dua Metrik Latensi Bernama:**
   - *Time to First Acknowledgment (TTFA):* Waktu dari akhir ucapan hingga audio pengakuan awal ("Baik kak,", "Siap,", visual keranjang muncul) dipancarkan.
   - *Time to Substantive Reply (TTSR):* Waktu hingga respon substansial penuh (validasi harga, pertanyaan upsell, penutup) selesai.
2. **Jalur Cepat Deterministik (*Deterministic Fast Path*):**
   - Pencocokan alias menu langsung ke Cart State Machine tanpa memanggil LLM untuk ujaran sederhana ("Mau burger satu"), dan memanggil LLM hanya untuk ujaran ambigu/koreksi kompleks.
3. **Panggilan LLM Parsial Spekulatif (*Speculative Partial LLM Calling*):**
   - Memulai pembuatan respon LLM secara spekulatif pada hasil transkrip parsial STT sebelum ucapan selesai.
- **Untuk Setiap Opsi di Atas, Wajib Mendokumentasikan:**
  - Apa yang perlu diukur.
  - Risiko teknis yang diantisipasi.
  - Interaksi terhadap guardrail cascade pipeline pada ADR-0001 (khususnya prinsip deterministik sebelum berbicara).

---

## 5. Korpus Evaluasi

Menggunakan skenario baku yang telah terdefinisi di `eval/datasets/v0/scenarios.jsonl` (30 skenario baku untuk E1, dan subset skenario jeda/koreksi untuk E2).
