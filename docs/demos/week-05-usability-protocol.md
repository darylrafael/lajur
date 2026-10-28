# Protokol Uji Ketergunaan Web Simulator — Minggu 5

**Dokumen:** `docs/demos/week-05-usability-protocol.md`  
**Milestone:** Minggu 5 (Web Simulator Usability Testing)  
**Target Rencana (§13):** *"3 orang awam menyelesaikan order di perangkat sendiri."*  
**Status Sesi:** **PENDING ON DARYL [HUMAN]** (Asisten AI tidak mengarang hasil pengujian nyata).  
**Kepatuhan Privasi:** Mematuhi ADR-0005 (*Zero Audio Persistence*) dan ADR-0009 (*Hosting Vercel & Worker*).

---

## 1. Profil & Rekrutmen Partisipan

- **Jumlah Partisipan:** 3 orang non-teknis (teman, keluarga, atau rekan yang bukan pengembang perangkat lunak dan tidak mengetahui arsitektur internal Lajur).
- **Perangkat:** Ponsel pintar milik partisipan sendiri (iPhone via Safari Mobile atau Android via Chrome Mobile), atau laptop pribadi via browser modern.
- **Kondisi Pengujian:** Mandiri tanpa panduan teknis (*unassisted*). Penguji (Daryl) hanya memberikan URL simulator dan skrip tugas.

---

## 2. Pernyataan Persetujuan & Privasi (*Informed Consent*)

Sebelum pengujian dimulai, penguji membacakan atau memperlihatkan pernyataan persetujuan berikut kepada partisipan:

> **Pernyataan Privasi Partisipan (ADR-0005):**  
> "Aplikasi demo ini menggunakan mikrofon Anda untuk mentranskripsi suara pemesanan secara langsung. Sesuai prinsip *Zero Audio Persistence*, suara Anda **TIDAK PERNAH DIREKAM ATAU DISIMPAN** ke dalam media penyimpanan maupun server manapun. Data suara langsung dibuang dari memori segera setelah diproses. Tidak ada identitas pribadi yang dikumpulkan. Anda dapat menghentikan sesi kapan saja dengan menutup peramban atau menekan tombol 'Selesai'."

Partisipan harus menyatakan persetujuannya secara lisan atau tertulis sebelum mikrofon diaktifkan.

---

## 3. Skenario Tugas Pemesanan (*Task Script*)

Partisipan diminta menyelesaikan dua tugas bertahap dalam satu sesi pemesanan:

### Skenario 1: Memesan Paket Makanan Utama
- **Instruksi untuk Partisipan:**  
  *"Silakan pesan satu paket makanan lengkap (misalnya Paket Hemat Burger Tunggal) dengan minuman pilihan Anda dan kentang goreng menggunakan suara Anda."*
- **Kriteria Keberhasilan:**  
  Item paket masuk ke dalam keranjang, pilihan slot (minuman/sampingan) terjawab, dan total harga IDR tertera pada panel keranjang.

### Skenario 2: Mengubah / Mengoreksi Item Pesanan
- **Instruksi untuk Partisipan:**  
  *"Sekarang ubah minuman Anda menjadi minuman lain (misalnya ganti Teh Botol menjadi Sprite), atau batalkan salah satu item pesanan Anda menggunakan suara."*
- **Kriteria Keberhasilan:**  
  State machine menerapkan koreksi (`replace_item` atau `remove_item`), keranjang langsung terbarui di layar, dan transkrip menampilkan koreksi yang dipahami.

---

## 4. Metrik yang Dicatat

Untuk setiap partisipan, catat data berikut secara objektif:
1. **Penyelesaian Tugas (*Task Completion*):**
   - **Berhasil Mandiri (Success):** Menyelesaikan tanpa bantuan sama sekali.
   - **Berhasil dengan Bantuan (Assisted):** Membutuhkan petunjuk dari penguji saat tersangkut.
   - **Gagal (Fail):** Tidak dapat menyelesaikan pesanan atau membatalkan sesi.
