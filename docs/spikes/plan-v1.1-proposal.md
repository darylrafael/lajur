# Proposal Perubahan Dokumen PROJECT_PLAN.md (Menuju Versi 1.1)

**Dokumen:** `docs/spikes/plan-v1.1-proposal.md`  
**Tanggal Pengajuan:** 2026-10-15  
**Status:** Menunggu Persetujuan User [HUMAN APPROVAL PENDING]  
**Catatan Kepatuhan:** Sesuai Hard Rule 1 & 2, file `PROJECT_PLAN.md` TIDAK DIUBAH secara langsung. Perubahan ini diajukan sebagai diff proposal berdasarkan temuan verifikasi resmi pada `docs/spikes/vendor-facts-2026-10.md`.

---

## 1. Usulan Revisi pada Bagian §7.1 (Fakta Vendor)

### 1.1 Deepgram Nova-3
- **Teks Eksisting (v1.0):**
  > `Deepgram Nova-3 | Indonesia (id) didukung streaming; language=multi TIDAK mencakup Indonesia; keyterm didukung (maks 100); $0,0077/mnt; kredit $200`
- **Usulan Revisi (v1.1):**
  > `Deepgram Nova-3 | Indonesia (id) didukung streaming; parameter language=multi terverifikasi mendukung percampuran bahasa/code-switching ID–EN; keyterm didukung (maks 100); $0,0077/mnt; kredit uji coba $200.`
- **Rasional:** Dokumentasi resmi Deepgram telah memperluas model Nova-3 Multilingual untuk mencakup bahasa Indonesia dalam deteksi dan transkripsi multi-bahasa.

### 1.2 Soniox
- **Teks Eksisting (v1.0):**
  > `Soniox | Indonesia didukung; $0,002/mnt`
- **Usulan Revisi (v1.1):**
  > `Soniox | Indonesia didukung dengan native code-switching ID–EN; $2,00/1M audio tokens (~$0,002/mnt); TIDAK ADA KREDIT GRATIS untuk akun API baru (wajib pay-as-you-go).`
- **Rasional:** Kebijakan anti-abuse Soniox menghapus saldo trial $200. Pengembang harus mengisi saldo awal kartu kredit/debit secara mandiri.

### 1.3 Model Gemini (LLM)
- **Teks Eksisting (v1.0):**
  > `Gemini | gemini-2.0-flash sudah pensiun (1 Jun 2026); free tier: prompt dan output bisa dipakai Google untuk training... Nama model terbaru harus diverifikasi di docs resmi`
- **Usulan Revisi (v1.1):**
  > `Gemini | Model aktif: gemini-2.5-flash-lite ($0,10 in / $0,40 out per 1M token) dan gemini-2.5-flash ($0,30 in / $2,50 out per 1M token). Free tier memanfaatkan prompt untuk training AI. Tier berbayar (Cloud Billing tertaut) MENJAMIN data prompt/transkrip TIDAK DIPAKAI untuk training produk Google.`
- **Rasional:** Nama model dan klausul privasi enterprise telah terverifikasi secara hukum di dokumen resmi Google AI Studio Terms.

### 1.4 Frontend Hosting (Vercel vs Cloudflare Pages)
- **Teks Eksisting (v1.0, §7.2):**
  > `Frontend Vercel/Cloudflare Pages; worker di container (Railway/Fly/VPS Singapura)`
- **Usulan Revisi (v1.1):**
  > `Frontend Cloudflare Pages (Free Tier mendukung penggunaan komersial dan unlimited request); worker di container (Railway/Fly/VPS Singapura). Vercel Hobby dihindari karena restriksi non-komersial.`
- **Rasional:** Vercel Fair Use Terms melarang keras segala bentuk penggunaan komersial di Hobby Plan, sementara Cloudflare Pages mengizinkannya secara legal tanpa biaya.

---

## 2. Usulan Revisi pada Bagian §11.1 (Model Biaya & Kapasitas Sesi)

- **Teks Eksisting (v1.0):**
  > `Total variabel: ~$0,02 (Deepgram: ~$0,035; ElevenLabs TTS: ~$0,05)`
  > `Pembatas utama adalah kuota LiveKit Build (1.000 menit/bulan) -> ±330 sesi per bulan. Rencana: Mulai di LiveKit Cloud Build, pasang kuota harian (±10 sesi) dan batas sesi 2,5–3 menit.`
- **Usulan Revisi (v1.1):**
  > `Total variabel aktual: $0,0163 per sesi 3 menit (Soniox STT $0,006 + Gemini 2.5 Flash-Lite $0,00074 + Azure S0 TTS $0,0096). Varian Deepgram + GPT-4o-mini: $0,0338/sesi. Varian Gladia: $0,0478/sesi.`
  > `Kapasitas kuota LiveKit Cloud Build (1.000 menit/bulan) terverifikasi memiliki perilaku Hard Stop tanpa tagihan overage otomatis: 333 sesi/bulan pada batas 3 menit (11 sesi/hari) atau 400 sesi/bulan pada batas 2,5 menit (13 sesi/hari).`
- **Rasional:** Angka telah dikonfirmasi berdasarkan tarif aktual per 15 Oktober 2026.

---

## Tindakan yang Diperlukan:
Mohon tinjau usulan ini. Jika Anda menyetujuinya, saya akan memperbarui `PROJECT_PLAN.md` ke Versi 1.1 pada siklus sesi berikutnya.
