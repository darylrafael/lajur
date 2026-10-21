# Gate G1 Final Validation Protocol: Live Pipeline Measurement (Minggu 4)

**Document:** `docs/gates/G1-minggu4-measurement.md`  
**Milestone:** Minggu 4 — Pengukuran Validasi Akhir Gerbang G1 pada Pipeline Nyata  
**Status:** Pre-registered (Committed in Minggu 2g)  
**Date:** 2026-10-21  
**Author:** Daryl (Solo Dev) & Implementation Agent  
**Rigidity Clause:** *Protokol ini telah disetujui dan dikomit sebelum pekerjaan Minggu 3 dan Minggu 4 dimulai. Protokol ini tidak dapat diubah tanpa persetujuan tertulis eksplisit dari pemilik proyek (Daryl).*

---

## 1. Konteks & Tujuan

Pada penutupan Minggu 2 (ADR-0013 status "Accepted by owner"), Gerbang G1 secara resmi dicatat sebagai **"not demonstrated"** (belum terbukti lulus, namun tidak ditolak mutlak). Keputusan yang diambil adalah **Opsi A-conditional**:
- Mempertahankan ambang batas Service Level Objective (SLO) latensi turn **$\le 1.200\text{ ms}$ (1.2 detik)**.
- Menetapkan pengukuran end-to-end pada pipeline WebRTC LiveKit nyata terintegrasi di Minggu 4 sebagai titik keputusan final (*definitive decision point*).
- Menjadwalkan fallback: Jika pengukuran Minggu 4 gagal memenuhi $\le 1.2\text{ s}$, pemilik proyek (Daryl) akan secara resmi menetapkan Opsi B dengan angka target latensi baru yang ditetapkan secara apriori berdasarkan justifikasi pengalaman pengguna (*user experience*) drive-thru sebelum pengukuran lanjutan.

---

## 2. Definisi Metrik Latensi Turn Realistis

Latensi turn percakapan pada pipeline nyata didefinisikan secara presisi sebagai:
$$\text{Turn Latency} = T_{\text{first\_audio\_out}} - T_{\text{speech\_end\_in}}$$

Di mana:
1. $T_{\text{speech\_end\_in}}$: Waktu tepat saat fonem terakhir dari ucapan pengguna selesai diartikulasikan di mikrofon peramban (*true speech end*).
   - **Metode Penentuan Referensi:** Diperoleh secara objektif melalui berkas audio berstempel waktu presisi (*scripted audio benchmark*) di mana durasi eksak bagian percakapan aktif diketahui hingga skala milidetik sebelum jeda hening alami, atau via forced-alignment auditori.
2. $T_{\text{first\_audio\_out}}$: Waktu paket frame audio pertama dari sintesis balasan suara kasir AI diterima dan siap dimainkan pada WebRTC audio receiver di peramban klien.
3. **Komponen yang Dicakup Secara Nyata:**
   - Jeda hening endpointing STT streaming (Deepgram Nova-3).
   - Waktu jaringan WebSocket/WebRTC dari peramban ke server LiveKit dan worker agen.
   - Waktu eksekusi Cart State Machine deterministik (`packages/cart`).
   - LLM Time to First Token (TTFT) streaming (Groq Qwen-27b).
   - TTS Time to First Audio Byte (TTFB) streaming (ElevenLabs Free Tier / kandidat resmi).
   - Buffer playout WebRTC LiveKit klien.

---

## 3. Metodologi Pengujian & Aturan Statistik

1. **Ukuran Sampel (*Sample Size*):**
   Minimal **30 giliran percakapan (*turns*)** yang mencakup pesanan sederhana, pesanan bernomor/kombo, dan variasi modifikasi menu.
2. **Kondisi Lingkungan Pengujian:**
   - Klien: Peramban fisik (Chrome/Safari) yang terhubung ke sesi WebRTC LiveKit nyata dari jaringan internet Indonesia.
   - Pacing Audio: Real-time $1.0\times$ streaming (tidak ada batch file upload).
   - Worker: LiveKit Python Agent Worker yang menjalankan pipeline penuh (STT adapter + Cart State Machine + LLM intent parser + TTS streaming).
3. **Statistik yang Wajib Dilaporkan:**
   - Median (P50)
   - Persentil ke-95 (P95)
   - Rata-rata (*Mean*) dengan 95% Bootstrap Confidence Interval (10.000 kali percontohan ulang).
   - Rasio keberhasilan (*Success Rate*) pemenuhan batas $\le 1.200\text{ ms}$.

---

## 4. Kriteria Keputusan Gerbang G1 di Minggu 4

1. **Kriteria Lolos (PASS):**
   Jika hasil pengukuran terbukti memenuhi:
   - Median (P50) Latensi Turn $\le 1.200\text{ ms}$ pada pipeline nyata.
   - Akurasi keranjang akhir (*resulting cart*) pada sesi suara interaktif $\ge 80\%$.
   - Tidak ada ketergantungan pada API tidak resmi (*no unofficial browser scraping APIs*).
   *Maka Gerbang G1 dinyatakan Lulus Definitif (PASS).*

2. **Kriteria Gagal & Tindakan Fallback Otomatis (MISS):**
   Jika P50 latensi turn terukur $> 1.200\text{ ms}$:
   - Pemilik proyek (Daryl) secara resmi memilih **Opsi B** (Revisi SLO berbasis UX interkom drive-thru).
   - Angka target baru ditetapkan oleh Daryl berdasarkan kenyamanan pacing interkom drive-thru (misal: P50 $\le 1.8\text{ s}$ atau $\le 2.0\text{ s}$) sebelum pengoptimalan lebih lanjut.
   - PRD §4.5 dan PROJECT_PLAN §3.2 & §4.5 diperbarui secara formal untuk mencerminkan SLO baru.
