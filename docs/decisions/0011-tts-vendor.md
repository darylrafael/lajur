# ADR-0011: Pemilihan Vendor Text-to-Speech (TTS)

## Status
Open

## Konteks
Sistem voice ordering Lajur membutuhkan komponen Text-to-Speech (TTS) yang mampu menyuarakan respon kasir dalam bahasa Indonesia sehari-hari yang ramah, natural, dan fasih melafalkan istilah menu makanan bahasa Inggris (*code-switching*) serta nominal rupiah.

Pada Spike Minggu 2 dan G1b, ditetapkan **Hard Constraint**: pengembang tidak akan menggunakan layanan apa pun yang mewajibkan kartu pembayaran/kredit (*payment card*).

## Pernyataan Status & Penolakan Prototipe
> [!WARNING]
> **Edge-TTS adalah wrapper tidak resmi (*unofficial reverse-engineered wrapper*) terhadap layanan browser Microsoft Edge.**  
> Audio yang dihasilkan **BUKAN dari Azure Cognitive Services Speech API resmi**. Layanan ini tidak memiliki jaminan ketersediaan (SLA), sewaktu-waktu dapat diblokir/dibatasi oleh Microsoft, dan tidak memiliki hak lisensi komersial.  
> **Status Edge-TTS:** **Prototipe saja, TIDAK DISETUJUI UNTUK PRODUK (prototype only, not approved for product).**

## Temuan Analisis Sensitivitas Alokasi Latensi TTS (G1b & G1f)
Berdasarkan pengukuran empiris 30 skenario pada fase G1b dan addendum G1f:
- Kombinasi **Deepgram Nova-3 Stream (524 ms)** + **Gemini First Sentence (841 ms)** = **1.365 ms**. Sisa alokasi untuk TTS: defisit -165 ms.
- Kombinasi **Deepgram Nova-3 Stream (524 ms)** + **Groq Qwen-27b Non-Reasoning (258–419 ms)** = **782–943 ms**. Sisa alokasi untuk TTS: 257–418 ms.
- **ElevenLabs Free Tier (`eleven_flash_v2_5`):** TTFB terukur P50 = **126.8 ms** (P95: 157.4 ms). Namun terikat ketentuan gratis:
  1. *Non-komersial mutlak* (Bagian 1(c) ToS): hanya untuk penggunaan personal/portofolio non-komersial.
  2. *Wajib atribusi:* wajib mencantumkan "elevenlabs.io" atau "11.ai".
  3. *Pelatihan data:* input teks default digunakan untuk melatih model ElevenLabs (dapat di-opt out).
  4. *Batas kuota:* 10.000 karakter/bulan.

*Kesimpulan:* ElevenLabs Free Tier tidak cocok untuk deployment komersial nyata.

## Keputusan Pemilik Proyek (Owner Decision - Minggu 2g)
1. **Status Pemilihan Vendor TTS Komersial:** Tetap **OPEN** (terbuka hingga sebelum Minggu 9 atau saat tersedianya provider berlisensi komersial card-free).
2. **Adopsi Bersyarat untuk Demo Portofolio:** Pemilik proyek (Daryl) menyetujui penggunaan **ElevenLabs Free Tier secara kondisional khusus untuk demonstrasi portofolio non-komersial saja**, dengan kewajiban menampilkan atribusi publik ("elevenlabs.io" / "11.ai") dan disclaimer non-komersial secara eksplisit pada antarmuka web.
3. **Investigasi Alternatif Terbuka:** Opsi Web Speech API (Browser Speech Synthesis) dan provider card-free lainnya tetap terbuka untuk diinvestigasi sebelum peluncuran produksi.

## Alternatif yang Terbuka & Dikeluarkan
- **ElevenLabs Free Tier:** Diterima bersyarat untuk demo/portofolio non-komersial; ditolak untuk komersial.
- **Azure Cognitive Services Speech SDK Resmi:** Memerlukan kartu kredit pada akun standar (`excluded: card required`), kecuali jika menggunakan akun Azure for Students.
- **Cartesia Sonic 3.x & Soniox:** Dikeluarkan dari pertimbangan (`excluded: card required`) karena mewajibkan kartu kredit untuk akses API.
- **Edge-TTS (Wrapper Browser):** Ditolak untuk produk (`prototype only, not approved for product`).
- **Web Speech API / Browser Synthesis:** Opsi fallback bebas biaya dan bebas server yang akan diinvestigasi lebih lanjut.

## Konsekuensi
- Arsitektur adapter (`TTSProvider` di `services/agent/src/lajur_agent/adapters/base.py`) tetap terisolasi sehingga switching provider antara ElevenLabs (demo) dan provider produksi resmi dapat dilakukan tanpa mengubah logika agen.
- Tampilan antarmuka web (`apps/web`) wajib memuat teks atribusi ElevenLabs selama menggunakan tier gratis.

