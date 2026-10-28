# Panduan Deployment Vercel Preview — Minggu 5

**Dokumen:** `docs/demos/week-05-deployment-guide.md`  
**Milestone:** Minggu 5 (Web Simulator Preview Deployment)  
**Terkait:** ADR-0009 (*Opsi Hosting Frontend dan Agent Worker*), ADR-0014 (*Web Protocol v1*)  
**Status Tindakan:** **PANDUAN LANGKAH MANUAL UNTUK DARYL [HUMAN]**

---

## 1. Konteks Keamanan & Pembagian Status Lingkungan

Sesuai ADR-0009 dan batasan rilis Minggu 5:

| Aspek / Rute | Status Perlindungan di Minggu 5 | Rekomendasi Operasional |
| :--- | :--- | :--- |
| **Replay Mode (`?mode=replay`)** | **100% Bebas Risiko & Terisolasi** | **Mode default yang direkomendasikan untuk uji publik/portofolio.** Berjalan sepenuhnya di sisi klien tanpa memanggil rute token LiveKit maupun kuota vendor berbayar. |
| **Live Token API (`/api/token`)** | **Terbuka (Belum ada Captcha / Rate Limit)** | Pengerasan keamanan (*Cloudflare Turnstile*, *IP rate-limiting*, *anti-bot*) baru dijadwalkan pada **Minggu 9**. Jangan membagikan URL live ke forum publik terbuka tanpa pengawasan. |
| **LiveKit Agent Worker** | **Berjalan di Laptop Pengembang** | Worker Python (`services/agent/src/lajur_agent/worker.py`) berjalan secara lokal di laptop Daryl dan terhubung via WebSocket ke LiveKit Cloud. Jika laptop mati atau worker tidak aktif, browser klien akan menampilkan banner *Agent Offline*. |
| **Vercel Deployment Protection** | **Wajib Dinonaktifkan (Public)** | Jika Deployment Protection aktif, browser ponsel (Safari/Chrome) akan dihalangi layar autentikasi Vercel SSO, sehingga pengujian perangkat nyata gagal. |

---

## 2. Langkah-Langkah di Vercel Dashboard (Daryl [HUMAN])

Ikuti langkah-langkah ringkas berikut pada antarmuka dashboard Vercel:

1. **Buka Proyek di Vercel:**
   - Masuk ke dashboard [vercel.com](https://vercel.com) menggunakan akun GitHub Anda.
   - Pilih proyek `lajur` (atau impor repositori `darylrafael/lajur` jika belum terhubung).

2. **Atur Konfigurasi Direktori & Framework:**
   - **Root Directory:** `apps/web` (Pastikan bukan root repositori).
   - **Framework Preset:** `Next.js`.
   - **Build Command:** `npm run build` (atau biarkan default).
   - **Output Directory:** `.next` (default).
   - **Node.js Version:** `20.x`.

3. **Masukkan Environment Variables (Khusus Live Mode):**
   Pada menu *Settings* &rarr; *Environment Variables*, tambahkan 4 kunci berikut untuk target *Preview* dan *Production*:
   - `LIVEKIT_URL` = `wss://<your-project>.livekit.cloud`
   - `LIVEKIT_API_KEY` = `<your-livekit-api-key>`
   - `LIVEKIT_API_SECRET` = `<your-livekit-api-secret>`
   - `NEXT_PUBLIC_LIVEKIT_URL` = `wss://<your-project>.livekit.cloud`

4. **Nonaktifkan Deployment Protection (PENTING untuk Akses Mobile):**
   - Buka menu *Settings* &rarr; *Deployment Protection*.
   - Pada bagian *Vercel Authentication*, pastikan statusnya **Disabled** (atau tambahkan bypass rule untuk preview link).
   - *Alasan:* Memungkinkan partisipan uji ketergunaan membuka URL preview langsung dari peramban ponsel mereka tanpa perlu login akun Vercel.

5. **Deploy & Salin URL:**
   - Setelah branch `feat/minggu-5-web-simulator` di-push, Vercel akan otomatis membangun preview build.
   - Salin URL preview yang dihasilkan (misal: `https://lajur-web-git-feat-minggu-5-web-simulator-....vercel.app`).

---

## 3. Verifikasi Checklist Setelah Deployment

Lakukan pengecekan cepat menggunakan ponsel fisik Anda:
- [ ] Buka URL dengan parameter `?mode=replay`: Halaman simulator termuat, menu board terlihat, dan skenario replay dapat diputar tanpa error console.
- [ ] Buka URL dalam mode Live: Tekan tombol *"Mulai Pesan"*, periksa apakah pop-up izin mikrofon muncul di peramban seluler.
- [ ] Jalankan worker di laptop (`uv run python -m lajur_agent.worker dev`): Pastikan status pada antarmuka web berubah menjadi *"Terhubung"* atau *"Kasir Siap"*.
