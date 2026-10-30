# Local Live-Mode Verification Check (Minggu 5c)
**Sisa Kuota ElevenLabs:** 1.576 karakter (read-only query API). Sisa kuota aman untuk ~24 turn uji coba.
1. Terminal 1 (Worker): `uv run python -m lajur_agent.worker dev` (atau `uv run python services/agent/src/lajur_agent/worker.py dev`)
2. Terminal 2 (Web PowerShell): `$env:LIVE_MODE_ENABLED="true"; npm run dev --prefix apps/web`
3. Terminal 2 (Web Bash): `LIVE_MODE_ENABLED=true npm run dev --prefix apps/web`
4. Akses peramban di `http://localhost:3000/?mode=live`, klik tombol *"Mulai Berbicara"*, izinkan akses mic.
5. Ucapkan satu pesanan uji: *"Pesan satu burger sapi spesial"*.
6. Amati transkrip parsial/final seketika di layar dan pembaruan keranjang belanja secara real-time.
7. Amati balasan suara bot; jika kuota habis, worker tetap memproses keranjang & transkrip.
8. Selesai sesi: matikan worker (Ctrl+C) dan kembalikan flag: `LIVE_MODE_ENABLED=false`.