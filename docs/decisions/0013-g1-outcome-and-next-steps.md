# ADR-0013: Hasil Gerbang G1 dan Langkah Selanjutnya (G1 Outcome and Next Steps)

## Status
Accepted by owner

## Konteks
Gerbang G1 (akhir Minggu 2) menetapkan kriteria kelayakan suara (*speech viability*) sebagai berikut (`PROJECT_PLAN.md` §3.2):
> "Tidak ada vendor STT dengan KER ≤ 15% pada set ucapan ID–EN bersih dan latensi turn estimasi ≤ 1,2s"

Berdasarkan audit pengukuran representatif G1b, G1c, dan audit akhir G1f pada 60 skenario baku:
1. **Akurasi STT (KER ≤ 15%):** Berstatus **PROVISIONAL**. Kedua kandidat memenuhi kriteria pada dataset sintetis bersih (Deepgram Nova-3: 3.89%, Groq Whisper Turbo: 11.11%). Uji paired bootstrap selisih KER ($\bar{\Delta} = -7.22\%$) memiliki 95% CI `[-15.0%, 0.0%]`, yang menyentuh angka nol (belum signifikan secara statistik mutlak pada $n=30$). Data suara manusia nyata belum memiliki ground-truth teks untuk diukur akurasinya *(status: asumsi belum terukur / assumption, not measured)*.
2. **Latensi Turn Estimasi (≤ 1.2s):** Berstatus **NOT DEMONSTRATED**.
   - **STT Streaming (Deepgram Nova-3):**
     - Angka turnaround pasca-ucapan **108.8 ms** pada skrip uji G1f dinyatakan **TIDAK KREDIBEL (*not credible: speech-end reference suspected wrong, to be re-measured on the real pipeline in Minggu 4*)**.
     - *Penjelasan Teknis Batasan Fisika Endpointing:* Algoritma endpointing Deepgram membutuhkan jendela keheningan terus-menerus $\ge 500\text{ ms}$ setelah ucapan selesai sebelum memancarkan event `speech_final=True`. Secara fisik, latensi turnaround dari akhir ucapan nyata (*true speech end*) ke transkrip final tidak mungkin lebih kecil dari $500\text{ ms} + \text{network RTT}$ (~700 ms dari Indonesia). Angka 108.8 ms (dan angka negatif pada varian 150/300ms) terbukti merupakan artefak misalignment penanda waktu hening pada file sintetis skrip offline.
     - Estimasi latensi STT streaming dari akhir ucapan yang lebih realistis mengacu pada audit G1d: P50 = **524.4 ms** (Mean 549.4 ms, P95: 856.2 ms).
   - **LLM Reasoning & Non-Reasoning (Groq & Gemini):**
     - Groq `qwen/qwen3.8-27b` (Non-reasoning): Warm TTFT P50 = **258.5 ms – 419.1 ms** (P95: 574.2 ms), Akurasi Intent: **73.3%**, Akurasi Keranjang Akhir (*Resulting Cart*): **76.7%**.
     - Groq `openai/gpt-oss-20b` (`reasoning_effort="low"`): Warm TTFT P50 = **616.6 ms**, Akurasi Keranjang: **56.7%**.
     - Google `gemini-3.5-flash-lite`: Warm TTFT P50 = **794.2 ms** (burst) / **7.303 ms** (beban antrean 60 giliran), Akurasi Keranjang: **76.7%**.
   - **TTS Terukur (ElevenLabs vs Gemini):**
     - **ElevenLabs Free Tier (`eleven_flash_v2_5`):** Terukur resmi via API key `.env`. Mendukung chunked streaming. TTFB audio pertama P50 = **126.8 ms** (P95: 157.4 ms). Namun terikat ketentuan gratis: strictly non-commercial only (Section 1(c) ToS), wajib atribusi publik, data input default dipakai untuk pelatihan model AI, dan kuota 10.000 karakter/bulan.
     - **Gemini API TTS:** TTFB P50 = **3.036,4 ms** (tanpa streaming, melatih model dari input).
     - **Azure Speech, Cartesia, Soniox:** Mewajibkan kartu kredit (*excluded: card required*).
   - **Rentang Estimasi Latensi Komponen Pra-Pipeline:**
     - STT Nova-3 (~524 ms) + Groq Qwen-27b (258–419 ms) = **782–943 ms** (pra-TTS).
     - Jika ElevenLabs free tier digunakan untuk demo: 782–943 ms + 127 ms TTFB = **~909–1.070 ms**. Angka ini merupakan estimasi terisolasi komponen parsial dan **BELUM DIBUKTIKAN (*not demonstrated*)** pada pipeline LiveKit utuh dengan overhead network WebRTC, browser audio context, dan sinkronisasi state machine.
     - Ambang batas 1.2 detik secara resmi dicatat sebagai **belum terbukti / not demonstrated**.

