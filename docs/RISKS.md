# Risk Register — Lajur

**Versi:** 1.0 · **Terakhir Diperbarui:** 2026-10-15 (Minggu 0 Kickoff)  
**Aturan Pembaruan:** Ditinjau dan diperbarui setiap sesi evaluasi mingguan. Skor Risiko = Probabilitas (P: 1–5) × Dampak (I: 1–5).

---

## 1. Tabel Risiko Aktif (v1)

| ID | Risiko | Kategori | P (1–5) | I (1–5) | Skor | Strategi Mitigasi | Indikator Pemicu (*Trigger*) | Status |
|---|---|---|:---:|:---:|:---:|---|---|:---:|
| **R1** | STT gagal mengenali *code-switching* ID–EN (menu Inggris dalam kalimat Indo) | Teknis | 4 | 5 | **20** | Benchmark 4 vendor di Gerbang G1 (Minggu 2); pasang keyterm boost & alias fonetik; fallback normalisasi LLM pasca-STT; evaluasi model multimodal. | Keyterm Error Rate (KER) > 15% pada dev dataset | Aktif |
| **R2** | Kuota bulanan LiveKit Cloud Build (1.000 menit agent) habis sebelum akhir bulan | Operasional | 4 | 3 | **12** | Batasi durasi sesi maks 3 menit; kuota harian global (~10–12 sesi/hari); sediakan fallback mode teks interaktif (FR-14); siapkan arsitektur self-host di VM Singapura. | Kuota terpakai > 80% sebelum tanggal 20 bulan berjalan | Aktif |
| **R3** | Lonjakan biaya vendor tak terkendali akibat bot, abuse, atau *wallet draining* | Finansial / Keamanan | 3 | 4 | **12** | Pasang Cloudflare Turnstile captcha; rate-limiting per IP; batas maksimal 20 item per pesanan; batas token LLM; pasang *hard spend cap* dan alert di setiap dashboard vendor. | Biaya harian aktual melebihi $1,00/hari | Aktif |
| **R4** | Latensi turn *end-to-end* melebihi batas kenyamanan (> 1,3 detik) dari koneksi Indonesia | Teknis | 3 | 4 | **12** | Pilih edge region terdekat (Singapura / Jakarta); optimasi VAD turn detection; streaming parsial audio; pilih model LLM ber-TTFT rendah (Flash / Groq). | Latensi P95 > 1.500 ms pada pengujian internet publik | Aktif |
| **R5** | *Scope Creep* (penambahan fitur di luar batasan portofolio & waktu solo dev) | Proses | 4 | 3 | **12** | Kunci daftar *Non-Goals* (§4.2) secara ketat; ide baru wajib dimasukkan ke `docs/BACKLOG-LATER.md`; tidak menambah fitur baru tanpa menghapus fitur lama setara. | Muncul tugas di luar PRD tanpa persetujuan ADR | Aktif |
| **R6** | Perubahan harga, pemutusan model, atau pemotongan free tier secara sepihak oleh vendor | Dependensi | 4 | 3 | **12** | Gunakan arsitektur adapter (ADR-0004); verifikasi rutin docs vendor; gunakan provider dengan API kompatibel (OpenAI-compatible). | Pemberitahuan deprecasi API / sunset model dari vendor | Aktif |
| **R7** | Pelanggaran privasi / data transkrip pengguna publik dijadikan bahan training model AI | Privasi / Legal | 3 | 4 | **12** | Dilarang menggunakan free tier yang mengeksploitasi data prompt; wajib menggunakan tier komersial berbayar (zero-data-retention policy); tampilkan consent banner jelas. | Menemukan klausul TOS vendor yang mengambil hak training atas payload API | Aktif |
| **R8** | Batasan konkurensi Azure Speech TTS Free Tier (F0: hanya 1 request simultan) menyebabkan antrean | Teknis | 3 | 3 | **9** | Evaluasi migrasi ke tier S0 Pay-As-You-Go ($16/1 jt karakter) dengan budget alert, atau gunakan Cartesia Sonic. | Log mendeteksi HTTP 429 Too Many Requests pada TTS | Aktif |
| **R9** | Kehabisan waktu dan kelelahan solo developer (kapasitas hanya 10–15 jam/minggu) | Proses | 3 | 4 | **12** | Sediakan masa penyangga di Minggu 8–10; pangkas fitur opsional (preset noise 4, dashboard publik) jika jadwal terancam; jangan pernah memangkas evaluasi (Minggu 7). | Dua minggu berturut-turut target mingguan tidak tercapai | Aktif |
| **R10** | Hasil akurasi akhir (*Order Accuracy Rate*) di bawah ekspektasi pasar | Kualitas Produk | 3 | 3 | **9** | Publikasikan data apa adanya secara transparan disertai *error analysis* mendalam; sesuaikan klaim ke domain yang lebih sempit; fokuskan nilai portofolio pada transparansi rekayasa. | Hasil evaluasi Gerbang G2 (Minggu 7) menghasilkan OAR < 75% | Aktif |
| **R11** | Masalah legal merek dagang terkait nama makanan atau format menu | Legal | 2 | 3 | **6** | Gunakan nama menu generik fiktif 100% (ADR-0006); simpan pemetaan merek nyata secara privat di luar repositori publik (`private/`). | Adanya kemiripan nama produk fiktif dengan merek terdaftar | Aktif |
| **R12** | Ketiadaan validasi pasar / pengguna tidak bersedia membayar (jalur startup) | Bisnis | 4 | 2 | **8** | Lakukan wawancara *The Mom Test* kepada 8–10 pemilik F&B sejak Minggu 6; hentikan ekspansi startup di Gerbang G3 jika sinyal bayar nihil, pertahankan sebagai portofolio murni. | Kurang dari 2 pemilik F&B bersedia pilot di akhir Minggu 10 | Aktif |

---

## 2. Rangkuman Tindakan Segera Minggu 0
1. **Mitigasi R3 & R7:** Pastikan seluruh vendor API menggunakan akun dengan tier berbayar yang menjamin kerahasiaan data (no-training) dan menetapkan hard spend limit di masing-masing dashboard.
2. **Mitigasi R11:** Pastikan file pemetaan merek asli ke item generik berada di folder `private/` dan terbukti diabaikan oleh git (`.gitignore`).
