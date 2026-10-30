# Barge-in and Acoustic Echo Cancellation (AEC) Architecture

**Dokumen:** `docs/design/barge-in-and-aec.md`  
**Milestone:** Minggu 6 — Robustness & Pipeline Hardening  
**Status:** IMPLEMENTED & DOCUMENTED  
**Terkait:** Risk R15 (Echo Bleed False Barge-in), Web Protocol v1 (`bot_speaking_start`, `bot_speaking_end`)

---

## 1. Arsitektur Full-Duplex & Barge-in

Pada sistem pemesanan suara *drive-thru*, pengguna dapat memotong ucapan bot kasir (*barge-in*) kapan saja, misalnya ketika sudah mengetahui pesanan tanpa menunggu bot selesai membacakan menu.

### 1.1 Komponen Barge-in
1. **`BargeInController` (`services/agent/src/lajur_agent/barge_in.py`):**
   - Melacak status apakah bot sedang mengeluarkan suara (`is_bot_speaking`) atau sedang dalam proses generasi (`is_generation_in_flight`).
   - Menyediakan `playback_cancel_event` (`asyncio.Event`) yang dicek di setiap iterasi pengiriman frame audio PCM (20 ms chunk).
   - Membatalkan *in-flight tasks* secara seketika saat interupsi terkonfirmasi.
   - Menghentikan pengaliran audio ke LiveKit AudioTrack dan mengirimkan event protokol `bot_speaking_end` ke klien.
2. **Echo-Bleed Guard (Mitigasi Risiko R15):**
   - **Masalah:** Suara bot dari loudspeaker perangkat pengguna dapat memantul kembali ke mikrofon perangkat (*acoustic echo*). Jika sistem langsung memotong bot pada frame audio pertama (20 ms), pantulan akustik singkat (*echo blip*) atau desah napas akan menyebabkan bot terpotong sendiri secara keliru (*false barge-in loop*).
   - **Solusi:** Guard durasi bicara minimum (`min_speech_duration_ms = 150.0 ms`). Energi suara yang berlangsung kurang dari 150 ms diabaikan sebagai transient echo/noise. Hanya suara yang bertahan $\ge 150$ ms yang memicu pembatalan playback bot.

---

## 2. Kemampuan & Batasan Acoustic Echo Cancellation (AEC) Browser

### 2.1 Yang Dicakup oleh Browser AEC
Standar W3C *Media Capture and Streams* ([W3C Recommendation, https://www.w3.org/TR/mediacapture-streams/](https://www.w3.org/TR/mediacapture-streams/), diakses Oktober 2026) dan spesifikasi WebRTC mendefinisikan constrain `echoCancellation: true` pada `navigator.mediaDevices.getUserMedia`:
- **Linear Adaptive Filtering:** Modul AEC bawaan browser (misalnya WebRTC AEC3 di Chromium dan CoreAudio AEC di Safari) memodelkan jalur transfer akustik linier antara speaker output browser dan mikrofon input.
- **Fixed Geometry & Moderate Volume:** Bekerja efektif pada laptop dan desktop di mana jarak dan sudut speaker-to-mic bersifat tetap, serta volume berada pada rentang linier (tidak terjadi saturasi membran speaker).
- **Residual Echo Suppression:** Menggunakan comfort noise generator (CNG) dan non-linear processor (NLP) untuk meredam sisa gema yang lolos dari filter adaptif.

### 2.2 Yang TIDAK Dicakup oleh Browser AEC
- **Saturasi dan Distorsi Non-Linier Loudspeaker:** Pada volume tinggi di speaker kecil (misal laptop tipis atau smartphone), membran speaker mengalami *hard clipping* dan distorsi harmonik non-linier. Model linier AEC browser gagal memprediksi harmonik ini, sehingga suara bocor (*bleed*) ke kanal mic.
- **Desinkronisasi Estimator Delay Akibat Bluetooth / OS Jitter:** Headset atau speaker nirkabel Bluetooth (profil A2DP / HFP) memiliki latensi dinamis dan *clock drift*. Jika estimator delay WebRTC kehilangan sinkronisasi (terjadi buffer underrun/overrun), AEC browser gagal total hingga filter melakukan konvergensi ulang (membutuhkan waktu 500–2000 ms).
- **Resonansi Bodi Perangkat (*Chassis Vibration*):** Getaran fisik casing smartphone atau laptop pada frekuensi rendah (bass) ditransmisikan langsung secara mekanis ke mikrofon internal tanpa melalui udara, melewati filter akustik.

---

## 3. Aspek yang Belum Teruji pada Ponsel Fisik (*Untested on Real Mobile Hardware*)

1. **Bypass Hardware DSP oleh Web Audio API:**
   - Pada iOS Safari (WebKit) dan Android Chrome, ketika mikrofon dihubungkan ke Web Audio API node (`AudioContext.createMediaStreamSource()`), beberapa vendor OS secara diam-diam mematikan hardware DSP AEC bawaan chipset (misal Qualcomm Fluence atau Apple Audio DSP) dan beralih ke software AEC WebRTC yang jauh lebih lemah dan memiliki latensi lebih tinggi.
2. **Akustik Helm & Kaca Mobil Terbuka:**
   - Penggunaan helm tertutup (*full-face*) memantulkan suara dari speaker telinga langsung ke mikrofon dagu dengan amplitudo sangat besar. Lingkungan kabin mobil dengan jendela terbuka menghasilkan pantulan turbulensi udara yang belum pernah diuji secara fisik di lapangan.
3. **Variasi Latensi AudioTrack Mobile:**
   - *Buffer size* audio pada perangkat Android kelas menengah ke bawah (*entry-level*) bervariasi antara 10 ms hingga 96 ms, mempengaruhi *stop latency* aktual yang dirasakan telinga manusia.

> [!NOTE]
> Seluruh skenario barge-in dan proteksi echo-bleed pada Minggu 6 diuji menggunakan simulasi frame audio deterministik pada lingkungan worker. Pengujian akustik fisik pada perangkat nyata tetap tercatat sebagai tugas uji manusia (*pending real-device testing*).
