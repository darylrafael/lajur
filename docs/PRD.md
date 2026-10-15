# Product Requirements Document (PRD) — Lajur

**Status:** Draft v1.0 · **Target Rilis:** Minggu 10 · **Penulis:** Daryl (Solo Dev)

---

## 1. Ringkasan Produk & Visi
Lajur adalah demo web publik *voice ordering* ala *drive-thru* yang mampu menangani pesanan lisan dalam **Bahasa Indonesia campur Inggris (*code-switching*)** di bawah kondisi derau akustik (motor/helm), dengan mempublikasikan metrik latensi dan akurasi (*Order Accuracy Rate*) secara transparan.

- **Masalah Utama:** Solusi Voice AI global dilatih untuk bahasa Inggris standar di kabin mobil tertutup yang tenang. Di Indonesia, pesanan lisan didominasi percampuran bahasa (*"paket hemat burger di-upsize ya, minumnya iced tea no sugar"*) dan sering diucapkan pengendara motor berhelm. Solusi yang ada tidak transparan mempublikasikan tingkat kegagalan.
- **Solusi:** Pipeline suara streaming cascade (STT &rarr; LLM &rarr; TTS), validasi pesanan berbasis *state machine* deterministik, penanganan interupsi (*barge-in*), *fallback* simulasi kru manusia, dan laporan evaluasi otomatis.

---

## 2. Target Pengguna & Persona
1. **P1 — Technical Reviewer / Recruiter / Senior Engineer (Primer):**
   - *Kebutuhan:* Menguji demo interaktif tanpa registrasi dalam waktu < 5 menit, melihat angka evaluasi nyata, serta meninjau keputusan arsitektur (ADR) dan trade-off rekayasa.
2. **P2 — Pemilik / Manajer F&B Indonesia (Sekunder / Eksplorasi Startup):**
   - *Kebutuhan:* Memahami bagaimana asisten suara dapat menangani jam sibuk tanpa salah order dan menawarkan upsell secara konsisten.
3. **P3 — Pengguna Awam:**
   - *Kebutuhan:* Memesan makanan via suara dari browser HP/laptop tanpa perlu membaca petunjuk teknis.

---

## 3. Scope & Non-Goals

### 3.1 In-Scope (v1)
- Pemesanan suara real-time WebRTC dua arah langsung dari browser (desktop & mobile).
- Simulasi menu generik (45–60 item) mencakup burger, ayam, minuman, sarapan, dan paket hemat bersarang.
- Penanganan koreksi/undo (*"tidak jadi kentangnya, ganti nasi"*), modifikasi item, dan deteksi stok habis (*86'd*).
- Barge-in (pelanggan memotong ucapan bot kasir).
- Pilihan simulasi preset derau audio: bersih, motor idle, hujan+knalpot, filter helm.
- Dashboard metrik publik (latensi turn, OAR test suite, total sesi).

### 3.2 Non-Goals (Tegas, §4.2)
- **Tidak ada hardware fisik**: Tidak membuat intercom, mikrofon khusus, atau edge box.
- **Tidak ada POS nyata / pembayaran nyata**: Tidak terintegrasi ke payment gateway atau sistem POS restoran sungguhan.
- **Tidak melatih / fine-tune model**: Menggunakan model foundation pihak ketiga melalui adapter.
- **Tidak ada integrasi telepon (SIP) atau WhatsApp** pada v1.
- **Tidak ada sistem akun pengguna / multi-tenant**.
- **Tidak menyimpan rekaman suara (audio biometrik)**.

---

## 4. Kebutuhan Fungsional & Non-Fungsional Inti

### Kebutuhan Fungsional
- **FR-01 (Voice Session):** Sesi WebRTC interaktif dua arah (mic &rarr; STT &rarr; LLM &rarr; TTS &rarr; audio balik).
- **FR-02 & FR-05 (Live Board):** Papan menu interaktif dan layar konfirmasi live yang sinkron dengan dialog bot.
- **FR-03 & FR-04 (Cart Mutation):** Tambah/hapus/ubah kuantitas, varian ukuran, dan slot combo bersarang.
- **FR-06 (Correction & Undo):** Membatalkan item terakhir tanpa memicu penambahan item baru yang keliru.
- **FR-07 (Availability):** Validasi jam sarapan vs reguler dan penolakan item stok habis (*86'd*).
- **FR-08 (Barge-in):** Penghentian TTS otomatis seketika saat pelanggan mulai berbicara.
- **FR-09 (Human Handoff):** Pengalihan otomatis ke simulasi kasir manusia jika confidence rendah / gagal berulang.
- **FR-10 (Upsell):** Tawaran upsell kontekstual maksimal satu kali per sesi order.
- **FR-11 (Noise Presets):** Injeksi derau audio sisi klien (bersih, motor idle, knalpot+hujan, helm).

### Kebutuhan Non-Fungsional & Guardrails
- **NFR-01 (SLO Latensi):** Latensi turn (selesai bicara &rarr; audio pertama) P50 < 800ms, P95 < 1.300ms.
- **NFR-02 (Privasi Suara):** Audio sama sekali tidak disimpan. Transkrip teks dan event log dianomalisasi (retensi maks 30 hari).
- **NFR-03 (Anti-Abuse):** Batas sesi 3 menit, kuota harian global (~10 sesi/hari di cloud free tier), Cloudflare Turnstile captcha, dan batas 20 item per order.
- **NFR-04 (Batas Biaya):** Biaya variabel < $0,05 per sesi; total pengeluaran vendor < $30/bulan dengan hard cap ketat.

---

## 5. Gerbang Keputusan Kritis (Kill / Pivot Criteria)
- **G1 (Minggu 2):** Benchmark STT ID-EN. Harus ada vendor dengan Keyterm Error Rate (KER) &le; 15% dan latensi turn &le; 1,2s.
- **G2 (Minggu 7):** Eval Harness. Order Accuracy Rate (OAR) &ge; 75% pada skenario inti audio bersih.
- **G3 (Minggu 10):** Jalur Startup. Minimal 2 pemilik F&B siap pilot dan menyatakan kesediaan bayar. Jika gagal, proyek tetap sebagai portofolio engineering.
