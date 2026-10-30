# Daftar Tugas Manusia & Alokasi Kuota (Minggu 6 Checklist)

**Dokumen:** `docs/demos/week-06-human-tasks.md`  
**Milestone:** Minggu 6 — Robustness & Validasi Pasar  
**Pelaksana:** Daryl (Solo Developer & Project Owner)  
**Status Keseluruhan:** PENDING (Belum dieksekusi oleh manusia)  

---

## 1. Status Kuota Vendor Terverifikasi (Read-Only Query)

Informasi kuota dibaca langsung dari endpoint resmi ElevenLabs via query baca-saja (*read-only*):
- **Metode Pembacaan:** HTTP `GET https://api.elevenlabs.io/v1/user/subscription` dengan header `xi-api-key`. Kueri ini bersifat 100% baca-saja (*read-only metadata*), tidak melakukan sintesis suara, tidak memakan karakter, dan berbiaya $0.00.
- **Paket / Tier:** `free`
- **Karakter Terpakai:** 8.424 / 10.000 karakter
- **Sisa Kuota Karakter:** **1.576 karakter**
- **Waktu Reset Kuota:** `2026-11-20T01:09:16Z` (20 November 2026, 08:09:16 WIB)
- **Rekomendasi Kuota:** Sesi uji kebergunaan pengguna (*usability testing*) dengan suara balasan audio **WAJIB dilaksanakan setelah tanggal reset kuota (pasca 20 November 2026)** agar tersedia kuota penuh 10.000 karakter dan mencegah kegagalan sintesis di tengah sesi pengujian.
- **Batas Groq Cloud (Qwen 3.8 27B):** 8.000 TPM (Token Per Menit), 200.000 TPD (Token Per Hari). Estimasi per giliran percakapan: ~1.604 token/turn (maksimum konkurensi aman: ~4 turn/menit; uji harus dilakukan 1 orang per waktu secara serial).

---

## 2. Urutan Prioritas Tugas Tertunda Daryl (*Order of Pending Tasks*)

Sesuai ketersediaan kuota dan efisiensi waktu tunggu (*lead time*), berikut adalah urutan pelaksanaan tugas yang wajib diikuti:

1. **Mulai Kontak & Penjadwalan Wawancara Mom Test Sekarang (*Start interview outreach now*)**
   - *Rasional:* Memiliki waktu tunggu (*lead time*) terlama untuk mencari dan mencocokkan jadwal pemilik F&B.
   - *Biaya Kuota:* 0 karakter ElevenLabs, 0 token Groq ($0.00).
   - *Panduan:* Gunakan pesan kontak di `docs/interviews/recruiting-message.md` dan panduan di `docs/interviews/interview-guide-id.md`.

2. **Uji Desktop Langsung (*Live desktop check*)**
   - *Rasional:* Verifikasi teknis cepat (sanity check) memastikan worker lokal dan simulator web live mode terhubung stabil.
   - *Biaya Kuota:* ~2–3 turn $\approx$ ~200 karakter ElevenLabs, ~4.000 token Groq (sangat aman di dalam sisa 1.576 karakter).

3. **Uji Order Suara di Perangkat Nyata (*Real-device order test*)**
   - *Rasional:* Menyelesaikan milestone fisik carryover Minggu 4 (1 order tuntas melalui peramban ponsel fisik iPhone via HTTPS tunnel/Vercel preview).
   - *Biaya Kuota:* ~3 turn $\approx$ ~250 karakter ElevenLabs, ~4.800 token Groq.

4. **Sesi Uji Kebergunaan 3 Orang Awam Pasca Reset (*Usability sessions after the reset*)**
   - *Rasional:* Memerlukan alokasi kuota suara yang cukup besar (15+ turn $\approx$ 1.200–1.500 karakter). Menunggu reset 20 November 2026 menjamin pengujian tidak terhenti akibat kuota habis.
   - *Prasyarat:* Kuota ElevenLabs telah ter-reset ke 10.000 karakter pada 20 November 2026.
   - *Panduan:* Gunakan protokol `docs/demos/week-05-usability-protocol.md`.

---

## 3. Matriks Ringkasan Tugas Pengujian

| No | Urutan Eksekusi | Tugas Pengujian | Asal Milestone | Target & Prasyarat | Estimasi Biaya Kuota | Status Saat Ini |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Prioritas 1 | **Outreach Wawancara Mom Test ($\ge 3$ Selesai)** | Minggu 6 & §16 | Wawancara 15–20 menit dengan $\ge 3$ pemilik/staf gerai F&B nyata tanpa menjual produk. | **0 karakter, 0 token ($0.00 vendor spend)** | **PENDING (Mulai Sekarang)** |
| **2** | Prioritas 2 | **Uji Desktop Langsung (Live Check)** | Minggu 5 & 6 | Menjalankan worker lokal (`lajur-agent worker`) + browser live mode dengan mikrofon desktop. Menguji VAD adaptif dan interupsi suara (*barge-in*). | ~3 turn $\approx$ ~250 karakter ElevenLabs, ~4.800 token Groq | **PENDING** |
| **3** | Prioritas 3 | **Uji Order Suara di Perangkat Nyata (Real-Device Voice Order)** | Minggu 4 | Membuka simulator via Safari / Chrome pada iPhone fisik (memerlukan tunnel HTTPS atau localhost proxy, bukan IP lokal mentah per aturan browser WebRTC). | ~3 turn $\approx$ ~250 karakter ElevenLabs, ~4.800 token Groq | **PENDING** |
| **4** | Prioritas 4 | **Uji Kebergunaan 3 Orang Awam (Usability Test)** | Minggu 5 | 3 orang non-teknis memesan makanan secara mandiri tanpa panduan. Dilakukan bergiliran serial. | 3 orang $\times$ 5 turn = 15 turn $\approx$ **1.200 karakter ElevenLabs**, ~24.000 token Groq | **PENDING (Wajib Setelah Reset 20 Nov)** |

---

## 4. Prosedur Eksekusi Aman (*Zero Spend & Rate Guard*)

1. **Jaga Batas Karakter ElevenLabs:**  
   Sisa kuota saat ini adalah **1.576 karakter**. Jangan menjalankan pengujian suara berulang kali di live mode sebelum tanggal reset 20 November 2026. Gunakan mode replay simulator untuk demonstrasi umum tanpa memakan kuota.
2. **Uji Kebergunaan (3 Orang):**  
   Wajib dijalankan satu per satu secara bergantian (jangan bersamaan) agar tidak melampaui batas 8.000 TPM Groq.
3. **Wawancara Mom Test:**  
   Catat hasil wawancara asli ke berkas `docs/interviews/session-0X-notes.md` lalu sintesiskan ke `docs/interviews/synthesis-template.md`. Jangan pernah memasukkan kutipan atau hasil karangan.
