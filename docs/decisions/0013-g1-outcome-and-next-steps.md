# ADR-0013: Hasil Gerbang G1 dan Langkah Selanjutnya (G1 Outcome and Next Steps)

## Status
Proposed

## Konteks
Gerbang G1 (akhir Minggu 2) menetapkan kriteria kelayakan suara (*speech viability*) sebagai berikut (`PROJECT_PLAN.md` §3.2):
> "Tidak ada vendor STT dengan KER ≤ 15% pada set ucapan ID–EN bersih dan latensi turn estimasi ≤ 1,2s"

Berdasarkan audit pengukuran representatif G1b dan eksplorasi tuas teknis G1c pada 30 skenario baku:
1. **Akurasi STT (KER ≤ 15%):** Berstatus **PROVISIONAL**. Kedua kandidat memenuhi kriteria pada dataset sintetis bersih (Deepgram Nova-3: 3.89%, Groq Whisper Turbo: 11.11%). Uji paired bootstrap selisih KER ($\bar{\Delta} = -7.22\%$) memiliki 95% CI `[-15.0%, 0.0%]`, yang menyentuh angka nol (belum signifikan secara statistik mutlak pada $n=30$). Data suara manusia nyata belum memiliki ground-truth teks untuk diukur akurasinya.
2. **Latensi Turn Estimasi (≤ 1.2s):** Berstatus **FAIL**. Komponen pra-TTS dalam kondisi warm connection:
   - Deepgram Nova-3 Streaming (P50 = 524.4 ms dari *true speech end*) + Gemini Flash-Lite Warm TTFT (P50 = 794.2 ms) menghasilkan **1.318,6 ms**.
   - Deepgram Nova-3 + Groq GPT-OSS-20b Low Reasoning (P50 = 602.6 ms) menghasilkan **1.127,0 ms** (hanya menyisakan 73 ms untuk TTS).
   - Deepgram Nova-3 + Groq Qwen-27b Non-Reasoning (P50 = 258.5 ms) menghasilkan **782.9 ms** (menyisakan 417 ms untuk TTS).
   - Namun, **seluruh API TTS resmi berbayar mewajibkan kartu pembayaran/kredit**, dan satu-satunya TTS resmi card-free terukur (Gemini API TTS) memiliki TTFB P50 = **3.036,4 ms** serta melatih model dari data input pengguna.

Batasan proyek (*Hard Constraint*): Sistem tidak akan menggunakan layanan pihak ketiga yang mewajibkan kartu pembayaran/kredit (*card-free constraint*).

Dokumen ini memaparkan 3 opsi keputusan teknis beserta trade-off masing-masing untuk diputuskan oleh Daryl (tanpa ada opsi yang dipilihkan secara sepihak oleh agen).

---

## Opsi Keputusan yang Tersedia

### Opsi A: Mempertahankan Target Latensi Turn ≤ 1,2 Detik (Stay the Course)
Mempertahankan ambang batas ketat latensi turn ≤ 1.200 ms sesuai rancangan awal PRD dan PROJECT_PLAN.

**Rekayasa Teknis yang Diperlukan Berdasarkan Data Terukur G1c:**
1. **STT Streaming:** Menggunakan WebSocket streaming native (Deepgram Nova-3) dengan parameter `endpointing=300ms` (P50 latensi turnaround pasca-ucapan: -140 ms s.d. 63 ms). *Catatan: Pengujian E2 membuktikan bahwa menyetel endpointing ke 150 ms menyebabkan False Cutoff Rate melonjak ke 13.3%, memotong ucapan pelanggan yang ragu-ragu.*
2. **Model LLM Non-Reasoning / Low Reasoning Cepat:**
   - Groq `qwen/qwen3.8-27b` terukur mencapai Warm TTFT P50 = **258.5 ms** (P95: 512.1 ms, Mean: 315.0 ms, 95% CI `[275.4 ms, 365.1 ms]`).
   - Groq `openai/gpt-oss-20b` dengan `reasoning_effort="low"` terukur mencapai Warm TTFT P50 = **602.6 ms** (menghemat 216 ms dibanding mode default reasoning).
3. **Chunked Streaming ke TTS:** Begitu klausa pertama terbentuk di LLM, token teks langsung dialirkan ke proses sintesis suara.
4. **Kebutuhan TTS Berlisensi Resmi:** Menemukan atau mengamankan provider TTS streaming resmi yang menyediakan latensi audio pertama (TTFB) ≤ 400 ms tanpa kewajiban kartu kredit *(status saat ini: asumsi belum terukur / tidak ditemukan TTS resmi streaming yang card-free)*.

