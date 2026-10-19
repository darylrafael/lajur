# ADR-0013: Hasil Gerbang G1 dan Langkah Selanjutnya (G1 Outcome and Next Steps)

## Status
Proposed

## Konteks
Gerbang G1 (akhir Minggu 2) menetapkan kriteria kelayakan suara (*speech viability*) sebagai berikut (`PROJECT_PLAN.md` §3.2):
> "Tidak ada vendor STT dengan KER ≤ 15% pada set ucapan ID–EN bersih dan latensi turn estimasi ≤ 1,2s"

Berdasarkan hasil audit pengukuran representatif G1b pada 30 skenario baku:
1. **Akurasi STT (KER ≤ 15%):** Berstatus **PROVISIONAL**. Kedua kandidat memenuhi kriteria pada dataset sintetis bersih (Deepgram Nova-3: 3.89%, Groq Whisper Turbo: 11.11%). Namun selang kepercayaan berpasangan 95% masih menyentuh 0.00% (`[-15.0%, 0.0%]`), dan data suara manusia nyata belum memiliki transkrip ground-truth untuk diukur akurasinya.
2. **Latensi Turn Estimasi (≤ 1.2s):** Berstatus **FAIL**. Komponen pra-TTS dalam kondisi warm connection saja (Nova-3 Streaming P50 = 524 ms + Gemini Flash-Lite Warm TTFT P50 = 840 ms) telah mencapai **1.364 ms**, melampaui batas 1.200 ms dengan defisit 164 ms tanpa menyisakan alokasi waktu untuk sintesis suara TTS (TTS TTFB).

Batasan proyek (*Hard Constraint*): Sistem tidak akan menggunakan layanan pihak ketiga yang mewajibkan kartu kredit (*card-free constraint*).

Dokumen ini memaparkan 3 opsi keputusan teknis beserta trade-off masing-masing untuk diputuskan oleh Daryl (tanpa ada opsi yang dipilihkan secara sepihak oleh agen).

---

## Opsi Keputusan yang Tersedia

### Opsi A: Mempertahankan Target Latensi Turn ≤ 1,2 Detik (Stay the Course)
Mempertahankan ambang batas ketat latensi turn ≤ 1.200 ms sesuai rancangan awal PRD dan PROJECT_PLAN.

**Rekayasa Teknis yang Diperlukan untuk Mencapainya:**
1. **STT Streaming:** Menggunakan WebSocket streaming native (Deepgram Nova-3) dengan *endpointing* agresif (~250–300 ms).
2. **LLM Mini / Ultra-Fast Edge:** Mengganti Gemini Flash-Lite (TTFT ~840 ms) dengan model berlatensi sangat rendah, misalnya Groq Llama-3.1-8b-instant (TTFT ~150–250 ms) atau model lokal terkuantisasi (Llama 3.2 3B via Ollama/vLLM) yang berjalan di server yang sama (*co-located*).
3. **Chunked Streaming ke TTS:** Begitu kata pertama atau klausa pertama terbentuk di LLM, token langsung dialirkan ke TTS streaming.
4. **TTS Ultra-Cepat Berlisensi Resmi Tanpa Kartu:** Menemukan provider TTS streaming resmi yang menyediakan latensi audio pertama (TTFB) ≤ 200 ms tanpa kewajiban kartu kredit.

**Trade-offs Opsi A:**
- **Keuntungan:** Mempertahankan standar latensi interaktif percakapan instan bertaraf internasional (< 1.2 detik). Nilai jual portofolio sangat tinggi jika berhasil dicapai dari Indonesia.
- **Kerugian / Risiko:** 
  - Ambang batas hening VAD/endpointing yang agresif (≤ 300 ms) memiliki risiko tinggi memotong ucapan pelanggan di tengah kalimat (*false turn cutoff*) saat pelanggan drive-thru ragu-ragu (*hesitation pauses*).
  - Model LLM yang lebih kecil (misal 8B) memiliki risiko halusinasi ekstraksi intent dan kepatuhan format JSON yang lebih rendah dibanding model yang lebih besar.
  - Sangat sulit menemukan provider TTS streaming resmi card-free dengan TTFB sub-200 ms untuk Bahasa Indonesia.

