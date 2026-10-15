# Checklist Pendaftaran Akun & Hard Spend Cap [HUMAN ACTION REQUIRED]

**Dokumen:** `docs/spikes/account-setup-checklist.md`  
**Target:** Daryl (Solo Dev)  
**Tujuan:** Panduan langkah demi langkah untuk mendaftarkan akun vendor, mengonfigurasi batasan pengeluaran ketat (*hard cap / budget alert*), dan mencatat environment variable yang relevan.

> [!IMPORTANT]
> Sesuai Hard Rule 7, seluruh pembuatan akun, input metode pembayaran, penetapan plafon kartu kredit, dan generate API key adalah tugas khusus **[HUMAN]**. Agen dilarang meminta atau memegang kartu kredit asli.

---

## 1. Daftar Akun & Konfigurasi Batas Biaya

### 1. LiveKit Cloud
- **URL Pendaftaran:** [cloud.livekit.io](https://cloud.livekit.io/)
- **Plan yang Dipilih:** **Build Plan (Free / $0/mo)**
- **Batas / Guardrail:**
  - Build plan menerapkan *hard stop* otomatis pada 1.000 menit sesi agen per bulan.
  - Jangan tambahkan kartu kredit / jangan upgrade ke Ship Plan ($50/mo) kecuali sengaja ingin menambah kuota.
- **Nama Variabel Lingkungan (`.env`):**
  - `LIVEKIT_URL=` (wss://...)
  - `LIVEKIT_API_KEY=`
  - `LIVEKIT_API_SECRET=`

---

### 2. Deepgram
- **URL Pendaftaran:** [console.deepgram.com](https://console.deepgram.com/)
- **Plan yang Dipilih:** **Pay As You Go** (klaim kredit gratis $200 untuk pengguna baru).
- **Batas / Guardrail:**
  - Masuk ke menu **Billing & Settings**.
  - **Auto-Reload:** Matikan (*Disabled*) fitur auto-reload, atau atur ambang batas maksimal $10.
  - **Spending Limit / Alert:** Atur alert email jika penggunaan kredit melebihi $50.
- **Nama Variabel Lingkungan (`.env`):**
  - `DEEPGRAM_API_KEY=`

---

### 3. Soniox
- **URL Pendaftaran:** [soniox.com](https://soniox.com/)
- **Plan yang Dipilih:** **API Pay-As-You-Go**
- **Batas / Guardrail:**
  - Peringatan: Tidak ada free credit API. Isi saldo awal minimal (misal $5–$10).
  - Atur saldo maksimal kartu virtual/e-wallet untuk mencegah tagihan siluman.
- **Nama Variabel Lingkungan (`.env`):**
  - `SONIOX_API_KEY=`

---

### 4. Gladia
- **URL Pendaftaran:** [app.gladia.io](https://app.gladia.io/)
- **Plan yang Dipilih:** **Starter (Free Trial €50 Credits)**
- **Batas / Guardrail:**
  - Manfaatkan kredit trial €50.
  - Jangan aktifkan recurring subscription tanpa evaluasi hasil spike G1.
- **Nama Variabel Lingkungan (`.env`):**
  - `GLADIA_API_KEY=`

---

### 5. Microsoft Azure Cognitive Services (Speech / TTS)
- **URL Pendaftaran:** [portal.azure.com](https://portal.azure.com/)
- **Layanan yang Dibuat:** **Azure AI Speech Resource**
- **Plan yang Dipilih:** Buat resource dengan tier **F0 (Free)** terlebih dahulu untuk pengujian lokal (500.000 karakter/bulan). Jika butuh konkurensi, buat tier **S0 (Pay-As-You-Go)**.
- **Batas / Guardrail:**
  - Masuk ke **Cost Management + Billing** &rarr; **Budgets**.
  - Buat budget baru: Plafon maksimal **$10,00/bulan**.
  - Pasang alert email pada 50% ($5) dan 80% ($8).
- **Nama Variabel Lingkungan (`.env`):**
  - `AZURE_SPEECH_KEY=`
  - `AZURE_SPEECH_REGION=` (contoh: `southeastasia` atau `eastasia`)

---

### 6. Google AI Studio / Gemini API
- **URL Pendaftaran:** [aistudio.google.com](https://aistudio.google.com/)
- **Plan yang Dipilih:** Tautkan project ke **Google Cloud Billing Account** dengan tier berbayar (Pay-As-You-Go) untuk mengaktifkan klausul privasi (data prompt tidak dipakai training).
- **Batas / Guardrail:**
  - Masuk ke [Google Cloud Console Billing Budgets](https://console.cloud.google.com/billing/budgets).
  - Buat budget alert: **$10,00/bulan** dengan email notification pada threshold 50%, 80%, dan 100%.
- **Nama Variabel Lingkungan (`.env`):**
  - `GEMINI_API_KEY=`

---

### 7. Groq Console
- **URL Pendaftaran:** [console.groq.com](https://console.groq.com/)
- **Plan yang Dipilih:** **Free Developer Tier** (20 RPM, 2.000 RPD untuk Whisper)
- **Batas / Guardrail:**
  - Gunakan kuota gratis developer. Tidak perlu memasukkan kartu kredit untuk kebutuhan spike.
- **Nama Variabel Lingkungan (`.env`):**
  - `GROQ_API_KEY=`

---

### 8. Cloudflare (Turnstile & Pages)
- **URL Pendaftaran:** [dash.cloudflare.com](https://dash.cloudflare.com/)
- **Layanan:** 
  1. **Turnstile**: Buat widget baru untuk domain `localhost:3000` dan domain demo.
  2. **Pages**: Hubungkan repositori GitHub ke Cloudflare Pages (Free Plan).
- **Nama Variabel Lingkungan (`.env`):**
  - `NEXT_PUBLIC_CLOUDFLARE_TURNSTILE_SITE_KEY=`
  - `CLOUDFLARE_TURNSTILE_SECRET_KEY=`

---

### 9. Sentry (Monitoring)
- **URL Pendaftaran:** [sentry.io](https://sentry.io/)
- **Plan yang Dipilih:** **Developer Plan ($0/bulan)**
- **Batas / Guardrail:**
  - Otomatis hard-stop saat 5.000 error/bulan tercapai. Tidak ada tagihan siluman.
- **Nama Variabel Lingkungan (`.env`):**
  - `SENTRY_DSN=`

---

## 2. Ringkasan Pagu Anggaran Maksimal Bulanan
- Target pengeluaran gabungan vendor per bulan: **< $30,00**.
- Plafon kartu debit/virtual gabungan yang direkomendasikan: **Maksimal Rp500.000 (~$32)**.
