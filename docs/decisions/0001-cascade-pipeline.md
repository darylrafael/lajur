# ADR-0001: Pipeline Cascade STT &rarr; LLM &rarr; TTS

## Status
Accepted

## Konteks
Sistem pemesanan suara (*voice ordering*) membutuhkan interaksi audio streaming dengan latensi rendah. Terdapat dua paradigma arsitektur utama:
1. **Audio-to-Audio Realtime Multimodal Model** (misal OpenAI Realtime API, Gemini Multimodal Live): Model memproses streaming audio langsung dan mengeluarkan streaming audio.
2. **Cascade Pipeline**: Pipeline terpisah yang terdiri dari Speech-to-Text (STT) &rarr; Large Language Model (LLM) untuk parsing intent &rarr; Text-to-Speech (TTS).

Pada sistem drive-thru restoran, kebenaran pesanan bersifat krusial. Pesanan harus divalidasi terhadap ketersediaan menu, stok bahan (*86'd*), jam operasional, dan aturan combo sebelum bot kasir mengonfirmasi pesanan kepada pelanggan.

## Keputusan
Kami mengadopsi arsitektur **Cascade Pipeline (STT &rarr; LLM &rarr; TTS)**. 
Transkrip teks dari STT diproses oleh LLM hanya untuk menghasilkan intent terstruktur (format JSON). Intent tersebut kemudian divalidasi dan diterapkan oleh Cart State Machine deterministik sebelum kalimat jawaban dikirim ke layanan TTS streaming.

## Alternatif yang Ditolak
- **Realtime Audio-to-Audio End-to-End API**: Ditolak karena:
  1. *Lack of Deterministic Control*: Sulit menjamin model tidak mengarang (berhalusinasi) item menu atau salah mengonfirmasi stok sebelum audio balasan keluar ke pelanggan.
  2. *Vendor Lock-in & Observability*: Latensi dan tingkat kesalahan tidak dapat diisolasi per komponen (tidak bisa membedakan apakah kesalahan terjadi pada pendengaran fonetik atau penalaran logika).
  3. *Biaya Tinggi*: Biaya streaming audio-to-audio per menit jauh lebih mahal dibandingkan kombinasi provider terpisah.

## Konsekuensi
- **Positif:**
  - Validasi stok, harga resmi, dan aturan menu 100% deterministik sebelum bot berbicara.
  - Setiap tahap dapat diukur latensinya secara terpisah (Time to First Audio STT, TTFT LLM, TTFB TTS).
  - Fleksibilitas mengganti komponen vendor (misal ganti STT tanpa mengubah logika dialog).
- **Negatif / Mitigasi:**
  - Akumulasi latensi *turn-taking* antar-komponen. Mitigasi: Menggunakan streaming di seluruh lapisan, WebSocket/WebRTC, dan VAD adaptif lokal.