---

### Opsi B: Merevisi Target Latensi Turn Berbasis Justifikasi UX (Revise Target with UX Rationale)
Mengubah target Service Level Objective (SLO) latensi turn percakapan demo dari P50 ≤ 800 ms / Max ≤ 1.200 ms menjadi **P50 ≤ 1.800 ms – 2.200 ms** (atau rentang toleransi hingga 2.500 ms).

**Justifikasi Desain Antarmuka & UX Drive-Thru:**
1. **Visual UI Feedback Instan (< 500 ms):** Pada simulator web drive-thru, layar papan pesanan visual (*digital menu board*) dapat langsung memperbarui item keranjang secara instan begitu transkrip parsial STT atau intent terdeteksi, sementara audio suara kasir AI mengonfirmasi secara verbal dalam waktu ~1.8–2.0 detik.
2. **Pacing Percakapan Interkom Alami:** Di lingkungan drive-thru fisik, jeda interkom ~1.5–2.0 detik dari kasir manusia dianggap wajar dan tidak mengganggu proses transaksi (memberikan jeda kognitif bagi pengemudi).
3. **Mempertahankan Validasi Keranjang Deterministik (ADR-0001 & ADR-0002):** Memberi cukup waktu bagi mesin *cart state machine* untuk memvalidasi stok, modifier, dan diskon sebelum kasir AI mulai berbicara.

**Trade-offs Opsi B:**
- **Keuntungan:** Realistis dicapai menggunakan tumpukan teknologi *cascade* cloud publik dari Indonesia (Deepgram streaming + Gemini Flash-Lite warm + TTS resmi). Menghindari pemotongan kalimat pelanggan karena VAD dapat mempertahankan jeda wajar (400–500 ms).
- **Kerugian / Risiko:** Klaim latensi proyek di portofolio bergeser dari "sub-second realtime" menjadi "near-realtime drive-thru conversational pacing". Memerlukan pembaruan resmi pada PRD §4.5 dan PROJECT_PLAN §3.2 & §4.5.

---

### Opsi C: Re-scoping Sesuai Tindakan Fallback Rencana (§3.2 Verbatim)
Menerapkan klausul fallback resmi yang telah ditetapkan di `PROJECT_PLAN.md` §3.2:
> *"Pivot ke normalisasi LLM pasca-STT atau turunkan klaim (\"mostly Indonesian + English item names\") dan perluas menu dengan alias. Jika tetap gagal: pindah ke bahasa Inggris saja + ID parsial, dan ubah narasi portofolio"*

**Bentuk Implementasi:**
1. **Pilihan C.1:** Menurunkan klaim pengenalan STT menjadi "mostly Indonesian + English item names" dengan memperbanyak pemetaan alias fonetik menu di `packages/cart` (misal *"french fries"* dipetakan dari varian fonetik *"peren prais"*, *"fren fris"*), sehingga beban akurasi tidak dibebankan mutlak pada model STT.
2. **Pilihan C.2:** Jika integrasi multi-bahasa terbukti terlalu lambat, beralih ke antarmuka utama Bahasa Inggris penuh dengan pengenalan entitas menu Indonesia secara parsial, memanfaatkan model STT/TTS bahasa Inggris yang memiliki latensi inferensi jauh lebih cepat dan ketersediaan provider gratis yang lebih luas.

**Trade-offs Opsi C:**
- **Keuntungan:** Memperkecil tantangan teknis code-switching bahasa; memungkinkan penggunaan model STT bahasa Inggris berukuran kecil yang lebih cepat.
- **Kerugian / Risiko:** Mengurangi relevansi produk terhadap pasar lokal restoran cepat saji Indonesia (F&B lokal), serta menurunkan diferensiasi portofolio yang bertumpu pada tantangan *code-switching* bahasa lokal.

---

## Konsekuensi & Batasan
- Keputusan gerbang G1 dan pemilihan antara Opsi A, B, atau C sepenuhnya berada di tangan Daryl.
- Cabang `feat/minggu-2-spikes` tidak akan di-merge ke `main` dan pekerjaan Minggu 3 tidak akan dimulai sebelum ada arahan tertulis mengenai opsi mana yang dipilih.