2. **Durasi Waktu (*Time on Task*):** Waktu dari tombol mulai ditekan hingga konfirmasi akhir (dalam detik).
3. **Titik Kebingungan (*Confusion Points*):**
   - Ragu/jeda canggung karena menunggu respon suara bot.
   - Ketidakjelasan status mikrofon atau pertanyaan bot.
   - Kebingungan navigasi antara tab menu dan keranjang pada layar ponsel.
4. **Kutipan Verbatim (*Verbatim Quotes*):** Komentar spontan partisipan saat berinteraksi dengan simulator.

---

## 5. Templat Lembar Hasil Pengujian (*Results Sheet Template*)

> **CATATAN PENTING:** Lembar di bawah ini wajib diisi oleh **Daryl [HUMAN]** setelah menjalankan sesi pengujian dengan 3 partisipan nyata.

### Partisipan 1
- **Nama/Inisial:** [Isi inisial, misal: P1 - Rekan Non-Teknis]
- **Perangkat & Browser:** [Misal: iPhone 13, Safari Mobile iOS 17.5]
- **Mode Uji:** [Live WebRTC / Replay Mode]
- **Tugas 1 (Pesan Makanan):** [Berhasil Mandiri / Berhasil dengan Bantuan / Gagal]
- **Tugas 2 (Koreksi Pesanan):** [Berhasil Mandiri / Berhasil dengan Bantuan / Gagal]
- **Waktu Penyelesaian:** [____ detik]
- **Titik Kebingungan:**
  - [Catat kebingungan partisipan jika ada]
- **Kutipan Verbatim:**
  - *"[Kutipan kata-kata langsung partisipan]"*
- **Catatan Penguji:** [Observasi Daryl]

---

### Partisipan 2
- **Nama/Inisial:** [Isi inisial]
- **Perangkat & Browser:** [Misal: Samsung Galaxy S22, Chrome Mobile]
- **Mode Uji:** [Live WebRTC / Replay Mode]
- **Tugas 1 (Pesan Makanan):** [Berhasil Mandiri / Berhasil dengan Bantuan / Gagal]
- **Tugas 2 (Koreksi Pesanan):** [Berhasil Mandiri / Berhasil dengan Bantuan / Gagal]
- **Waktu Penyelesaian:** [____ detik]
- **Titik Kebingungan:**
  - [Catat kebingungan partisipan jika ada]
- **Kutipan Verbatim:**
  - *"[Kutipan kata-kata langsung partisipan]"*
- **Catatan Penguji:** [Observasi Daryl]

---

### Partisipan 3
- **Nama/Inisial:** [Isi inisial]
- **Perangkat & Browser:** [Misal: MacBook Air, Google Chrome Desktop]
- **Mode Uji:** [Live WebRTC / Replay Mode]
- **Tugas 1 (Pesan Makanan):** [Berhasil Mandiri / Berhasil dengan Bantuan / Gagal]
- **Tugas 2 (Koreksi Pesanan):** [Berhasil Mandiri / Berhasil dengan Bantuan / Gagal]
- **Waktu Penyelesaian:** [____ detik]
- **Titik Kebingungan:**
  - [Catat kebingungan partisipan jika ada]
- **Kutipan Verbatim:**
  - *"[Kutipan kata-kata langsung partisipan]"*
- **Catatan Penguji:** [Observasi Daryl]

---

## 6. Ringkasan & Kesimpulan Akhir (*Post-Test Evaluation*)

| Metrik Agregat | Target Rencana (§13) | Hasil Nyata (3 Partisipan) | Status |
| :--- | :--- | :--- | :--- |
| Jumlah Partisipan Menyelesaikan Order | 3 orang awam di perangkat sendiri | [Diisi setelah uji] | **PENDING [HUMAN]** |
| Tingkat Keberhasilan Mandiri (*Unassisted Rate*) | $\ge 67\%$ (2 dari 3 orang) | [Diisi setelah uji] | **PENDING [HUMAN]** |
| Evaluasi Live Transcript vs Latensi Suara | Transkrip instan meredam persepsi jeda latensi bot | [Diisi setelah uji] | **PENDING [HUMAN]** |
