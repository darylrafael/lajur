# ADR-0009: Opsi Hosting Frontend dan Agent Worker

## Status
Accepted [HUMAN DECISION: 2026-10-18]
- **Frontend (`apps/web`):** Vercel
- **Worker (`services/agent`):** Proses lokal/kontainer terhubung ke LiveKit Cloud (transisi ke VPS Singapura/Fly.io/Railway pada Minggu 4/9)

## Konteks
Sistem Lajur membutuhkan dua lingkungan hosting terpisah:
1. **Frontend Simulator (`apps/web`)**: Aplikasi web Next.js dengan Server Route (`/api/token`) untuk menerbitkan token WebRTC LiveKit berumur pendek.
2. **Agent Worker (`services/agent`)**: Proses kontainer Python berumur panjang (*long-running WebSocket worker*) yang mempertahankan koneksi real-time ke LiveKit Cloud/Server.

Target latensi sistem adalah P50 < 800ms dan P95 < 1.300ms dari koneksi internet publik Indonesia. Karena itu, lokasi region server (khususnya kedekatan dengan Indonesia, yaitu Region Singapura / `sin`) sangat krusial.

---

## 1. Analisis Ketentuan Vercel Hobby & Penggunaan Komersial

### Kutipan Resmi Verbatim (Vercel Fair Use Guidelines)
- **URL Sumber:** [https://vercel.com/docs/limits/fair-use-guidelines](https://vercel.com/docs/limits/fair-use-guidelines)
- **Terakhir Diperbarui:** 2026-09-14 (Diverifikasi langsung: 2026-10-18)
- **Definisi Penggunaan Komersial (Verbatim):**
  > *"Hobby teams are restricted to non-commercial personal use only. All commercial usage of the platform requires either a Pro or Enterprise plan.*
  > 
  > *Commercial usage is defined as any Deployment that is used for the purpose of financial gain of anyone involved in any part of the production of the project, including a paid employee or consultant writing the code. Examples of this include, but are not limited to, the following:*
  > 
  > *- Any method of requesting or processing payment from visitors of the site*
  > *- Advertising the sale of a product or service*
  > *- Receiving payment to create, update, or host the site*
  > *- Affiliate linking is the primary purpose of the site*
  > *- The inclusion of advertisements, including but not limited to online advertising platforms like Google AdSense*
  > 
  > *💡 Note: Asking for Donations does not fall under commercial usage.*
  > 
  > *If you are unsure whether or not your site would be defined as commercial usage, please contact the Vercel Support team."*

### Penilaian Status Hukum untuk Lajur: Ambigu
Status kepatuhan Lajur pada tier Vercel Hobby bersifat **ambigu**:
- Di satu sisi, aplikasi saat ini tidak menerima pembayaran, tidak menayangkan iklan, dirilis dengan kode sumber terbuka (Apache-2.0 / CDLA), dan ditujukan sebagai portofolio teknis rekayasa sistem suara drive-thru.
- Di sisi lain, proyek ini secara eksplisit mencakup hipotesis validasi startup (`docs/PROJECT_PLAN.md` §16), mencakup rencana wawancara pelanggan *The Mom Test* (Minggu 6), dan memiliki gerbang komersialisasi G3 (Minggu 10) untuk menguji kesediaan bayar restoran.
- Karena klausul Vercel menyebutkan *"used for the purpose of financial gain of anyone involved in any part of the production of the project"*, batas antara portofolio eksploratif dan fase pra-pendapatan startup adalah area abu-abu. Sesuai panduan resmi Vercel, kondisi ambigu ini mengharuskan konfirmasi dengan tim Support Vercel sebelum peluncuran publik skala penuh.

---

## 2. Keputusan yang Diambil

1. **Frontend Simulator (`apps/web`):**
   - Menggunakan **Vercel** untuk preview deployment dan pengujian antarmuka selama fase pengembangan awal (Minggu 1 s.d. Minggu 8).
   - Rute `/api/token` berjalan sebagai **Node.js Serverless Function** bawaan Vercel (bukan Edge Runtime), menjamin kompatibilitas penuh dengan modul `crypto` Node.js dan `livekit-server-sdk`.
   - **Dated Checkpoint (Wajib):** Sebelum peluncuran publik Minggu 9 (T-7 Hari, 2026-12), pengembang wajib mere-evaluasi paket hosting frontend:
     - Mengontak Vercel Support untuk klarifikasi/dispensasi status proyek riset/portofolio, atau
     - Upgrade ke akun berbayar Vercel Pro ($20/bulan), atau
     - Memigrasikan frontend ke Cloudflare Workers/Pages atau server container mandiri.

2. **Agent Worker (`services/agent`):**
   - Pada Minggu 1 (Walking Skeleton), agent worker dijalankan langsung dari **mesin lokal pengembang (Windows/Docker)** yang terhubung via WebSocket ke LiveKit Cloud.
   - LiveKit Cloud bertindak sebagai WebRTC Selective Forwarding Unit (SFU) global publik, sehingga pengujian audio WebRTC melalui smartphone seluler tetap berjalan end-to-end tanpa memerlukan IP publik di laptop pengembang.
   - Rencana migrasi worker ke lingkungan server kontinu (Fly.io Region Singapura `sin` atau Railway) dijadwalkan pada milestone pipeline suara mandiri (Minggu 4).

---

## 3. Spesifikasi Teknis Deployment Vercel (`apps/web`)

| Parameter | Pengaturan di Vercel Dashboard |
|---|---|
| **Root Directory** | `apps/web` |
| **Framework Preset** | `Next.js` |
| **Build Command** | `next build` (default) |
| **Output Directory** | `.next` (default) |
| **Node.js Version** | `20.x` |
| **Environment Variables (Wajib)** | `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` |
| **Deployment Protection (PENTING)** | **Disabled** / **Public** pada Preview Deployments (agar browser HP seluler dapat mengakses tanpa login Vercel) |

---

## 4. Konsekuensi

### Positif
- **Zero Build Friction:** Next.js 14 App Router berjalan native tanpa perlu adapter OpenNext tambahan di fase awal.
- **Rute Token Andal:** Modul kriptografi Node.js pada `livekit-server-sdk` berjalan stabil di Node.js runtime.
- **Preview Cepat:** Setiap push git menghasilkan URL preview terisolasi yang dapat langsung diuji dari browser ponsel fisik.

### Negatif & Risiko
- Terdapat keharusan audit kepatuhan dan kemungkinan biaya ($20/bulan) atau kerja migrasi tambahan pada checkpoint Minggu 9 sebelum rilis publik.
