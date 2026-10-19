# ADR-0011: Pemilihan Vendor Text-to-Speech (TTS)

## Status
Proposed (OPEN)

## Konteks
Sistem voice ordering Lajur membutuhkan komponen Text-to-Speech (TTS) yang mampu menyuarakan respon kasir dalam bahasa Indonesia sehari-hari yang ramah, natural, dan fasih melafalkan istilah menu makanan bahasa Inggris (*code-switching*) serta nominal rupiah.

Pada Spike Minggu 2 dan G1b, ditetapkan **Hard Constraint**: pengembang tidak akan menggunakan layanan apa pun yang mewajibkan kartu pembayaran/kredit (*payment card*).

## Pernyataan Status & Penolakan Prototipe
> [!WARNING]
> **Edge-TTS adalah wrapper tidak resmi (*unofficial reverse-engineered wrapper*) terhadap layanan browser Microsoft Edge.**  
> Audio yang dihasilkan **BUKAN dari Azure Cognitive Services Speech API resmi**. Layanan ini tidak memiliki jaminan ketersediaan (SLA), sewaktu-waktu dapat diblokir/dibatasi oleh Microsoft, dan tidak memiliki hak lisensi komersial.  
> **Status Edge-TTS:** **Prototipe saja, TIDAK DISETUJUI UNTUK PRODUK (prototype only, not approved for product).**

## Temuan Analisis Sensitivitas Alokasi Latensi TTS (G1b)
Berdasarkan pengukuran empiris 30 skenario pada fase G1b:
- Kombinasi **Deepgram Nova-3 Stream (1.820 ms)** + **Gemini First Sentence (841 ms)** = **2.661 ms**.  
  Sisa alokasi untuk TTS agar lolos batas $\le 1.200\text{ ms}$: **-1.461 ms (Defisit/Mustahil)**.
- Kombinasi **Groq Whisper (+500ms VAD = 990 ms)** + **Gemini First Sentence (841 ms)** = **1.831 ms**.  
  Sisa alokasi untuk TTS agar lolos batas $\le 1.200\text{ ms}$: **-631 ms (Defisit/Mustahil)**.

*Kesimpulan Matematis:* Bahkan jika tersedia mesin TTS instan dengan TTFB 0 ms, sistem cascade tetap tidak dapat mencapai batas latensi turn 1.200 ms karena akumulasi STT dan LLM saja sudah melampaui batas tersebut.

## Keputusan
Status pemilihan vendor TTS ditetapkan sebagai **OPEN**.

### Syarat Penutupan Keputusan (Requirements to Close):
Keputusan vendor TTS baru dapat dikunci dan ditutup apabila salah satu kondisi berikut terpenuhi:
1. **Integrasi Resmi Card-Free:** Disediakannya kredensial/kunci API resmi untuk layanan berlisensi tanpa kartu (misal kredensial Azure for Students, atau provider TTS resmi card-free yang terverifikasi); **ATAU**
2. **Keputusan Tertulis Pengembang:** Keputusan eksplisit tertulis dari Daryl yang menyatakan menerima secara sadar risiko teknis dan hukum dari penggunaan wrapper tidak resmi (*Edge-TTS*) untuk demo publik.

*Keputusan akhir sepenuhnya berada di tangan pengembang (Daryl); agen pengembang tidak menentukan pilihan ini.*

## Alternatif yang Terbuka & Dikeluarkan
- **Azure Cognitive Services Speech SDK Resmi:** Memerlukan kartu kredit pada akun standar (`excluded: card required`), kecuali jika menggunakan akun Azure for Students (kunci belum tersedia di `.env`).
- **Cartesia Sonic 3.x:** Dikeluarkan dari pertimbangan (`excluded: card required`) karena mewajibkan kartu kredit untuk akses API.
- **ElevenLabs Free Tier:** Menyediakan kuota bulanan 10k karakter gratis tanpa kartu, namun lisensi free tier mewajibkan atribusi dan bersifat non-komersial.

## Konsekuensi
- Arsitektur adapter (`TTSProvider` di `services/agent/src/lajur_agent/adapters/base.py`) tetap terisolasi sehingga provider resmi dapat langsung dihubungkan begitu kunci API tersedia tanpa mengubah kode agen lainnya.
