# ADR-0011: Pemilihan Vendor Text-to-Speech (TTS)

## Status
Proposed (OPEN)

## Konteks
Sistem voice ordering Lajur membutuhkan komponen Text-to-Speech (TTS) yang mampu menyuarakan respon kasir dalam bahasa Indonesia sehari-hari yang ramah, natural, dan fasih melafalkan istilah menu makanan bahasa Inggris (*code-switching*) serta nominal rupiah.

Pada Spike Minggu 2, dilakukan eksplorasi awal menggunakan alat bantu lokal:
- **Edge-TTS (`id-ID-GadisNeural` & `id-ID-ArdiNeural`):** Menghasilkan sintesis audio dengan RTF 0.44x, kualitas vokal yang alami, dan latensi TTFB antara 1,406 ms (Tier 1 pendek) hingga 2,636 ms (Tier 3 panjang).

## Pernyataan Status & Penolakan Prototipe
> [!WARNING]
> **Edge-TTS adalah wrapper tidak resmi (*unofficial reverse-engineered wrapper*) terhadap layanan browser Microsoft Edge.**  
> Audio yang dihasilkan **BUKAN dari Azure Cognitive Services Speech API resmi**. Layanan ini tidak memiliki jaminan ketersediaan (SLA), sewaktu-waktu dapat diblokir/dibatasi oleh Microsoft, dan tidak memiliki hak lisensi komersial.  
> **Status Edge-TTS:** **Prototipe saja, TIDAK DISETUJUI UNTUK PRODUK (prototype only, not approved for product).**

## Keputusan
Status pemilihan vendor TTS ditetapkan sebagai **OPEN**.

### Syarat Penutupan Keputusan (Requirements to Close):
Keputusan vendor TTS baru dapat dikunci dan ditutup apabila salah satu kondisi berikut terpenuhi:
1. **Integrasi Resmi:** Disediakannya kredensial/kunci API resmi untuk layanan berlisensi, seperti:
   - Azure Cognitive Services Speech API (Tier S0 Pay-As-You-Go); atau
   - Cartesia Sonic / ElevenLabs Flash dengan kunci API resmi; **ATAU**
2. **Keputusan Tertulis Pengembang:** Keputusan eksplisit tertulis dari Daryl yang menyatakan menerima secara sadar risiko teknis dan hukum dari penggunaan wrapper tidak resmi (*Edge-TTS*) untuk demo publik.

*Keputusan akhir sepenuhnya berada di tangan pengembang (Daryl); agen pengembang tidak menentukan pilihan ini.*

## Alternatif yang Terbuka
- **Azure Cognitive Services Speech SDK Resmi (S0 Tier):** Menggunakan endpoint cloud resmi regional Asia Tenggara dengan koneksi persistent WebSocket.
- **Cartesia Sonic 3.x:** Vendor streaming ultra-rendah latensi (klaim TTFB < 90 ms) dengan model multibahasa.
- **ElevenLabs Flash v2.5:** Model streaming cepat dengan vokal ekspresif.

## Konsekuensi
- Arsitektur adapter (`TTSProvider` di `services/agent/src/lajur_agent/adapters/base.py`) tetap terisolasi sehingga provider resmi dapat langsung dihubungkan begitu kunci API tersedia tanpa mengubah kode agen lainnya.
