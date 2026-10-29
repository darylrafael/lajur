# Local Live-Mode Verification Check (Minggu 5b)
**Sisa Kuota ElevenLabs:** 1.576 karakter tersisa dari batas 10.000 (terverifikasi via API read-only).
1. Terminal 1 (Jalankan Worker): `uv run python -m lajur_agent.worker dev`
2. Terminal 2 (Aktifkan Live Mode & Web): `$env:LIVE_MODE_ENABLED="true"; npm run dev --prefix apps/web`
3. Buka peramban di `http://localhost:3000/?mode=live`, klik *"Mulai Sesi Suara"*, dan izinkan akses mic.
4. Ucapkan satu pesanan singkat: *"Pesan burger sapi satu"*.
5. Verifikasi visual: transkrip parsial muncul seketika saat berbicara disusul transkrip final.
6. Verifikasi keranjang: lencana *"Keranjang Diperbarui"* menyala dan item burger masuk ke daftar pesanan.
7. Verifikasi asisten: visualizer bicara aktif, teks balasan muncul, dan suara bot terdengar.
8. Catatan evaluasi: amati apakah kemunculan transkrip instan meredam rasa canggung jeda respon audio bot.
