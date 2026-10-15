# ADR-0007: Strategi Evaluasi Bertahap: Dataset Sintetis Terlebih Dahulu, Ditumbuhkan dari Trace Nyata

## Status
Accepted

## Konteks
Evaluasi sistem AI percakapan membutuhkan korpus pengujian yang representatif. Namun, pada tahap awal proyek mandiri (Minggu 0–Minggu 4), belum ada pengguna dan belum ada lalu lintas data rekaman suara nyata yang tersedia. Mengumpulkan ratusan rekaman suara manusia di awal membutuhkan biaya, waktu rekrutmen, serta persetujuan privasi yang rumit sebelum pipeline dasarnya terbukti berfungsi (*tracer bullet*).

## Keputusan
Menerapkan strategi **Synthetic-First Evaluation, Grown from Real Traces**:
1. **Fase Awal (Minggu 0 s/d Minggu 6)**: Membangun dataset skenario terstruktur berbasis teks dan audio sintetis (`eval/datasets/v0/`). Ujaran audio sintetis dibuat menggunakan multi-voice TTS dan dicampur (*mixed*) dengan simulasi derau latar belakang (motor idle, knalpot, filter helm) pada rentang SNR (Signal-to-Noise Ratio) 0–15 dB.
2. **Fase Evaluasi Baseline (Minggu 7 / Gerbang G2)**: Mengunci dataset uji menjadi dua bagian: *dev split* (untuk iterasi tuning prompt dan alias) dan *held-out split* (tidak pernah dilihat selama tuning untuk menguji generalisasi).
3. **Fase Pasca-Peluncuran (Minggu 9 s/d Minggu 10)**: Memperkaya dataset dengan kasus-kasus kegagalan baru yang diekstraksi dari transkrip teks anonim sesi pengguna nyata (*production traces*).

## Alternatif yang Ditolak
- **Menunda Evaluasi Sampai Mendapatkan Rekaman Suara Pelanggan Asli**: Ditolak karena melanggar prinsip *Eval-Driven Development*; rekayasawan tidak dapat mengukur regresi akurasi saat mengembangkan modul state machine dan prompt.
- **Hanya Mengandalkan Evaluasi Sintetis Selamanya Tanpa Validasi Data Lapangan**: Ditolak karena suara sintetis TTS memiliki artikulasi fonetik yang terlalu bersih dan sering gagal memodelkan intonasi rancu, jeda canggung (*hesitation*), dan artikulasi tidak jelas penutur asli.

## Konsekuensi
- **Positif:**
  - Pipeline pengujian otomatis dapat dijalankan sejak Minggu 1 dalam CI tanpa menunggu keterlibatan manusia.
  - Skalabilitas pengujian variasi derau (derau motor, hujan, helm) dapat disimulasikan secara presisi dan konsisten.
  - Privasi terjamin sepenuhnya pada tahap pengembangan awal.
- **Negatif / Mitigasi:**
  - Evaluasi sintetis berisiko memberikan skor akurasi yang lebih optimis dibanding performa lapangan. Mitigasi: Di Minggu 2 dan Minggu 7 dilakukan pengujian sampling manual menggunakan suara pengembang sendiri pada perangkat fisik iPhone dan jaringan seluler.
