# Panduan Deployment Vercel & Pengujian Usability — Minggu 5

**Dokumen:** `docs/demos/week-05-deployment-guide.md`  
**Milestone:** Minggu 5 (Web Simulator Preview Deployment)  
**Terkait:** ADR-0009 (*Hosting Frontend & Worker*), ADR-0014 (*Web Protocol v1*)  
**Status Panduan:** **PANDUAN LANGKAH MANUAL UNTUK DARYL [HUMAN]**

---

## 1. Dua Mode Operasional yang Terpisah Jelas

Aplikasi web simulator dirancang dengan sakelar lingkungan `LIVE_MODE_ENABLED` (default `false` di seluruh lingkungan):

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

---

## 2. Tabel Konsolidasi Kuota Vendor & Batasan Teknis

> [!IMPORTANT]
> **Aturan Pengujian Wajib:** Seluruh sesi pengujian 3 orang awam **WAJIB DILAKUKAN SATU PER SATU (*STRICTLY TESTED ONE AT A TIME*)**. Pengujian simultan (2 atau 3 orang berbicara bersamaan) dipastikan memicu kegagalan HTTP 429 pada Groq LLM karena batas ketat *Tokens Per Minute (TPM)*.

| Vendor / Layanan | Model ID / Spesifikasi | Batas Free Tier Resmi | Konsumsi per Turn Terukur | Anggaran 3 Partisipan (1 per 1, @ 8 turn = 24 turn) | Status & Evaluasi Risiko |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ElevenLabs TTS** | `eleven_flash_v2_5` | **1.576 karakter tersisa** (dari limit 10.000, dicek via API *read-only*) | Salam pembuka 69 char, balasan kasir ~45 char (rentang 32–60 char) | 3 salam (207 char) + 24 turn (~1.080 char) = **~1.287 char** (rentang atas ~1.527 char) | **Tight Fit (Margin Sisa 49–289 char)**. Partisipan tidak boleh diajak mengobrol di luar skrip. Kuota habis jika turn > 24. |
| **Groq LLM (TPM)** | `qwen/qwen3.8-27b` | **8.000 tokens/minute (TPM)** ([console.groq.com/docs/rate-limits](https://console.groq.com/docs/rate-limits), Okt 2026) | ~1.604 token/turn (1.499 prompt + 105 completion) | 1 turn mengonsumsi 20% TPM. Maksimum kapasitas: **~4,98 turn/menit (~4 turn/min)** | **Bottleneck Kritis**. Jika 3 orang berbicara simultan, kebutuhan token mencapai >9.600 TPM (melebihi 8.000) &rarr; **HTTP 429**. |
| **Groq LLM (TPD)** | `qwen/qwen3.8-27b` | **200.000 tokens/day (TPD)** & 1.000 requests/day | ~1.604 token/turn | 24 turn = **~38.496 token** (19,2% kuota harian) | **Aman**. Kapasitas harian mencukupi hingga ~124 turn/hari. |
| **LiveKit Cloud** | SFU WebRTC Agent | **1.000 menit/bulan** | Hard cap 3 menit (180 detik) per sesi | 3 sesi $\times$ 3 menit = **9 menit total** | **Sangat Aman** (< 1% kuota bulanan terpakai). |

---

## 3. Persyaratan Secure Context Mikrofon (MDN)

Berdasarkan dokumentasi resmi MDN Web Docs ([MediaDevices.getUserMedia()](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia), verifikasi Oktober 2026):
- Metode `navigator.mediaDevices.getUserMedia()` adalah fitur berprivasi tinggi yang **HANYA TERSEDIA PADA SECURE CONTEXT (`isSecureContext === true`)**.
- Konteks yang diakui aman oleh peramban hanyalah:
  1. Protokol HTTPS (`https://`)
  2. Alamat lokal pengembang (`http://localhost` atau `http://127.0.0.1`)
- **Peringatan Kritis Akses Ponsel:** Alamat IP lokal seperti `http://192.168.x.x:3000` yang dibuka melalui peramban ponsel (Chrome Android atau Safari iOS) **DITOLAK SEBAGAI INSECURE CONTEXT**. Pada kondisi ini, properti `navigator.mediaDevices` bernilai `undefined`, tombol mic gagal berfungsi, dan izin mikrofon sama sekali tidak dapat diminta.
- Oleh karena itu, pengujian pada perangkat ponsel **WAJIB menggunakan URL berprotokol HTTPS**.

---

## 4. Status Vercel Deployment Protection & Shareable Links (Hobby Plan)

Berdasarkan dokumentasi resmi Vercel ([vercel.com/docs/security/deployment-protection](https://vercel.com/docs/security/deployment-protection), verifikasi Oktober 2026):
- **Password Protection (Sandi Masuk Standar):** **TIDAK TERSEDIA pada paket Hobby gratis**. Memerlukan add-on Pro berbayar ($20/bulan per proyek) atau Enterprise.
- **Vercel Authentication (SSO Login):** Tersedia gratis pada paket Hobby. Namun, pengunjung yang membuka tautan preview wajib login dengan akun Vercel dan meminta izin akses. Partisipan awam tanpa akun Vercel akan terblokir oleh layar login SSO Vercel dan tidak dapat membuka simulator.
- **Shareable Links pada Hobby Plan:**
  - *Ketersediaan:* **Tersedia pada paket Hobby gratis**, namun **dibatasi ketat maksimal 1 link aktif per akun** (pada Pro/Enterprise tidak terbatas).
  - *Pengalaman Partisipan:* Partisipan yang membuka Shareable Link (memuat parameter token bypass `?_vercel_share=...`) **dapat langsung mengakses aplikasi web simulator tanpa login akun Vercel**. Pengunjung akan melihat Vercel Toolbar kecil di bagian bawah layar.

---

## 5. Pilihan Solusi HTTPS untuk Pengujian Usability (Tanpa Memilih / Tanpa Mengimplementasikan)

Berikut adalah opsi-opsi yang memenuhi persyaratan HTTPS untuk mikrofon ponsel partisipan:

### Opsi 1: Deployed Vercel Preview dengan Shareable Link (Bypass Resmi)
- **Cara Kerja:** Biarkan *Vercel Authentication* tetap aktif di Settings. Masuk ke Vercel Dashboard &rarr; Deployments &rarr; pilih preview aktif branch `feat/minggu-5-web-simulator` &rarr; klik **Share** &rarr; aktifkan **Shareable Link**. Salin tautan ber-token bypass tersebut dan bagikan ke partisipan satu per satu. Set `LIVE_MODE_ENABLED=true` pada preview.
- **Syarat Akun / Biaya:** Akun Vercel Hobby gratis milik Daryl, tanpa kartu kredit ($0).
- **Paparan:** Terbatas pada pemegang tautan bertoken bypass (maksimal 1 link aktif).
- **Penutupan:** Hapus link share atau ubah `LIVE_MODE_ENABLED=false` setelah 3 sesi selesai.

### Opsi 2: Deployed Vercel Preview dengan Protection Disabled Sementara
- **Cara Kerja:** Di Vercel Dashboard &rarr; Settings &rarr; Deployment Protection, nonaktifkan *Vercel Authentication* (*Disabled*) sementara selama sesi uji coba. Bagikan URL preview unik `https://lajur-xxx-daryl.vercel.app/?mode=live` ke partisipan secara bergantian.
- **Syarat Akun / Biaya:** Gratis tanpa kartu kredit ($0).
- **Paparan:** Siapa saja di internet publik yang memegang URL dapat membuka halaman.
- **Mitigasi:** Worker hanya menyala di laptop Daryl; dilindungi hard cap token 5 menit dan batas sesi 180s. Setelah 3 sesi selesai, aktifkan kembali *Vercel Authentication* dan set `LIVE_MODE_ENABLED=false`.

### Opsi 3: HTTPS Tunnel dari Laptop (Cloudflare Quick Tunnel / TryCloudflare)
- **Cara Kerja:** Menjalankan web lokal di laptop (`npm run dev --prefix apps/web`) lalu mengeksposnya ke HTTPS via perintah resmi:
  `cloudflared tunnel --url http://localhost:3000`
- **Syarat Akun / Biaya:** **100% Tanpa Akun dan Tanpa Kartu Kredit**. Cloudflare Quick Tunnel menghasilkan URL acak `https://<random>.trycloudflare.com` secara instan.
- **Ketentuan Layanan:** Ditujukan untuk pengujian dan evaluasi lokal sementara.
- **Paparan:** URL HTTPS acak di internet publik selama proses tunnel berjalan. Matikan terminal `cloudflared` begitu pengujian selesai.

### Opsi 4: Alternatif HTTPS Tunnel Lainnya (Localtunnel / Pinggy)
- **Localtunnel:** `npx localtunnel --port 3000` (Gratis, tanpa akun, tanpa kartu kredit; namun menampilkan halaman konfirmasi IP pengembang pada kunjungan pertama di ponsel).
- **Pinggy.io:** `ssh -p 443 -R0:localhost:3000 a.pinggy.io` (Gratis, tanpa akun, tanpa kartu kredit; dibatasi durasi koneksi maksimal 60 menit per sesi).
- **Ngrok:** Memerlukan pendaftaran akun dan konfigurasi *auth token* personal (meskipun tier gratis tidak membutuhkan kartu kredit).
