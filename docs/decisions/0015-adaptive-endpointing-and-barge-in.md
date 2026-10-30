# ADR-0015: Turn Detection Adaptif, Barge-in, dan Mitigasi Echo-Bleed

## Status
Proposed (2026-10-30)

## Konteks
Pada Minggu 4 dan Gerbang G1, sistem voice pipeline menggunakan baseline Deepgram Nova-3 static endpointing 300 ms. Pada pengujian skenario ragu (*hesitation*), jeda hening sesaat di tengah pemikiran (misal: *"ayam goreng satu sama..."* lalu jeda 400 ms) menyebabkan STT memotong ucapan sebelum pengguna menyelesaikan order (*false cutoff* rate mendekati 100%).

Di sisi lain, untuk mewujudkan interaksi percakapan alami (*full-duplex*), pengguna harus dapat memotong balasan bot kasir kapan saja (*barge-in*). Namun, suara bot dari loudspeaker perangkat pengguna berisiko bocor kembali ke mikrofon (*acoustic echo bleed*, Risiko R15). Jika barge-in dipicu tanpa filter durasi energi suara, pantulan suara singkat atau desah napas akan menyebabkan bot terpotong secara keliru (*false barge-in*).

---

## Keputusan

Sistem menerapkan arsitektur ketahanan dialog Minggu 6:

1. **Turn Detection & Adaptive Endpointing (`services/agent/src/lajur_agent/turn_detection.py`):**
   - **Baseline Deepgram Endpointing:** Tetap dipertahankan pada 300 ms (tidak mengubah konfigurasi G1).
   - **Heuristik Partikel Gantung:** Menganalisis token terakhir pada transkrip sementara (*partial/speech_final*). Jika transkrip berakhir dengan partikel ragu (*fillers*: "anu", "sebentar", "apa ya"), konjungsi gantung ("sama", "dan", "terus"), atau kata kerja gantung ("mau", "pesan"), sistem memberikan perpanjangan waktu tunggu terikat (*bounded extension window*) sebesar +500 ms (dikonfigurasi via `HESITATION_EXTENSION_MS`).
   - **Invarian Latensi Kalimat Bersih:** Pada kalimat lengkap tanpa partikel ragu (misal: "pesan burger sapi satu"), turn langsung difinalisasi seketika tanpa penundaan tambahan (tambahan latensi = 0,0 ms).
   - **Interupsi Pembicaraan Lanjutan:** Jika pengguna melanjutkan bicara saat jendela ekstensi sedang berjalan, timer ekstensi dibatalkan dan aliran suara diserap mulus.

2. **Barge-in Controller & Echo-Bleed Guard (`services/agent/src/lajur_agent/barge_in.py`):**
   - **Pembatalan Output Instan:** Menggunakan `playback_cancel_event` (`asyncio.Event`) yang dipantau pada setiap pengiriman frame PCM 20 ms. Saat barge-in terpicu, pengaliran audio ke LiveKit AudioSource dihentikan seketika dan event `bot_speaking_end` dikirimkan ke UI.
   - **Pembatalan In-Flight Tasks:** Seluruh tugas latar belakang (LLM verbalizer/TTS synthesis) dibatalkan secara elegan saat interupsi terjadi.
   - **Echo-Bleed Guard (R15):** Mengharuskan energi suara terdeteksi bertahan minimum $\ge 150$ ms (`BARGE_IN_MIN_SPEECH_DURATION_MS`) sebelum interupsi dikonfirmasi. Lonjakan akustik singkat $< 150$ ms (pantulan speaker atau noise spike) diabaikan sehingga bot tidak terpotong sendiri.

3. **Konsistensi State Keranjang:**
   - Karena mutasi keranjang bersifat murni dan deterministik melalui `packages/cart` State Machine, pembatalan turn di tengah jalan tidak meninggalkan *half-applied intents* atau merusak konsistensi keranjang.

---

## Konsekuensi

### Positif
- Menghilangkan *false cutoff* pada jeda 300 ms dari 100% menjadi 0,0%.
- Memberikan pengalaman pengguna yang responsif (*stop latency* interupsi bot < 1 ms secara terukur pada pengujian otomatis).
- Nol latensi tambahan pada kalimat bersih (terukur 0,10 ms, 95% CI: [0,03, 0,23] ms).
- Nol *false barge-in* terhadap pantulan akustik singkat di bawah 150 ms.

### Keterbatasan
- Pengujian audio sejauh ini menggunakan audio sintetis dan fakes terisolasi. Kinerja filter akustik fisik pada perangkat ponsel nyata tetap memerlukan verifikasi lapangan oleh pemilik proyek (*pending real-device verification*).
