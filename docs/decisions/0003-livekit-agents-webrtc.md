# ADR-0003: Adopsi LiveKit Agents (WebRTC) sebagai Transport dan Orkestrator Suara

## Status
Proposed, pending vendor verification

## Konteks
Sistem voice assistant real-time dari browser memerlukan protokol transport audio latensi rendah dua arah (< 200ms transport budget) dan kerangka orkestrator yang mendukung interupsi suara (*barge-in*), manajemen koneksi WebRTC, serta *turn-detection*.
Terdapat beberapa opsi arsitektur:
1. Framework open-source WebRTC dengan worker terkelola (LiveKit Agents, Pipecat + Daily.co).
2. Platform API voice tertutup (Vapi, Retell AI).
3. Implementasi WebSockets mentah buatan sendiri (Custom WebSocket + MediaRecorder).

## Keputusan
Kami mengusulkan adopsi **LiveKit Cloud (Build Tier) dan framework `livekit-agents` (Python)**.
- Komunikasi audio klien-ke-server menggunakan WebRTC peer-to-peer/SFU dengan latensi minimal.
- Frontend React memanfaatkan pustaka `@livekit/components-react` untuk manajemen mikrofon, audio visualizer, dan data channel.
- Server worker menggunakan Python `livekit-agents` yang mengintegrasikan Silero VAD, sinkronisasi audio streaming, dan penjadwalan worker secara terdistribusi.
- Jika kuota cloud gratis habis, arsitektur LiveKit memungkinkan *self-hosting* server SFU pada VM sendiri tanpa mengubah kode agent.

## Alternatif yang Ditolak
- **Vapi / Retell AI**: Ditolak karena sifatnya *black-box*, biaya markup per menit yang mahal, dan minimnya kendali mendalam atas *cart state machine* deterministik.
- **Pipecat + Daily.co**: Alternatif yang sangat baik, namun komponen frontend LiveKit dan ekosistem worker Python-nya dinilai lebih matang dan memiliki opsi *self-host* SFU yang lebih teruji.
- **Custom WebSocket + AudioWorklet**: Ditolak karena waktu pengembangan solo (10-15 jam/minggu) akan habis untuk menangani kompleksitas transport WebRTC/ICE/Jitter buffering alih-alih fokus pada akurasi *code-switching*.

## Konsekuensi
- **Positif:**
  - Penanganan WebRTC, audio jitter, dan peredaman gema (echo cancellation) ditangani di level protokol WebRTC standar.
  - Dukungan native *barge-in* yang memotong output audio seketika saat mic pengguna mendeteksi suara.
  - Komponen UI frontend siap pakai.
- **Negatif / Mitigasi:**
  - Batasan kuota LiveKit Cloud Build (1.000 menit agent/bulan, maks 5 konkurensi). Mitigasi: Pasang durasi sesi 3 menit, kuota harian (~10 sesi/hari), dan siapkan panduan fallback *self-hosting* LiveKit Server di VM.
