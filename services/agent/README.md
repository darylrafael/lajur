# Services: Agent Worker

Direktori ini berisi agen worker Python berbasis `livekit-agents` yang mengorkestrasi pipeline suara:
- **VAD & Turn Detection**: Silero VAD + deteksi jeda semantik.
- **Cascade Pipeline**: Adapter STT streaming -> LLM intent parsing -> Adapter TTS streaming.
- **Guardrails**: Batas durasi sesi (3 menit), batas turn, batas item, anti-prompt injection.
- **Event Logging**: Pencatatan metrik latensi per tahap dan token/karakter ke log terstruktur.

*Status: Dibuat di Minggu 1 (Echo) & Minggu 4 (Tracer Bullet).*