Batasan proyek (*Hard Constraint*): Sistem tidak akan menggunakan layanan pihak ketiga yang mewajibkan kartu pembayaran/kredit (*card-free constraint*).

---

## Keputusan Pemilik Proyek (Owner Decision - Minggu 2g)

Pemilik proyek (Daryl) telah meninjau bukti audit dan menetapkan keputusan resmi berikut:

1. **Hasil Gerbang G1: Opsi A-Bersyarat (A-Conditional)**
   - Target latensi turn **$\le 1,2\text{ detik}$ dipertahankan**.
   - Gerbang G1 dicatat secara jujur sebagai **"NOT DEMONSTRATED"** (bukan PASS).
   - Dibuat pra-registrasi pengukuran latensi end-to-end pada pipeline nyata di Minggu 4 ([`docs/gates/G1-minggu4-measurement.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/gates/G1-minggu4-measurement.md)) sebagai titik keputusan definitif (*decision point*).
   - **Klausul Fallback Opsi B:** Jika pengukuran live pipeline di Minggu 4 gagal memenuhi target 1.2 detik, pemilik proyek akan langsung beralih ke **Opsi B** dengan angka target baru yang ditetapkan dari pertimbangan *user-experience* (UX) sebelum pengukuran dilakukan.
2. **Keputusan Vendor Text-to-Speech (TTS):**
   - Pemilihan vendor TTS komersial tetap berstatus **OPEN** (ADR-0011).
   - Pemilik proyek menyetujui adopsi **ElevenLabs Free Tier secara kondisional khusus untuk demo portofolio non-komersial**, dengan kewajiban menampilkan atribusi publik ("elevenlabs.io" / "11.ai") dan disclaimer non-komersial pada aplikasi web.
3. **Kandidat Primer STT dan LLM:**
   - **STT:** Deepgram Nova-3 WebSocket streaming diterima sebagai kandidat utama (ADR-0010, subjek pengukuran Minggu 4).
   - **LLM:** Groq-hosted `qwen/qwen3.8-27b` (Non-reasoning) diterima sebagai kandidat utama (ADR-0012, subjek pengukuran Minggu 4).
   - **Gemini Free Tier:** Dilarang untuk memproses data suara/teks pengunjung nyata karena klausul pelatihan data melanggar ADR-0005.

---

## Baseline LLM dan Isu Terbuka (LLM Baseline & Open Issues)

Pada audit akhir G1f (60 skenario baku), performa parsing intent LLM berbasis teks menunjukkan hasil baseline sebagai berikut:
- **Intent Accuracy:** **73.3%** (sama pada Qwen-27b dan Gemini Flash-Lite).
- **Resulting Cart Accuracy:** **76.7%** (Qwen-27b dan Gemini Flash-Lite).
- **Per Kategori:**
  - Simple Orders: **80.0%**
  - Quantity & Combo: **89.5%** (Qwen) / **94.7%** (Gemini)
  - Modifiers & Size: **100.0%** (Qwen) / **93.3%** (Gemini)
  - Correction / Undo: **0.0%** Intent Match (18.2% Cart Match).

### Analisis Hipotesis Diskrepansi:
1. **Cakupan Alias Menu:** Sebagian kegagalan disebabkan oleh variasi istilah yang belum terdaftar di `MenuService` (misal variasi slang atau penamaan menu alternatif).
2. **Ketiadaan State Keranjang pada Prompt Evaluasi:** Prompt benchmark mengevaluasi setiap giliran tanpa menyuntikkan isi keranjang belanja saat ini (*current cart context*), sehingga ujaran bertahap atau korektif sulit disimpulkan secara tepat oleh LLM.
3. **Bias Label Emas Sintetis pada Koreksi/Undo:** Skrip gold intent awal (`generate_gold_intents.py`) secara otomatis menghasilkan intent sintetis `undo` untuk skenario berlabel koreksi, padahal model LLM secara wajar langsung memancarkan intent `add_item` dengan item pengganti.
4. **Tindak Lanjut:** Penyelidikan mendalam, penyempurnaan alias menu, dan pengayaan penanganan koreksi dialihkan ke siklus **Minggu 3 (Cart State Machine)** dan evaluasi komprehensif **Minggu 8**.

---

## State Machine yang Digunakan untuk Penilaian (State Machine Used for Scoring)

Untuk menghitung metrik *Resulting Cart Accuracy* pada evaluasi G1f:
- Evaluasi dijalankan menggunakan fungsi `evaluate_intent_and_cart()` di `eval/scripts/spikes/benchmark_g1f.py`.
- Komponen yang digunakan adalah modul deterministik `MenuService` dari `packages/cart/src/lajur_cart/menu.py`.
- **Fungsi yang Tersedia Saat Ini:**
  - Pencocokan nama/alias menu ke `item_id` baku.
  - Resolusi harga integer rupiah deterministik dari `menu.json`.
  - Agregasi item dan kuantitas sederhana ke struktur baris keranjang belanja.
- **Apa yang Masih Harus Dibangun di Minggu 3:**
  - *Cart State Machine* percakapan penuh (ADR-0001 & ADR-0002) yang mencakup manajemen sesi, transisi status pesanan (`idle` $\to$ `ordering` $\to$ `confirming` $\to$ `checkout`), validasi stok bahan/ketersediaan, aturan kombinasi paket combo dan modifier yang sah, serta logika deterministik penanganan pembatalan (*cancellation/undo*) dan resolusi konflik pesanan.

---

## Opsi Arsitektur Tambahan (Terdokumentasi, Tanpa Implementasi di Minggu 2)

### 1. Pemisahan Dua Metrik Latensi Bernama (Dual Latency Metrics)
- **Time to First Acknowledgment (TTFA):** Waktu dari akhir ucapan pelanggan hingga audio respons awal ("Baik kak,") terdengar.
- **Time to Substantive Reply (TTSR):** Waktu dari akhir ucapan hingga audio respons substansi pesanan selesai dipancarkan.
- *Guardrail ADR-0001:* Audio acknowledgment awal dilarang mengonfirmasi pesanan sebelum validasi Cart State Machine selesai.

### 2. Jalur Cepat Deterministik (Deterministic Fast Path)
- Mencocokkan ujaran sederhana langsung ke `packages/cart` tanpa memanggil LLM.
- Menghindari latensi LLM (menghemat ~250–800 ms) pada pesanan langsung.

### 3. Panggilan LLM Parsial Spekulatif (Speculative Partial LLM Calling)
- Memulai pengiriman prompt LLM saat transkrip parsial stabil sebelum endpointing hening selesai.
- *Guardrail ADR-0001:* Mutasi keranjang dan pemancaran audio TTS wajib menunggu event transkrip final STT.

---

## Konsekuensi & Batasan
- Keputusan gerbang G1 secara resmi ditutup dengan status **A-bersyarat (not demonstrated)**.
- Protokol pengukuran pipeline langsung di Minggu 4 telah terkunci di `docs/gates/G1-minggu4-measurement.md`.
- Cabang `feat/minggu-2-spikes` **tidak akan di-merge ke `main`** dan pekerjaan Minggu 3 **tidak akan dimulai** sebelum seluruh dokumen Minggu 2g ter-commit dan CI tervalidasi.

