# ADR-0006: Penggunaan Menu Generik Fiktif Berstruktur Cepat Saji

## Status
Accepted

## Konteks
Tujuan teknis proyek Lajur adalah membuktikan bahwa sistem dapat menangani kompleksitas struktural pemesanan makanan cepat saji (item burger, paket hemat combo bertingkat, modifier wajib/opsional seperti ukuran minuman atau saus, menu sarapan vs reguler, serta ketersediaan stok *86'd*). 

Jika sistem menggunakan nama merek nyata (misalnya "McDonald's", "Big Mac", "McFlurry"), terdapat risiko hukum pelanggaran hak cipta dan merek dagang (*trademark infringement*).

## Keputusan
1. Seluruh data publik dalam repositori dan antarmuka demo publik menggunakan **nama fiktif dan generik** (misalnya "Burger Sapi Keju Ganda", "Ayam Renyah Spesial", "Paket Hemat Kenyang", "Es Kopi Susu Aren").
2. Struktur data menu (kategori, slot combo, modifier, batas jam sarapan) tetap mempertahankan kompleksitas setara restoran cepat saji global modern.
3. Tabel pemetaan (*mapping table*) dari nama merek asli dunia nyata ke nama generik disimpan secara **privat** di luar repositori publik (`private/`) untuk keperluan penyusunan skenario realistis tanpa mengeksposnya ke publik.

## Alternatif yang Ditolak
- **Menggunakan Nama Menu dan Merek McDonald's Asli Secara Terang-terangan**: Ditolak karena risiko *cease-and-desist* atau tuntutan hukum hak kekayaan intelektual (HAKI) dari pemegang merek.
- **Menu Sangat Sederhana (Hanya 5 Item Standar)**: Ditolak karena menu yang terlalu sederhana tidak mampu membuktikan kemampuan sistem dalam menangani skenario industri nyata (koreksi combo, modifier bersarang, dan ketersediaan dinamis).

## Konsekuensi
- **Positif:**
  - Aman 100% dari potensi sengketa hukum merek dagang.
  - Nilai teknis proyek tetap terbukti karena kompleksitas logika relasi data dan state machine tetap penuh.
  - Kemudahan mengadaptasi menu generik ke menu kafe/restoran lokal mitra jika lolos ke tahap pilot startup (Gerbang G3).
- **Negatif / Mitigasi:**
  - Pengguna uji mungkin terbiasa menyebut nama merek terkenal ("mau Big Mac satu"). Mitigasi: Di lingkungan internal/pengembangan privat disediakan alias fonetik pemetaan, namun pada demo publik bot kasir merespons dengan nama generik resminya.
