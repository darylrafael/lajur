# Naskah Demo Minggu 1 — Walking Skeleton & Menu/Cart Dasar

**Durasi:** ~2 Menit (120 Detik)  
**Tujuan Demo:** Memperlihatkan bukti kerja integrasi WebRTC dua arah (Walking Skeleton) tanpa vendor berbayar, dan integritas logika kalkulasi keranjang belanja (`packages/cart`) yang 100% deterministik.  
**Target Penonton:** Reviewer teknis, hiring manager, dan dokumentasi mingguan portofolio.

---

## Persiapan Sebelum Rekaman (Checklist)

1. [ ] Buka dua terminal di VS Code / Windows Terminal:
   - **Terminal 1:** Jalankan agent worker (`uv run python -m lajur_agent.worker dev` atau `docker compose up agent`).
   - **Terminal 2:** Jalankan web frontend (`npm run dev` di `apps/web`).
2. [ ] Buka browser di `http://localhost:3000`.
3. [ ] Siapkan mikrofon dan earphone (agar tidak ada feedback loop akustik selama demo).
4. [ ] Buka tab terminal ketiga untuk menjalankan suite test `pytest`.

---

## Alur & Naskah Rekaman (Timeline)

### 00:00 – 00:25 | Pembukaan & Konteks Arsitektur
- **Aksi Layar:** Tampilkan layar browser `http://localhost:3000` (aplikasi web Lajur).
- **Narasi:**
  > *"Halo! Ini adalah update progres Minggu ke-1 untuk proyek **Lajur** — sistem drive-thru voice ordering bilingual Indonesia-Inggris.*
  > *Fokus minggu ini adalah membangun **Walking Skeleton**: membuktikan jalur WebRTC end-to-end dari browser ke Python worker, serta membangun mesin kalkulasi keranjang belanja deterministik murni tanpa bergantung pada API AI pihak ketiga terlebih dahulu.*
  > *Mengapa? Supaya kita memvalidasi plumbing latensi dan state machine sebelum membakar biaya vendor STT, LLM, atau TTS."*

### 00:25 – 00:55 | Uji Coba Audio Echo & Latensi WebRTC
- **Aksi Layar:**
  1. Klik tombol **"Mulai Sesi Pesan"** di browser.
  2. Tunjukkan badge status berubah hijau: `● Terhubung (Room: lajur-...)`.
  3. Perhatikan indikator **Latensi RTT (Round-Trip Time)** yang muncul live (misal: ~35 ms lokal).
  4. Ucapkan kalimat uji ke mikrofon: *"Halo kasir, saya mau pesan satu paket hemat burger."*
  5. Terdengar pantulan suara kembali secara instan dan jernih lewat earphone.
- **Narasi:**
  > *"Ketika saya menekan tombol Mulai Sesi, browser meminta token ephemeral dari Next.js server route, lalu tersambung ke LiveKit room.*
  > *Worker Python di backend menerima stream audio mentah melalui `AudioStream`, lalu memancarkannya kembali secara langsung ke `AudioSource` tanpa proses AI.*
  > *Secara bersamaan, browser dan worker bertukar detak heartbeat melalui WebRTC Data Channel `lajur-control` untuk mencatat RTT latensi jaringan secara realtime. Kita membuktikan latensi dasar WebRTC berada di level sub-100 milidetik sebelum penambahan model AI."*

### 00:55 – 01:30 | Mesin Keranjang Belanja Deterministik (`packages/cart`)
- **Aksi Layar:** Pindah ke Terminal 3. Jalankan perintah:
  `uv run pytest packages/cart/tests -v`
  Tunjukkan 149 tes lulus dengan 100% green dalam waktu < 0.5 detik.
- **Narasi:**
  > *"Di layer logika bisnis, kita telah menyelesaikan paket murni `packages/cart`.*
  > *Sesuai aturan arsitektur kami, LLM tidak boleh memiliki wewenang mengubah harga atau langsung menyentuh database. Keranjang dikelola 100% oleh MenuService deterministik.*
  > *Di sini ada 149 unit tests yang mencakup seluruh aturan:*
  > *Pertama, validasi slot combo bertingkat; kedua, jam operasional sarapan yang deterministik menggunakan clock injection; ketiga, batas maksimal 20 item per pesanan untuk mencegah denial-of-wallet; dan keempat, verifikasi 135 skenario dev dataset dengan perhitungan total rupiah yang presisi."*

### 01:30 – 01:50 | Dataset Evaluasi v0.1 & Kesiapan Gerbang G1
- **Aksi Layar:** Buka file `eval/datasets/v0/COVERAGE.md` di editor. Tampilkan tabel statistik:
  - 135 skenario total (40% code-switching ID-EN)
  - 11 skenario noise helm motor
  - 35 skenario handwritten alami
- **Narasi:**
  > *"Untuk dataset pengujian, kita memperluas cakupan ke v0.1 dengan 135 skenario terverifikasi.*
  > *40% di antaranya menggunakan code-switching campuran bahasa Indonesia dan Inggris, dan 11 skenario menyimulasikan derau helm pengendara motor untuk menguji ketahanan akustik.*
  > *Dataset ini siap digunakan sebagai tolak ukur objektif pada Gerbang G1 minggu depan."*

### 01:50 – 02:00 | Penutup & Rencana Minggu 2
- **Aksi Layar:** Kembali ke browser atau diagram arsitektur.
- **Narasi:**
  > *"Walking skeleton berdiri, fondasi keranjang teruji, dan repositori bersih dengan CI green.*
  > *Minggu ke-2, kita akan melangkah ke Gerbang G1: benchmark streaming STT antara Deepgram Nova-3, Soniox, dan Gladia. Sampai jumpa di update berikutnya!"*