**Trade-offs Opsi A:**
- **Keuntungan:** Mempertahankan standar latensi interaktif percakapan instan bertaraf internasional (< 1.2 detik). Nilai jual portofolio sangat tinggi jika berhasil dicapai dari Indonesia.
- **Kerugian / Risiko:** 
  - Ketiadaan API TTS resmi streaming card-free menjadi penghalang fatal jika batasan kartu tidak dilonggarkan.
  - Model non-reasoning (Qwen 27B) membutuhkan validasi intent ekstra agar format JSON dan logika pesanan menu tetap stabil pada ujaran kompleks.

---

### Opsi B: Merevisi Target Latensi Turn Berbasis Justifikasi UX (Revise Target with UX Rationale)
Mengubah target Service Level Objective (SLO) latensi turn percakapan demo menjadi target baru yang **ditetapkan oleh pemilik proyek (*to be decided by the owner*)**, berbasiskan prinsip interaksi pengguna (*user experience*) drive-thru daripada sekadar mengikuti batas kemampuan vendor cloud.

**Justifikasi Desain Antarmuka & UX Drive-Thru (Tanpa Menentukan Angka):**
1. **Umpan Balik Visual Keranjang Instan (Visual Acknowledgment):** Pada simulator web drive-thru, layar papan pesanan visual (*digital menu board*) dapat langsung memperbarui item keranjang secara instan begitu intent terdeteksi, memberikan kepastian visual kepada pelanggan bahwa sistem sedang memproses pesanan, sementara audio suara kasir AI mengonfirmasi secara verbal.
2. **Pacing Percakapan Interkom Alami:** Di lingkungan drive-thru fisik, jeda interkom wajar dari kasir manusia (memberikan waktu berpikir bagi pengemudi) lebih disukai daripada sistem yang memotong terlalu cepat atau membalas secara terburu-buru.
3. **Mempertahankan Validasi Keranjang Deterministik (ADR-0001 & ADR-0002):** Memberi cukup waktu bagi mesin *cart state machine* untuk memvalidasi stok, modifier, dan diskon sebelum kasir AI mulai berbicara.

**Trade-offs Opsi B:**
- **Keuntungan:** Realistis dicapai menggunakan tumpukan teknologi *cascade* cloud publik dari Indonesia. Menghindari pemotongan kalimat pelanggan karena VAD dapat mempertahankan jeda wajar (300–500 ms).
- **Kerugian / Risiko:** Klaim latensi proyek di portofolio bergeser dari "sub-second realtime" menjadi "near-realtime drive-thru conversational pacing". Memerlukan pembaruan resmi pada PRD §4.5 dan PROJECT_PLAN §3.2 & §4.5 setelah target angka resmi dikunci oleh pemilik proyek.

---

### Opsi C: Re-scoping Sesuai Tindakan Fallback Rencana (§3.2 Verbatim)
Menerapkan klausul fallback resmi yang telah ditetapkan di `PROJECT_PLAN.md` §3.2:
> *"Pivot ke normalisasi LLM pasca-STT atau turunkan klaim (\"mostly Indonesian + English item names\") dan perluas menu dengan alias. Jika tetap gagal: pindah ke bahasa Inggris saja + ID parsial, dan ubah narasi portofolio"*

**Bentuk Implementasi:**
1. **Pilihan C.1:** Menurunkan klaim pengenalan STT menjadi "mostly Indonesian + English item names" dengan memperbanyak pemetaan alias fonetik menu di `packages/cart` (misal *"french fries"* dipetakan dari varian fonetik *"peren prais"*, *"fren fris"*), sehingga beban akurasi tidak dibebankan mutlak pada model STT.
2. **Pilihan C.2:** Jika integrasi multi-bahasa terbukti terlalu lambat, beralih ke antarmuka utama Bahasa Inggris penuh dengan pengenalan entitas menu Indonesia secara parsial, memanfaatkan model STT/TTS bahasa Inggris yang memiliki ketersediaan provider dan optimasi edge yang lebih matang.

**Trade-offs Opsi C:**
- **Keuntungan:** Memperkecil tantangan teknis code-switching bahasa; memungkinkan penggunaan model STT bahasa Inggris berukuran kecil yang lebih cepat.
- **Kerugian / Risiko:** Mengurangi relevansi produk terhadap pasar lokal restoran cepat saji Indonesia (F&B lokal), serta menurunkan diferensiasi portofolio yang bertumpu pada tantangan *code-switching* bahasa lokal.

