# Panduan Deployment Vercel & Pengujian Usability — Minggu 5

**Dokumen:** `docs/demos/week-05-deployment-guide.md`  
**Milestone:** Minggu 5 (Web Simulator Preview Deployment)  
**Terkait:** ADR-0009 (*Hosting Frontend & Worker*), ADR-0014 (*Web Protocol v1*)  
**Status Panduan:** **PANDUAN LANGKAH MANUAL UNTUK DARYL [HUMAN]**

---

## 1. Dua Mode Operasional yang Terpisah Jelas

Aplikasi web simulator dirancang dengan sakelar lingkungan `LIVE_MODE_ENABLED` (default `false` di semua lingkungan):

### Mode A: Public Showcase (Rekomendasi Utama — 100% Aman)
- **Konfigurasi:** `LIVE_MODE_ENABLED=false` (Default pada file `.env.example` dan `apps/web/.env.example`).
- **Perilaku:**
  - Rute `/api/token` mengembalikan HTTP `403 Forbidden` (`{"error": "Live mode is disabled."}`).
  - Antarmuka web menampilkan banner pemberitahuan *"Live voice is off; try the demo replay"* dan tombol mulai live dinonaktifkan.
  - Mode Demo Replay (`?mode=replay`) berjalan penuh di peramban dengan skenario rekaman baku.
- **Tingkat Risiko & Biaya:** **$0.00 (Nol Risiko).** Tidak ada kuota vendor yang tersentuh, tidak memerlukan worker yang menyala di laptop, dan aman dibagikan ke publik atau portfolio reviewer kapan saja.

### Mode B: Usability-Test Window (Jendela Uji Keterbatasan)
- **Konfigurasi:** `LIVE_MODE_ENABLED=true` diatur **hanya selama durasi sesi uji berlangsung**.
  - **PowerShell:** `$env:LIVE_MODE_ENABLED="true"; npm run dev --prefix apps/web`
  - **Bash:** `LIVE_MODE_ENABLED=true npm run dev --prefix apps/web`
- **Prasyarat Operasional:** Laptop Daryl harus menyala dan menjalankan agent worker secara lokal:
  `uv run python -m lajur_agent.worker dev`  
  *(atau: `uv run python services/agent/src/lajur_agent/worker.py dev`)*
