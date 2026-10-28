# Pre-Registered Measurement Protocol: Gate G1-v2 (Minggu 4c)

**Document:** `docs/gates/G1-v2-protocol.md`  
**Milestone:** Minggu 4c — Pengukuran Validasi Gerbang G1-v2 Pasca Perbaikan Overhead Implementasi  
**Date:** 2026-10-25  
**Author:** Daryl (Solo Dev) & Claude (Owner-delegated defaults, owner may overrule)  
**Status:** PRE-REGISTERED PROTOCOL — LOCKED BEFORE CODE CHANGES  

---

## 1. Status Keputusan & Batasan Operasional (*Owner-Delegated Defaults*)

Keputusan berikut diusulkan oleh asisten (Claude) dan didelegasikan oleh pemilik proyek (Daryl) sebagai *owner-delegated defaults* (pemilik berhak membatalkan/mengubah):
1. **Opsi B (Fix Implementation Overhead & Re-measure Once):** Memperbaiki overhead implementasi dan mengukur ulang tepat **SATU KALI (*single run, no tuning after seeing results*)** dengan ambang batas yang SAMA PERSIS. Setelah pengukuran ini selesai, apa pun hasilnya, proyek berlanjut ke Minggu 5 dan angka v2 ini menjadi figur latensi yang dipublikasikan. Tidak ada putaran pengukuran latensi lanjutan sebelum Minggu 8 kecuali diinstruksikan oleh pemilik.
2. **Konfigurasi Utama (*Primary Configuration*):** Menggunakan balasan templat deterministik (*deterministic template replies*, tanpa pemanggilan LLM kedua). Seluruh koneksi dipanaskan (*pre-warmed*) di awal sesi saat ucapan pembuka (*greeting*). Mode balasan verbalisasi LLM **TIDAK DIUKUR ULANG** (*not re-measured*).
3. **Konfigurasi Endpointing:** Parameter `endpointing=500` ms tetap dipertahankan pada *headline run* (tidak diturunkan ke 300 ms agar stabilitas deteksi hening tetap konsisten dengan Minggu 4).
4. **Lokasi Worker:** Worker tetap berjalan di laptop dev di Indonesia (tanpa deployment cloud). Ini secara sadar dicatat sebagai **penyiapan pesimistik (*pessimistic setup*)** karena jarak fisik jaringan ke API vendor adalah ~180–240 ms.
5. **Cadangan Kuota ElevenLabs:** Menyimpan cadangan minimal **600 karakter ElevenLabs** khusus untuk pengujian perangkat fisik nyata mendatang. Kuota saat ini adalah 2.577 karakter, sehingga batas pengeluaran maksimal adalah $2.577 - 600 = \mathbf{1.977\text{ karakter}}$.
6. **Vonis Minggu 4 Tetap Berlaku:** Kegagalan Minggu 4 pada kedua ambang batas tetap tercatat permanen di [`docs/gates/G1-minggu4-results.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/gates/G1-minggu4-results.md). Protokol v2 ini menghasilkan catatan baru yang terpisah, bukan menghapus atau menggantikan hasil lama.

---

## 2. Kriteria & Ambang Batas Evaluasi (SAMA PERSIS DENGAN PROTOKOL G1 AWAL)

Ambang batas pengujian tidak diubah:
1. **Target Orisinal (PRD §4.5):**
   $$P50 \le 1.200\text{ ms}\quad (1,2\text{ detik})$$
2. **Batas Toleransi Pemilik Proyek (*Owner Fallback*, ADR-0013 Opsi B):**
   $$P50 \le 1.800\text{ ms}\quad\text{DAN}\quad P95 \le 3.000\text{ ms}$$
   *Diukur dari saat pengguna selesai berbicara ($T_{\text{speech\_end}}$) hingga frame audio pertama balasan terdengar di telinga klien ($T_{\text{first\_audio}}$).*

---

## 3. Desain Pengujian & Aturan Metrik Utama

- **Jumlah Giliran:** Minimal **30 giliran percakapan (*turns*)** mewakili ragam pesanan (simple, combo/quantity, modifier, correction/undo).
- **Metrik Utama (*Primary Metric*):** Dihitung terhadap **SELURUH GILIRAN (*ALL TURNS*)** termasuk giliran pertama dari setiap sesi. Pre-warming selama greeting diperlakukan sebagai perilaku produk alami (*product behavior*). Latensi giliran pertama dilaporkan secara terpisah sebagai perbandingan transparansi.
- **Aturan Eksekusi Tunggal (*Single Run Rule*):** Pengukuran dijalankan satu kali penuh. Dilarang melakukan penyesuaian parameter (*tuning*) atau pengulangan setelah melihat hasil evaluasi.
- **Estimasi Statistik:** Semua metrik (P50, P95, Mean) dihitung dengan **10.000 sampel bootstrap resampling** untuk menghasilkan selang kepercayaan 95% persentil.

---

## 4. Metodologi Penentuan Titik Referensi ($T_{\text{speech\_end}}$ dan $T_{\text{first\_audio}}$)

1. **Speech-End Reference ($T_{\text{speech\_end}}$):**
   - Klien sintetis lokal memutar file audio ucapan ke WebRTC audio track.
   - Timestamp `t_speech_end` dicatat secara presisi menggunakan `time.monotonic()` tepat ketika frame audio PCM terakhir diserahkan ke WebRTC `AudioSource`.
   - Tidak ada estimasi mundur atau tebakan berbasis transkrip teks.
2. **First Audio Receipt ($T_{\text{first\_audio}}$):**
   - Klien memantau track audio WebRTC yang dikirimkan oleh worker agen.
   - Timestamp `t_first_audio` dicatat saat frame audio masuk pertama kali dan energi sinyalnya melampaui ambang batas hening ($\text{rms} > 300,0$).
3. **Total Latensi Terukur:**
   $$\Delta T = T_{\text{first\_audio}} - T_{\text{speech\_end}}$$

---

## 5. Rencana Anggaran Karakter ElevenLabs

- Sisa Kuota Saat Ini: **2.577 karakter**
- Cadangan Wajib Perangkat Fisik: **600 karakter**
- Batas Maksimal Kuota Terpakai: **1.977 karakter**
- Strategi: **Templat Balasan Ringkas (*Terse Template Replies*)**
  - Panjang rata-rata balasan: $\approx 22$ karakter per turn (misal: `"1 Burger dicatat."`).
  - Total konsumsi untuk 30 giliran: $30 \times 22 \approx \mathbf{660\text{ karakter}}$.
  - Sisa kuota pasca-uji: $2.577 - 660 \approx \mathbf{1.917\text{ karakter}}$ (sangat aman di atas cadangan 600 karakter).
  - *Sebelum panggilan TTS pertama dimulai, script wajib memverifikasi kuota via API header ElevenLabs. Jika kuota tidak mencukupi, script STOP dan bertanya kepada pemilik.*

---

## 6. Daftar Perubahan Implementasi yang Diuji (Hanya Ini, Tidak Ada yang Lain)

1. **Reuse HTTP Session per Worker:** Mempertahankan satu instance `aiohttp.ClientSession` bersama dengan *TCP connection pooling* dan *keep-alive* aktif untuk seluruh panggilan REST ke Groq dan ElevenLabs (mengeliminasi 3x negosiasi handshake per giliran).
2. **Single Persistent Deepgram WebSocket Connection:** Mempertahankan satu koneksi WebSocket streaming Deepgram terbuka sepanjang sesi dengan mekanisme keep-alive dan penanganan rekoneksi otomatis jika terputus.
3. **Pre-Warming Koneksi saat Greeting:** Membuka dan menghangatkan koneksi ke LiveKit, Deepgram, dan HTTP API saat pemutaran salam pembuka (*greeting*). Waktu pre-warming dicatat dalam metrik terpisah (`t_prewarm_ms`).
4. **Non-Blocking Telemetry:** Penulisan telemetri SQLite dan pembacaan token dipindahkan ke antrean asinkron (*async queue*) dengan *background worker*, mengeliminasi seluruh operasi I/O sinkron dari jalur kritis audio.
5. **Penambahan Telemetri Tahap yang Hilang:**
   - Timestamp partial transkrip pertama STT (`t_stt_first_partial_ms`).
   - Waktu koneksi/handshake (`t_connect_ms`).
   - Timestamp saat worker agen mem-publish frame audio pertama (`t_agent_publish_ms`) vs saat klien menerima frame tersebut (`t_first_audio_frame_ms`).
6. **Invarian Arsitektur:** Cart State Machine ([`packages/cart`](file:///c:/Users/Lenovo/Downloads/drivethru/packages/cart)) dan Intent Parser Contract tetap **TIDAK BERUBAH** sedikit pun.