---

## Opsi Arsitektur Tambahan (Documented Only, No Implementation)

### 1. Pemisahan Dua Metrik Latensi Bernama (Dual Latency Metrics)
Alih-alih mengukur latensi turn sebagai angka tunggal yang kaku, sistem mendefinisikan dua metrik terpisah:
1. **Time to First Acknowledgment (TTFA):** Waktu dari akhir ucapan pelanggan (*true speech end*) hingga audio respon awal ("Baik kak,", "Siap,", atau bunyi lonceng/indikator visual keranjang) mulai terdengar.
2. **Time to Substantive Reply (TTSR):** Waktu dari akhir ucapan hingga audio respon penuh berisi substansi pesanan, harga, dan klarifikasi selesai dipancarkan.

- **Apa yang Perlu Diukur:** Jeda waktu antara akhir pengucapan acknowledgment awal dan dimulainya kalimat substantif, serta kenyamanan ritme percakapan.
- **Risiko Teknis:** Jika kasir AI mengucapkan "Baik kak," tetapi validasi keranjang menemukan item habis, AI terpaksa meralat di kalimat berikutnya ("Eh maaf kak, itemnya habis"), menimbulkan kejanggalan percakapan (*awkward false acknowledgment*).
- **Interaksi dengan Guardrail ADR-0001:** Audio acknowledgment awal hanya boleh bersifat netral (*filler acoustic* / pengakuan pendengaran), dan **dilarang mengonfirmasi pesanan** sebelum Cart State Machine selesai memvalidasi transaksi secara deterministik.

### 2. Jalur Cepat Deterministik (Deterministic Fast Path)
Untuk ujaran pelanggan yang sederhana dan tidak ambigu (misal: "Pesan burger sapi satu"), sistem mencocokkan alias menu langsung dari transkrip STT ke `packages/cart`, mengeksekusi state machine, dan menghasilkan teks balasan kasir dari template baku tanpa memanggil LLM sama sekali. LLM hanya dipanggil untuk ujaran ambigu, koreksi bertingkat, atau pembatalan kompleks.

- **Apa yang Perlu Diukur:** Rasio ujaran yang berhasil ditangani fast path vs slow path pada korpus 135 skenario, selisih penghematan latensi (tanpa LLM, latensi terpangkas ~250–800 ms), dan *false positive rate*.
- **Risiko Teknis:** Kesalahan pengenalan entitas pada kalimat negatif atau bersyarat ("Mau burger tapi jangan yang sapi") jika regex/alias parser gagal memahami negasi.
- **Interaksi dengan Guardrail ADR-0001:** Sangat selaras dengan ADR-0001 dan ADR-0002 karena validasi state machine tetap 100% deterministik dan bebas dari halusinasi model bahasa.

### 3. Panggilan LLM Parsial Spekulatif (Speculative Partial LLM Calling)
Memulai pengiriman prompt ke LLM secara spekulatif saat STT streaming memancarkan transkrip parsial yang stabil, sebelum jeda hening VAD/endpointing selesai. Jika kata terakhir berubah saat ucapan tuntas, request spekulatif dibatalkan (*abort controller*) dan dipanggil ulang.

- **Apa yang Perlu Diukur:** Rasio pembatalan spekulasi (*cancellation rate*) saat pelanggan melanjutkan ucapan, lonjakan konsumsi token/kuota rate limit, dan penghematan TTFT aktual.
- **Risiko Teknis:** Pemborosan kuota API (terkena HTTP 429 rate limit pada free tier) dan potensi race condition jika respons spekulatif terlanjur diproses ke TTS sebelum pembatalan tiba.
- **Interaksi dengan Guardrail ADR-0001:** Spekulasi hanya boleh menghasilkan draf respons LLM; mutasi state keranjang dan pemancaran audio TTS tetap **wajib menunggu event transkrip final STT (`speech_final`)**.

---

## Konsekuensi & Batasan
- Keputusan gerbang G1 dan pemilihan antara Opsi A, B, atau C sepenuhnya berada di tangan Daryl.
- Cabang `feat/minggu-2-spikes` tidak akan di-merge ke `main` dan pekerjaan Minggu 3 tidak akan dimulai sebelum ada arahan tertulis mengenai opsi mana yang dipilih.
