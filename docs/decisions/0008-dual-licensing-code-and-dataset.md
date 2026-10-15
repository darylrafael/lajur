# ADR-0008: Lisensi Ganda: Apache-2.0 untuk Kode dan CDLA-Permissive-2.0 untuk Dataset Sintetis

## Status
Proposed, pending vendor verification

## Konteks
Proyek Lajur menghasilkan dua jenis artefak utama:
1. **Source Code**: Implementasi arsitektur perangkat lunak (aplikasi web Next.js, worker Python, library cart state machine, skrip pengujian).
2. **Dataset & Benchmark**: Korpus teks skenario pemesanan, definisi relasi menu JSON, konfigurasi profil derau, dan laporan evaluasi metrik akurasi.

Pemilihan lisensi sumber terbuka harus memperhatikan:
- Perlindungan hak paten timbal balik (*patent grant*).
- Kredibilitas dan kenyamanan reviewer teknis/recruiter perusahaan teknologi.
- Kejelasan hak cipta atas dataset benchmarking data publik tanpa klausul viral copyleft yang menghambat adopsi.
- Opsi untuk melanjutkan ke entitas startup komersial pasca Gerbang G3 tetap terbuka.

## Keputusan
Kami mengusulkan model lisensi terpisah:
1. **Kode Sumber Perangkat Lunak**: Menggunakan lisensi **Apache License 2.0** (`LICENSE`). Lisensi ini memberikan izin penggunaan komersial yang luas, kewajiban atribusi yang jelas, serta klausul hibah paten eksplisit (*express patent grant*) yang melindungi kontributor dan pengguna.
2. **Dataset dan Artefak Evaluasi**: Menggunakan lisensi **Community Data License Agreement – Permissive – Version 2.0 (CDLA-Permissive-2.0)** (`eval/LICENSE-DATA.md`). Lisensi data standar dari The Linux Foundation ini secara spesifik dirancang untuk data terbuka (bukan kode software) tanpa klausul restriksi paten software yang tidak relevan bagi tabel data.

## Alternatif yang Ditolak
- **MIT License untuk Seluruh Proyek**: Ditolak karena MIT tidak memiliki klausul perlindungan hak paten eksplisit yang melindungi aset rekayasa.
- **GNU AGPLv3 / Copyleft**: Ditolak karena lisensi viral copyleft sering menjadi lampu merah bagi reviewer perusahaan enterprise dan mempersulit potensi monetisasi komersial jika proyek berkembang menjadi startup.
- **Creative Commons (CC-BY / CC0) untuk Kode**: Ditolak karena Creative Commons secara resmi tidak direkomendasikan untuk perangkat lunak komputasi.

## Konsekuensi
- **Positif:**
  - Standar industri tinggi yang diakui komunitas open-source global dan ekosistem enterprise.
  - Memisahkan secara tegas hak cipta algoritma software dengan hak distribusi korpus data evaluasi.
  - Menjaga kebebasan bagi publik untuk mereproduksi hasil benchmark evaluasi.
- **Negatif / Mitigasi:**
  - Diperlukan pengelolaan dua file lisensi yang berbeda di repositori (`LICENSE` di root dan `eval/LICENSE-DATA.md`). Struktur ini didokumentasikan secara gamblang di `README.md`.
