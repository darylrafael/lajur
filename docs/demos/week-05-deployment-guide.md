# Panduan Deployment Vercel — Minggu 5

**Dokumen:** `docs/demos/week-05-deployment-guide.md`  
**Milestone:** Minggu 5 (Web Simulator Preview Deployment)  
**Terkait:** ADR-0009 (*Hosting Frontend & Worker*), ADR-0014 (*Web Protocol v1*)  
**Status Panduan:** **PANDUAN LANGKAH MANUAL UNTUK DARYL [HUMAN]**

---

## 1. Dua Mode Operasional yang Terpisah Jelas

Aplikasi web simulator dirancang dengan sakelar lingkungan `LIVE_MODE_ENABLED` (default `false` di semua lingkungan):

### Mode A: Public Showcase (Rekomendasi Utama — 100% Aman)
- **Konfigurasi:** `LIVE_MODE_ENABLED=false` (Default).
- **Perilaku:**
  - Rute `/api/token` mengembalikan HTTP `403 Forbidden` jika diakses.
  - Antarmuka web menampilkan banner pemberitahuan *"Live voice is off; try the demo replay"* dan tombol mulai live dinonaktifkan.
  - Mode Demo Replay (`?mode=replay`) berjalan penuh di peramban dengan 5 skenario baku.
- **Tingkat Risiko & Biaya:** **$0.00 (Nol Risiko).** Tidak ada kuota vendor yang tersentuh, tidak memerlukan laptop worker yang menyala, dan aman dibagikan ke publik atau portfolio reviewer kapan saja.

### Mode B: Usability-Test Window (Jendela Uji Keterbatasan)
- **Konfigurasi:** `LIVE_MODE_ENABLED=true` diatur **hanya selama sesi uji berlangsung**.
- **Prasyarat Operasional:** Laptop Daryl harus menyala dan menjalankan agent worker secara lokal (`uv run python -m lajur_agent.worker dev`).
- **Paparan Risiko Selama Jendela Aktif:** Siapapun yang memiliki URL preview dapat memulai sesi suara WebRTC langsung yang mengonsumsi kuota gratis vendor pihak ketiga:
  - **ElevenLabs Free Tier:** Sisa kuota terukur **1.576 karakter** (dari batas 10.000). Setiap giliran balasan templat kasir mengonsumsi ~18 karakter. Cadangan aman untuk ~80 giliran percakapan.
  - **LiveKit Cloud Build Tier:** Batas 1.000 menit agent/bulan. Setiap sesi dibatasi hard cap 3 menit (180 detik).
  - **Groq Free Tier (Qwen-2.5-32b):** Batas 14.400 permintaan/hari dan 6.000 token/menit. Konsumsi aktual terukur dari audit: ~120–150 token input dan ~30–50 token output per giliran (~170 token total/turn).
- **Prosedur Penutupan:** Segera setelah 3 sesi uji selesai, ubah kembali `LIVE_MODE_ENABLED=false` di Vercel Dashboard dan *Redeploy* untuk menutup akses API token.

---

## 2. Pengaturan Vercel Deployment Protection & Akses Ponsel

Secara default, Vercel mengaktifkan *Deployment Protection* (Vercel Authentication) pada Preview Deployments. **Pengaturan ini sebaiknya TETAP AKTIF (*stay ON*)** guna mencegah publik mengakses preview build secara liar.

Jika Deployment Protection aktif, partisipan yang membuka link di ponsel mereka akan dihalangi oleh layar login Vercel SSO. Berikut panduan singkat (maksimal 10 baris) untuk Daryl:

1. Buka dashboard Vercel &rarr; Proyek `lajur` &rarr; tab *Deployments*.
2. Pilih deployment preview aktif dari branch `feat/minggu-5-web-simulator`.
3. Klik tombol **Share** di pojok kanan atas, lalu aktifkan **Shareable Link** (membuat tautan khusus bertoken bypass proteksi).
4. Bagikan *Shareable Link* tersebut kepada partisipan agar mereka dapat membuka simulator di ponsel tanpa login Vercel.
5. Atau (opsional): buka *Project Settings* &rarr; *Deployment Protection*, ubah *Vercel Authentication* menjadi *Disabled* HANYA selama durasi 3 sesi uji usability.
6. Masukkan Environment Variables di Vercel: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `NEXT_PUBLIC_LIVEKIT_URL`, dan `LIVE_MODE_ENABLED` (`false` untuk Mode A, `true` sementara untuk Mode B).
7. Simpan pengaturan dan picu *Redeploy*.
8. Jika tadi menonaktifkan Deployment Protection, segera kembalikan ke *Enabled* setelah sesi uji selesai.
