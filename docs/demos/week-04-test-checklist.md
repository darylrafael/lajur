# Checklist Uji Coba Suara Perangkat Fisik (Minggu 4: Tracer Bullet)

**Dokumen:** `docs/demos/week-04-test-checklist.md`  
**Milestone:** Minggu 4 — Voice Pipeline Tracer Bullet  
**Target Penguji:** Daryl (Pemilik Proyek / Solo Dev)  
**Lingkungan Uji:** Laptop Pengembang & Ponsel Pribadi (Jaringan Seluler 4G/5G, non-Wi-Fi)  
**Tujuan:** Memvalidasi pengalaman pemesanan suara nyata dari ujung ke ujung (*end-to-end voice ordering*) pada interkoneksi WebRTC langsung.

---

## 1. Prasyarat & Persiapan Lingkungan

Pastikan variabel lingkungan pada berkas `.env` di direktori utama telah terisi:
- `LIVEKIT_URL` (contoh: `wss://lajur-6xsjb7dn.livekit.cloud`)
- `LIVEKIT_API_KEY` dan `LIVEKIT_API_SECRET`
- `DEEPGRAM_API_KEY` (Streaming STT Nova-3)
- `GROQ_API_KEY` (Intent Parser Qwen-27b)
- `ELEVENLABS_API_KEY` (Streaming TTS Flash v2.5)

### Menjalankan Worker Agen di Laptop:
Buka terminal PowerShell pada laptop Anda dan jalankan perintah:
```powershell
uv run python services/agent/src/lajur_agent/worker.py dev
```
*Tunggu hingga terminal menampilkan log: `Lajur Voice Ordering Agent is ready and listening...`.*

### Membuka Klien di Perangkat Fisik (Laptop & Ponsel):
1. **Di Laptop:** Buka peramban Google Chrome dan akses LiveKit Agents Playground:  
   👉 `https://agents-playground.livekit.io/`
2. **Di Ponsel (Wajib via Jaringan Seluler / Data 4G/5G):** Matikan Wi-Fi ponsel, aktifkan data seluler, lalu buka tautan Playground yang sama di peramban seluler (Safari di iPhone atau Chrome di Android).
3. Sambungkan ke room:
   - Masukkan `LiveKit Cloud URL`, `API Key`, dan `API Secret` proyek Anda.
   - Tetapkan Room Name (misal: `lajur-demo-01`).
   - Tekan **Connect** dan izinkan akses mikrofon peramban.

---

## 2. Naskah Pengujian 3 Giliran (*Exact Spoken Script*)

Ucapkan kalimat berikut secara alami (seperti berbicara di depan speaker drive-thru):

### 🗣️ Giliran 1: Memesan Menu Utama & Sampingan
> *"Halo kak, saya mau pesan burger sapi keju satu sama kentang goreng satu."*
- **Yang Harus Diamati di Layar:**
  - Transkrip ucapan Anda muncul secara langsung saat berbicara.
  - Panel keranjang terupdate menampilkan:  
    1. `1x Burger Sapi Keju` (Rp28.000)  
    2. `1x Kentang Goreng` (Rp16.000)  
    Total: **Rp44.000**
- **Yang Harus Didengar di Audio:**  
  Kasir bot menyapa ramah dan mengonfirmasi penambahan item (misal: *"Baik kak, satu Burger Sapi Keju dan satu Kentang Goreng sudah masuk keranjang. Mau ukuran apa untuk kentangnya?"*).

---

### 🗣️ Giliran 2: Menambahkan Modifikasi & Ukuran
> *"Burgernya tambah extra cheese, kentangnya yang large ya."*
- **Yang Harus Diamati di Layar:**
  - Item kentang goreng berubah menjadi ukuran `Large` (Rp22.000).
  - Burger sapi keju mendapatkan modifier `Extra Cheese` (+Rp5.000).
  - Total keranjang terupdate menjadi **Rp55.000**.
- **Yang Harus Didengar di Audio:**  
  Kasir bot mengonfirmasi penyesuaian ukuran dan keju ekstra, lalu menanyakan apakah pesanan sudah lengkap.

---

### 🗣️ Giliran 3: Mengonfirmasi & Menyelesaikan Pesanan
> *"Sudah itu aja, konfirmasi pesanannya."*
- **Yang Harus Diamati di Layar:**
  - Status keranjang berpindah dari `ordering` menjadi `done` / `confirming`.
  - Keranjang terkunci, menampilkan ringkasan final.
- **Yang Harus Didengar di Audio:**  
  Kasir bot mengonfirmasi total akhir Rp55.000 dan mengarahkan kendaraan ke loket berikutnya (misal: *"Total belanja kakak lima puluh lima ribu rupiah. Silakan maju ke loket pembayaran ya kak, terima kasih!"*).

---

## 3. Format Pencatatan Hasil Uji (*Observation Form*)

Salin bagian ini dan isi hasil pengamatan Anda:

| Aspek Evaluasi | Pengujian Laptop (Wi-Fi/LAN) | Pengujian Ponsel (Data Seluler 4G/5G) | Catatan / Temuan |
| :--- | :--- | :--- | :--- |
| **Persepsi Jeda Waktu (*Perceived Latency*)** | [ ] Instan (< 1s)<br>[ ] Ada jeda wajar (1-2s)<br>[ ] Terasa lama (> 3s) | [ ] Instan (< 1s)<br>[ ] Ada jeda wajar (1-2s)<br>[ ] Terasa lama (> 3s) | *(Apakah jeda terasa seperti kasir nyata sedang mencatat?)* |
| **Kualitas & Kelancaran Audio** | [ ] Jernih & mulus<br>[ ] Ada patah-patah/glitch<br>[ ] Suara terputus | [ ] Jernih & mulus<br>[ ] Ada patah-patah/glitch<br>[ ] Suara terputus | *(Evaluasi stabilitas buffer WebRTC saat sinyal seluler berfluktuasi)* |
| **Kebenaran Transkrip & Keranjang** | [ ] 100% Sesuai<br>[ ] Ada salah dengar/item | [ ] 100% Sesuai<br>[ ] Ada salah dengar/item | *(Periksa item, modifier keju, dan ukuran large)* |
| **Kenyamanan Pacing Dialog** | [ ] Nyaman alami<br>[ ] Bot memotong ucapan<br>[ ] Terlalu kaku | [ ] Nyaman alami<br>[ ] Bot memotong ucapan<br>[ ] Terlalu kaku | *(Apakah endpointing 300ms cukup atau terlalu cepat memotong?)* |

---

## 4. Prosedur Hentikan Darurat (*Emergency Stop / Kill Switch*)

Jika terjadi kendala (misal: loop audio, halusinasi berulang, atau kelebihan token):
1. **Cara Utama (Terminal Laptop):**  
   Tekan kombinasi tombol **`Ctrl + C`** pada terminal PowerShell yang menjalankan `worker.py`. Proses akan mati seketika (*graceful shutdown*).
2. **Cara Kill Switch (Variabel Lingkungan):**  
   Set variabel lingkungan `KILL_SWITCH=1` pada berkas `.env` dan simpan. Worker secara otomatis menolak memproses pesanan baru dan mengalihkan status ke `handoff`.
