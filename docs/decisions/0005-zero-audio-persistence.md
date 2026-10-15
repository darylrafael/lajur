# ADR-0005: Kebijakan Tanpa Penyimpanan Audio Pengguna (Zero Audio Persistence)

## Status
Accepted

## Konteks
Sistem voice demo yang dibuka untuk umum rentan terhadap isu privasi dan kepatuhan hukum. Di berbagai yurisdiksi, termasuk regulasi perlindungan data di Indonesia (UU Perlindungan Data Pribadi No. 27/2022), rekaman suara manusia dikategorikan sebagai data biometrik spesifik yang memerlukan persetujuan eksplisit, tata kelola penyimpanan yang ketat, enkripsi tingkat lanjut, serta hak penghapusan data (*right to be forgotten*).

Menyimpan rekaman suara dari pengunjung demo publik (yang berpotensi anonim) membuka celah kebocoran data, risiko gugatan hukum, dan kebutuhan infrastruktur penyimpanan yang mahal.

## Keputusan
Sistem menerapkan prinsip **Zero Audio Persistence**:
- File audio/rekaman suara pengguna **SAMA SEKALI TIDAK PERNAH DISIMPAN** ke dalam media penyimpanan persisten (baik disk lokal server, database, maupun object storage seperti S3/GCS).
- Aliran audio hanya diproses di memori volatil (*RAM*) untuk kebutuhan VAD dan streaming ke STT provider, lalu segera dibuang (*flushed*).
- Hanya data transkrip teks anonim, intent JSON yang dihasilkan, serta metrik performa operasional (latensi turn, token count, status error) yang dicatat ke event log.
- Seluruh event log dibersihkan secara otomatis dengan masa retensi maksimal 30 hari.

## Alternatif yang Ditolak
- **Menyimpan Sampel Suara untuk Analisis Kesalahan (Error Debugging)**: Ditolak karena risiko pelanggaran privasi data biometrik melampaui manfaat teknisnya bagi proyek portofolio solo developer. Kebutuhan evaluasi diselesaikan dengan audio sintetis dan rekaman suara internal pengembang sendiri.
- **Opt-in Audio Recording**: Ditolak untuk versi awal guna menghindari kompleksitas pengelolaan consent database dan hak penarikan persetujuan.

## Konsekuensi
- **Positif:**
  - Kepatuhan privasi yang kuat dan perlindungan penuh terhadap risiko kebocoran data biometrik pengunjung demo.
  - Arsitektur backend lebih ramping tanpa kebutuhan pipeline kompresi dan storage bucket audio.
  - Menjadi nilai jual etika rekayasa (*privacy-first engineering*) yang solid bagi reviewer portofolio.
- **Negatif / Mitigasi:**
  - Tidak dapat memutar ulang audio asli pengguna jika STT salah mentranskripsikan kata. Mitigasi: Melakukan analisis kesalahan (*error analysis*) berbasis transkrip teks dan menduplikasi ucapan bermasalah menggunakan generator audio sintetis internal.
