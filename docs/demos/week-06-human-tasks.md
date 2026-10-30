# Daftar Tugas Manusia & Alokasi Kuota (Minggu 6 Checklist)

**Dokumen:** `docs/demos/week-06-human-tasks.md`  
**Milestone:** Minggu 6 — Robustness & Validasi Pasar  
**Pelaksana:** Daryl (Solo Developer & Project Owner)  
**Status Keseluruhan:** PENDING (Belum dieksekusi oleh manusia)  

---

## 1. Status Kuota Vendor Terverifikasi (Read-Only Query)

Informasi kuota dibaca langsung dari endpoint resmi ElevenLabs:
- **Paket / Tier:** `free`
- **Karakter Terpakai:** 8.424 / 10.000 karakter
- **Sisa Kuota Karakter:** **1.576 karakter**
- **Waktu Reset Kuota:** `2026-11-20T01:09:16Z` (20 November 2026, 08:09:16 WIB)
- **Batas Groq Cloud (Qwen 3.8 27B):** 8.000 TPM (Token Per Menit), 200.000 TPD (Token Per Hari). Estimasi per giliran percakapan: ~1.604 token/turn (maksimum konkurensi aman: ~4 turn/menit; uji harus dilakukan 1 orang per waktu secara serial).

---

## 2. Checklist Tugas Pengujian Nyata (*Human Tasks Checklist*)

| No | Tugas Pengujian | Asal Milestone | Target & Prasyarat | Estimasi Biaya Kuota | Status Saat Ini |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Uji Desktop Langsung (Live Check)** | Minggu 5 & 6 | Menjalankan worker lokal (`lajur-agent worker`) + browser live mode dengan mikrofon desktop. Menguji VAD adaptif dan interupsi suara (*barge-in*). | ~3 turn $\approx$ ~250 karakter ElevenLabs, ~4.800 token Groq | **PENDING** |
| **2** | **Uji Order Suara di Perangkat Nyata (Real-Device Voice Order)** | Minggu 4 | Membuka simulator via Safari / Chrome pada iPhone fisik (memerlukan tunnel HTTPS atau localhost proxy, bukan IP lokal mentah per aturan browser WebRTC). | ~3 turn $\approx$ ~250 karakter ElevenLabs, ~4.800 token Groq | **PENDING** |
| **3** | **Uji Kebergunaan 3 Orang Awam (Usability Test)** | Minggu 5 | 3 orang non-teknis memesan makanan secara mandiri tanpa panduan. **Dijadwalkan ulang ke akhir Minggu 6 pasca reset kuota ElevenLabs pada 20 November 2026**. | 3 orang $\times$ 5 turn = 15 turn $\approx$ **1.200 karakter ElevenLabs**, ~24.000 token Groq | **PENDING (Menunggu Reset 20 Nov)** |
| **4** | **Wawancara Mom Test F&B ($\ge 3$ Selesai)** | Minggu 6 & §16 | Wawancara 15–20 menit dengan $\ge 3$ pemilik/staf gerai F&B nyata menggunakan panduan di `docs/interviews/interview-guide-id.md`. | **0 karakter, 0 token ($0.00 vendor spend)** | **PENDING** |

---

## 3. Prosedur Eksekusi Aman (*Zero Spend & Rate Guard*)

1. **Jaga Batas Karakter ElevenLabs:**  
   Sisa kuota hanya **1.576 karakter**. Jangan menjalankan pengujian suara berulang kali di live mode sebelum tanggal reset 20 November 2026. Gunakan mode replay simulator untuk demonstrasi umum tanpa memakan kuota.
2. **Uji Kebergunaan (3 Orang):**  
   Wajib dijalankan satu per satu secara bergantian (jangan bersamaan) agar tidak melampaui batas 8.000 TPM Groq.
3. **Wawancara Mom Test:**  
   Catat hasil wawancara asli ke berkas `docs/interviews/session-0X-notes.md` lalu sintesiskan ke `docs/interviews/synthesis-template.md`. Jangan pernah memasukkan kutipan atau hasil karangan.
