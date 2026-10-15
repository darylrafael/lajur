# ADR-0009: Opsi Hosting Frontend dan Agent Worker

## Status
Proposed, waiting for user selection [HUMAN]

## Konteks
Sistem Lajur membutuhkan dua lingkungan hosting terpisah:
1. **Frontend Simulator (`apps/web`)**: Aplikasi web Next.js dengan Server Route (`/api/token`) untuk menerbitkan token WebRTC LiveKit berumur pendek.
2. **Agent Worker (`services/agent`)**: Proses kontainer Python berumur panjang (*long-running WebSocket worker*) yang mempertahankan koneksi real-time ke LiveKit Cloud/Server.

Target latensi sistem adalah P50 < 800ms dan P95 < 1.300ms dari koneksi internet publik Indonesia. Karena itu, lokasi region server (khususnya kedekatan dengan Indonesia, yaitu Region Singapura / `sin`) sangat krusial.

---

## 1. Opsi Hosting Frontend Simulator (`apps/web`)

### Opsi A (Rekomendasi Utama): Vercel Preview
- **Karakteristik:** Zero-config untuk Next.js App Router; server route `/api/token` berjalan native di Node.js Serverless Function.
- **Biaya:** $0 (Hobby Plan).
- **Batasan & Trade-off:**
  - Vercel Hobby melarang penggunaan komersial. Untuk fase portofolio non-komersial saat ini (Minggu 1–9) sepenuhnya legal dan aman.
  - Jika di Gerbang G3 diputuskan berlanjut ke entitas startup komersial, frontend wajib dipindahkan ke Cloudflare Pages atau Vercel Pro ($20/bulan).

### Opsi B: Cloudflare Pages + OpenNext
- **Karakteristik:** Gratis untuk komersial, unlimited requests.
- **Batasan & Trade-off:**
  - Memerlukan adapter `@cloudflare/next-on-pages` dan flag `nodejs_compat` karena `livekit-server-sdk` memerlukan modul kriptografi Node.js. Konfigurasi build lebih kompleks dibandingkan Vercel.

---

## 2. Opsi Hosting Agent Worker (`services/agent`)

Agent worker adalah aplikasi berbasis kontainer Python (`Dockerfile`) yang harus berjalan kontinu (*background daemon*), bukan serverless function.

| Parameter | Opsi 1: Fly.io (Region Singapura `sin`) | Opsi 2: Railway (Region Singapura) | Opsi 3: VPS Singapura (Hetzner / DO) |
|---|---|---|---|
| **Lokasi Region** | **Singapura (`sin`)** — ~25–35ms ping dari Jakarta | **Singapura (`asia-southeast1`)** | **Singapura** |
| **Estimasi Biaya** | **~$2,50 – $3,50 / bulan** (`shared-cpu-1x`, 512MB RAM) | **~$3,00 – $5,00 / bulan** ($5 base Hobby plan, ditagih per vCPU/RAM detik) | **~$4,50 – $6,00 / bulan** (Fixed flat rate) |
| **Metode Deploy** | `fly launch` / `fly deploy` berbasis Dockerfile | Git push webhook otomatis berbasis Dockerfile | SSH manual / Docker Compose di VPS Linux |
| **Kelebihan** | Latensi terendah ke Indonesia; routing WebRTC/UDP sangat baik | Dashboard UI sangat intuitif; manajemen env var mudah | Biaya flat tetap; bisa sekaligus menjalankan self-hosted LiveKit Server jika kuota cloud habis |
| **Kelemahan** | CLI first; perlu kartu kredit untuk verifikasi | Kuota sleep jika free tier habis | Perlu perawatan OS Linux mandiri (security update) |

---

## Keputusan Sementara (Sebelum Dipilih [HUMAN])
1. **Frontend:** Menggunakan Vercel untuk deployment preview URL yang cepat dan andal pada fase portofolio.
2. **Worker:** Selama menunggu keputusan [HUMAN], agent worker dijalankan langsung dari **laptop pengembang lokal (Windows/Docker)** yang terhubung via WebSocket ke LiveKit Cloud. Konfigurasi ini didokumentasikan sebagai sementara (*temporary*).

## Konsekuensi
- Pengembang lokal tidak mengeluarkan biaya hosting worker di awal sebelum arsitektur diuji pada perangkat nyata.
- Evaluasi perangkat nyata (iPhone seluler) dapat langsung menguji WebRTC secara nyata karena LiveKit Cloud bertindak sebagai SFU relay publik.