- **Paparan Risiko Selama Jendela Aktif:** Siapapun yang memiliki akses URL preview dapat memulai sesi suara WebRTC langsung yang mengonsumsi kuota gratis vendor:
  - **ElevenLabs Free Tier:** Sisa kuota terukur **1.576 karakter** (dari batas 10.000, dicek via query API *read-only*).
    - Konsumsi teks templat: salam pembuka 69 karakter, rata-rata balasan kasir ~45 karakter (rentang 32–60 karakter).
    - Anggaran 3 partisipan @ 8 turn: 3 salam pembuka (207 char) + 24 turn (~1.080 char) = ~1.287 karakter (batas atas ~1.527 karakter).
    - Evaluasi kapasitas: Kuota 1.576 karakter **mencukupi secara ketat** (*tight fit*, sisa margin 49–289 karakter). Jika partisipan banyak mengulang ucapan atau memicu pesan bantuan panjang, kuota dapat habis sebelum turn ke-24.
    - Catatan kode: Saat ini belum ada mode balasan teks-saja (*text-only reply mode*) di dalam worker; jika kuota TTS habis, worker memunculkan error TTS. Diusulkan penambahan `TTS_MODE="none"` atau `NoOpTTSAdapter` pada iterasi mendatang bila diperlukan.
  - **Groq Free Tier (Qwen-2.5-32b / Qwen3.8-27b):**
    - Batas resmi dokumentasi Groq ([console.groq.com/docs/rate-limits](https://console.groq.com/docs/rate-limits), verifikasi Oktober 2026): **200.000 tokens/day (TPD)**, 1.000 requests/day (RPD), 8.000 tokens/minute (TPM), 30 requests/minute (RPM).
    - Konsumsi aktual terukur dari audit: rata-rata **~1.499 prompt tokens + ~105 completion tokens (~1.604 token total per turn)**. *(Klaim lama "~170 tokens/turn" telah ditarik dan dikoreksi)*.
    - Kapasitas harian: $200.000 / 1.604 \approx 124$ turn/hari. Anggaran 24 turn untuk 3 partisipan mengonsumsi ~38.496 token (~19% dari kuota harian), sangat aman.
  - **LiveKit Cloud Build Tier:** Batas 1.000 menit agent/bulan. Setiap sesi dibatasi *hard cap* 3 menit (180 detik) dan 12 turn.
- **Prosedur Penutupan:** Segera setelah 3 sesi uji selesai, matikan worker lokal (`Ctrl+C`), ubah kembali `LIVE_MODE_ENABLED=false` di Vercel Dashboard, dan picu *Redeploy* untuk menutup akses API token.

---

## 2. Status Vercel Deployment Protection pada Paket Hobby

Berdasarkan dokumentasi resmi Vercel ([vercel.com/docs/security/deployment-protection](https://vercel.com/docs/security/deployment-protection), verifikasi Oktober 2026):
- **Password Protection (Kata Sandi Standar):** **TIDAK TERSEDIA pada paket Hobby gratis**. Fitur ini memerlukan paket berbayar Pro ($20/bulan per proyek) atau Enterprise. Oleh karena itu, opsi Password Protection ditiadakan dari panduan ini.
- **Vercel Authentication (SSO Login):** Tersedia gratis pada paket Hobby. Namun, fitur ini mewajibkan setiap pengunjung untuk login menggunakan akun Vercel dan meminta akses (*Request Access*) ke pemilik proyek.
- **Pengalaman Partisipan Tanpa Akun Vercel:** Jika Vercel Authentication aktif, partisipan yang membuka tautan preview di ponsel akan melihat layar login Vercel (*"Log in to Vercel"*). Partisipan yang bukan developer dan tidak memiliki akun Vercel **SAMA SEKALI TIDAK BISA MEMBUKA APLIKASI**.

---

## 3. Opsi Pelaksanaan Jendela Uji Usability (Deskripsi Objektif)

Untuk memfasilitasi 3 partisipan non-teknis tanpa kartu kredit dan tanpa biaya tambahan, berikut opsi yang dapat dipilih Daryl:

### Opsi A: Deployment Protection Dinonaktifkan Sementara (Jendela Sesi Uji)
- **Cara Kerja:**
  1. Masuk ke Vercel Dashboard &rarr; Proyek `lajur` &rarr; Settings &rarr; Deployment Protection.
  2. Ubah *Vercel Authentication* menjadi **Disabled** hanya selama durasi 3 sesi pengujian.
  3. Set Environment Variable pada Preview: `LIVE_MODE_ENABLED=true`.
  4. Bagikan URL deployment unik (misal: `https://lajur-xxx-daryl.vercel.app/?mode=live`) secara privat hanya kepada 3 partisipan via chat WhatsApp.
  5. Daryl menyalakan worker di laptop (`uv run python -m lajur_agent.worker dev`).
  6. Setelah 3 sesi selesai, set `LIVE_MODE_ENABLED=false`, redeploy, dan aktifkan kembali *Vercel Authentication*.
- **Tingkat Paparan & Kuota:**
  URL preview dapat diakses siapa saja di internet publik selama jendela waktu tersebut. Namun, risiko dibatasi oleh:
  - Worker hanya aktif saat laptop Daryl terhubung ke LiveKit Cloud.
  - Token API LiveKit dibatasi TTL 5 menit dan room suffix acak 16-heksadesimal tak tertebak.
  - Hard cap sesi 3 menit dan 12 turn per koneksi.
  - ElevenLabs memiliki sisa 1.576 karakter dan Groq 200.000 token/hari.

### Opsi B: Menggunakan Shareable Link Bypass (Jika Tersedia di Preview)
- **Cara Kerja:**
  1. Biarkan *Vercel Authentication* tetap aktif (*Enabled*).
  2. Di tab *Deployments*, pilih deployment preview aktif dari branch `feat/minggu-5-web-simulator`.
  3. Klik menu **Share** &rarr; aktifkan **Shareable Link** (menghasilkan tautan dengan token bypass parameter URL).
  4. Bagikan *Shareable Link* tersebut kepada 3 partisipan.
- **Tingkat Paparan:**
  Hanya pihak yang memegang tautan bertoken bypass yang dapat mengakses preview tanpa login Vercel.

### Opsi C: Pengujian Menggunakan Jaringan Wi-Fi Lokal (Nol Paparan Internet Publik)
- **Cara Kerja:**
  1. Jika pengujian dilakukan bersama teman/keluarga yang berada di lokasi fisik yang sama (satu jaringan Wi-Fi rumah/kantor):
  2. Jalankan aplikasi web lokal: `$env:LIVE_MODE_ENABLED="true"; npm run dev --prefix apps/web -- -H 0.0.0.0`
  3. Jalankan worker: `uv run python -m lajur_agent.worker dev`
  4. Minta partisipan membuka browser ponsel di alamat IP lokal laptop Daryl (misal: `http://192.168.1.xxx:3000/?mode=live`).
- **Tingkat Paparan & Risiko:**
  **0% Paparan ke Internet Publik.** Tidak ada URL publik yang terekspos ke crawler, tidak memerlukan Vercel deployment, dan 100% aman dari pihak luar.
