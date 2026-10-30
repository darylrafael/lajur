# Risk Register — Lajur

**Versi:** 1.2 · **Terakhir Diperbarui:** 2026-10-21 (Minggu 2 Closeout & Gate G1 Audit)  
**Aturan Pembaruan:** Ditinjau dan diperbarui setiap sesi evaluasi mingguan. Skor Risiko = Probabilitas (P: 1–5) × Dampak (I: 1–5).

---

## 1. Tabel Risiko Aktif (v1.2)

| ID | Risiko | Kategori | P (1–5) | I (1–5) | Skor | Strategi Mitigasi | Indikator Pemicu (*Trigger*) | Status |
|---|---|---|:---:|:---:|:---:|---|---|:---:|
| **R1** | STT gagal mengenali *code-switching* ID–EN (menu Inggris dalam kalimat Indo) | Teknis | 3 | 5 | **15** | Benchmark 60 skenario baku di Gerbang G1 (Deepgram Nova-3 KER 3.89%, Groq 11.11%); pasang keyterm boost & alias fonetik di `packages/cart`; Deepgram Nova-3 diterima sebagai kandidat utama (ADR-0010) subjek verifikasi pipeline nyata di Minggu 4. | Keyterm Error Rate (KER) > 15% pada dev dataset | Terkendali (Provisional) |
| **R2** | Kuota bulanan LiveKit Cloud Build (1.000 menit agent) habis sebelum akhir bulan | Operasional | 4 | 3 | **12** | Batasi durasi sesi maks 2,5–3 menit; kuota harian global (~11–13 sesi/hari); sediakan fallback mode teks interaktif (FR-14); siapkan arsitektur self-host di VPS cadangan via Docker Compose. | Kuota terpakai > 50% dalam minggu pertama rilis atau > 80% sebelum tanggal 20 | Aktif |
| **R3** | Lonjakan biaya vendor / serangan *denial-of-wallet* tak terkendali oleh bot | Finansial / Keamanan | 3 | 5 | **15** | Pasang Cloudflare Turnstile captcha; rate-limiting per IP (2 sesi/IP/jam); batas maksimal 20 item per pesanan; batas token LLM; pasang *hard spend cap* ($10/bulan) dan alert di dashboard vendor. | Biaya harian aktual melebihi $1,00/hari | Aktif |
| **R4** | Latensi turn *end-to-end* melebihi batas kenyamanan (> 1,2 detik) dari koneksi Indonesia | Teknis | 4 | 4 | **16** | Diukur pada pipeline WebRTC nyata di Minggu 4 (60 turns): P50 = 2.969,8 ms (Templat) dan 3.365,3 ms (LLM). Keduanya meleset dari target 1,2s dan fallback pemilik (P50 $\le$ 1,8s). Keputusan Opsi B diserahkan sepenuhnya ke Daryl (ADR-0013). | Latensi turn P50 > 1.200 ms pada pipeline Minggu 4 | Terukur (Pending Owner Decision) |
| **R5** | *Scope Creep* (penambahan fitur di luar batasan portofolio & waktu solo dev) | Proses | 4 | 3 | **12** | Kunci daftar *Non-Goals* (§4.2) secara ketat; ide baru wajib dimasukkan ke `docs/BACKLOG-LATER.md`; tidak menambah fitur baru tanpa menghapus fitur lama setara. | Muncul tugas di luar PRD tanpa persetujuan ADR | Aktif |
| **R6** | Perubahan harga, pemutusan model, atau pemotongan free tier secara sepihak oleh vendor | Dependensi | 4 | 3 | **12** | Gunakan arsitektur adapter (ADR-0004); verifikasi rutin docs vendor; gunakan provider dengan API kompatibel (OpenAI-compatible). | Pemberitahuan deprecasi API / sunset model dari vendor | Aktif |
| **R7** | Pelanggaran privasi / data transkrip pengguna publik dijadikan bahan training model AI | Privasi / Legal | 3 | 5 | **15** | **Hard Constraint Card-Free**: Google Gemini Free Tier terbukti melatih model dari input sehingga dilarang menerima data pengunjung nyata (ADR-0005 & ADR-0012); Groq API terms mengecualikan pelatihan data API; ElevenLabs Free Tier terikat lisensi non-komersial dan wajib atribusi (ADR-0011). | Menemukan klausul TOS vendor yang mengambil hak training atas payload API | Aktif (Termitigasi untuk Groq) |
| **R8** | Ketiadaan TTS komersial berlisensi resmi tanpa kartu kredit (*Card-Free Constraint*) | Lisensi / Teknis | 4 | 3 | **12** | Vendor TTS resmi (Azure Speech, Cartesia, Soniox) mewajibkan kartu kredit (`excluded: card required`); Edge-TTS ditolak karena wrapper browser ilegal; ElevenLabs Free Tier diterima bersyarat khusus demo portofolio non-komersial (ADR-0011); deployment komersial tetap Open. | Kegagalan lisensi atau kehabisan kuota 10k karakter ElevenLabs | Aktif (Open ADR-0011) |
| **R9** | Kehabisan waktu dan kelelahan solo developer (kapasitas hanya 10–15 jam/minggu) | Proses | 3 | 4 | **12** | Sediakan masa penyangga di Minggu 8–10; pangkas fitur opsional (preset noise 4, dashboard publik) jika jadwal terancam; jangan pernah memangkas evaluasi (Minggu 7). | Dua minggu berturut-turut target mingguan tidak tercapai | Aktif |
| **R10** | Hasil akurasi akhir (*Order Accuracy Rate*) di bawah ekspektasi pasar | Kualitas Produk | 3 | 4 | **12** | Logika state machine deterministik selesai di Minggu 3 dan mencapai 100% pass rate pada 135 skenario baku dev split; baseline teks LLM diukur ulang di Minggu 4 dan Minggu 8. | Hasil evaluasi Gerbang G2 (Minggu 7) menghasilkan OAR < 75% | Terkendali di Cart (Minggu 3) |
| **R11** | Masalah legal merek dagang terkait nama makanan atau format menu | Legal | 2 | 3 | **6** | Gunakan nama menu generik fiktif 100% (ADR-0006); simpan pemetaan merek nyata secara privat di luar repositori publik (`private/`). | Adanya kemiripan nama produk fiktif dengan merek terdaftar | Aktif |
| **R12** | Ketiadaan validasi pasar / pengguna tidak bersedia membayar (jalur startup) | Bisnis | 4 | 3 | **12** | Lakukan wawancara *The Mom Test* kepada 8–10 pemilik F&B sejak Minggu 6; hentikan ekspansi startup di Gerbang G3 jika sinyal bayar nihil, pertahankan sebagai portofolio murni. | Kurang dari 2 pemilik F&B bersedia pilot di akhir Minggu 10 | Aktif |
| **R13** | Kegagalan akustik di balik helm pengendara motor (*muffled audio* & derau knalpot) | Teknis | 4 | 4 | **16** | Masukkan simulasi filter akustik helm (low-pass filter 3 kHz + resonansi helm) ke dataset eval; tambahkan alias fonetik kata menu untuk pengucapan teredam; VAD adaptif. | KER pada skenario noise helm > 20% pada Spike G1 | Aktif |
| **R14** | Kegagalan menangani slang & bahasa gaul lokal Indonesia (*"ijo-ijo"*, *"micin"*, *"es dikit"*) | Kualitas Produk | 4 | 3 | **12** | Tambahkan kamus sinonim slang kuliner Indonesia ke Menu Service dan prompt LLM; uji skenario modifier informal dalam dataset evaluasi dev split; coverage alias menu mencapai 100% di Minggu 3. | Muncul error parsing pada skenario slang di dev dataset | Terkendali di Menu |
| **R15** | *Acoustic echo / audio bleed* dari speaker fisik memicu *barge-in false positive* | Teknis | 4 | 4 | **16** | Aktifkan WebRTC Acoustic Echo Cancellation (AEC) di browser; pasang threshold VAD semantik yang mengabaikan energi audio saat TTS bot sedang aktif. | Bot memotong bicaranya sendiri tanpa suara pengguna pada tes speaker fisik | Aktif |
| **R16** | Eksploitasi *prompt injection* memanipulasi keranjang belanja & harga | Keamanan | 1 | 5 | **5** | **Termitigasi secara Konstruksi (Minggu 3)**: Intent Schema v1 melarang field ekstra (`extra="forbid"`) dan tanpa field finansial (`price`, `total`, `discount`). State machine murni menghitung harga secara independen dari `menu.json`. Uji properti membuktikan harga tidak dapat dimutasi oleh intent. | Tes red-team di Minggu 8 berhasil memanipulasi total harga | Termitigasi secara Konstruksi |
| **R17** | Kebijakan *autoplay* & izin mikrofon iOS Safari menolak audio WebRTC | Kompatibilitas | 4 | 3 | **12** | Buat alur interaksi eksplisit tombol *"Mulai Pesan (Aktifkan Suara)"* yang memicu Web Audio context resume sebelum sesi WebRTC terhubung; uji manual wajib di perangkat iPhone fisik. | Audio bisu saat pengujian di Safari iOS fisik | Aktif |
| **R18** | Dataset evaluasi terlalu optimis / tidak mencerminkan ucapan nyata (*overfitting dev set*) | Evaluasi | 4 | 4 | **16** | Kunci *held-out dataset* di Minggu 7 yang tidak pernah disentuh saat tuning prompt; perkaya skenario dengan jeda canggung (*hesitation*) dan rekaman suara manusia nyata pengembang sendiri. | Selisih skor OAR antara dev set dan pengujian manual > 15% | Aktif |
| **R19** | Kontainer Agent Worker pada Free Tier Hosting (Render) tertidur setelah 15 menit idle | Operasional / UX | 4 | 3 | **12** | Render Free Web Service memasuki mode sleep setelah 15 menit tanpa traffic HTTP masuk (koneksi outbound WebSocket worker tidak dihitung). Mitigasi: Frontend memicu `GET /health` ke URL worker saat halaman web simulator dibuka, memicu cold start resmi (~50s). Memori worker terukur 113.92 MB RSS (aman di bawah 512 MB). | Worker tidak menerima sesi audio karena tertidur | Aktif |

---

## 2. Rangkuman Tindakan Minggu 1
1. **Mitigasi R13 & R18:** Dataset evaluasi diperluas ke v0.1 dengan 135 skenario (35 skenario handwritten alami, 11 skenario noise helm, 54 skenario mixed ID-EN 40%).
2. **Mitigasi R16:** `packages/cart` (`MenuService`) telah dibangun murni deterministik. Seluruh harga dihitung dari `menu.json` dengan integer rupiah, dan LLM tidak memiliki akses mutasi langsung ke harga.
3. **Mitigasi R17:** Tombol *"Mulai Sesi"* di `apps/web` menginisialisasi mikrofon dan audio context setelah user interaction (klik tombol), mematuhi kebijakan autoplay iOS Safari.
4. **Checkpoint Hosting Minggu 9 (ADR-0009):** Sebelum peluncuran publik Minggu 9 (T-7 Hari), re-evaluasi paket hosting frontend (hubungi Vercel Support untuk klarifikasi status non-komersial portofolio dengan hipotesis startup, atau upgrade ke Vercel Pro $20/bln, atau migrasikan frontend ke Cloudflare / self-hosted).

---

## 3. Rangkuman Tindakan Minggu 2 (Gerbang G1 & Spikes)
1. **Penyelidikan Hard Constraint Card-Free:** Seluruh vendor disaring dengan batasan tanpa kartu kredit. Azure Speech, Cartesia, dan Soniox dikeluarkan (`excluded: card required`). Edge-TTS browser wrapper ditolak untuk produk resmi.
2. **Kandidat STT & LLM (ADR-0010 & ADR-0012):** Deepgram Nova-3 WebSocket streaming (KER 3.89%, P50 turn 524 ms) dan Groq Qwen-27b Non-Reasoning (Warm TTFT 258–419 ms, Cart Acc 76.7%) diterima sebagai kandidat utama, subjek pengukuran live pipeline di Minggu 4. Gemini Free Tier dilarang untuk data pengunjung riil (ADR-0005).
3. **Status TTS (ADR-0011):** ElevenLabs Free Tier (TTFB 126.8 ms) diterima bersyarat untuk demo portofolio non-komersial saja dengan kewajiban atribusi. Keputusan vendor komersial tetap Open.
4. **Hasil Gerbang G1 (ADR-0013):** Status gerbang ditetapkan sebagai **A-bersyarat (not demonstrated)**. Target 1.2s dipertahankan, dan titik keputusan dipra-registrasikan ke pengukuran live pipeline di Minggu 4 (`docs/gates/G1-minggu4-measurement.md`).
5. **Mitigasi R19 (Worker Hosting & Memory):** Memori proses utuh worker terukur 113.92 MB RSS (aman di bawah 512 MB). Mekanisme bangun container via HTTP health check dirancang untuk mengatasi sleep 15 menit Render Free.


---

## 4. Rangkuman Tindakan Minggu 3 (Cart State Machine & Intent Schema v1)
1. **Mitigasi R16 (Price Manipulation Impossible by Construction):** Skema intent v1 dibekukan dalam Pydantic discriminated union dengan `extra="forbid"` dan tanpa field finansial apapun (`price`, `total`, `discount`). State machine deterministik murni di luar LLM adalah satu-satunya entitas yang memutasi keranjang dan menghitung total harga dari `menu.json`.
2. **Mitigasi R10 (100% Core Scenarios Pass):** 100% (135/135) skenario evaluasi pada `eval/datasets/v0/gold_intents_v2.jsonl` lulus replay dengan pencocokan sempurna pada item, ukuran, modifier, combo slots, total harga integer rupiah, dan status keranjang.
3. **Mitigasi R14 (Menu Aliases 100% Coverage):** 20 alias baru ditambahkan ke `eval/menu/menu.json`, mencapai 100% alias coverage pada 135 transkrip evaluasi.
4. **Verifikasi Properti & Kualitas (Hypothesis & 96% Coverage):** Pengujian properti berbasis Hypothesis memverifikasi 8 invarian bisnis utama; modul `packages/cart` mencapai 96% coverage (melampaui target >=95%).

---

## 5. Rangkuman Tindakan Minggu 4 (Voice Pipeline Tracer Bullet & Gate G1 Validation)
1. **Pengukuran Empiris Latensi Pipeline Nyata (R4):** 60 giliran percakapan dieksekusi penuh pada WebRTC LiveKit, Deepgram Nova-3, Groq Qwen-27b, Cart State Machine, dan ElevenLabs Flash v2.5. Hasil pengukuran median: **P50 Templat = 2.969,8 ms** (95% CI: [2.735,2, 3.376,5]) dan **P50 LLM = 3.365,3 ms** (95% CI: [2.986,8, 3.616,3]). Target 1,2 detik asli dan fallback pemilik (P50 $\le$ 1,8 detik) terlewati. Hasil dilaporkan secara netral di `docs/gates/G1-minggu4-results.md` tanpa klaim kelulusan sepihak; keputusan arah arsitektur dan fallback Opsi B berada di tangan Daryl.
2. **Keandalan STT & False Cutoff (R1):** Pengaturan `endpointing=500` menghasilkan **0,0% false cutoff rate** tanpa pemotongan ucapan prematur di tengah kalimat. Akurasi intent mencapai 96,7% (Templat) dan 93,3% (LLM).
3. **Optimasi Kuota Card-Free ElevenLabs (R7 & R8):** Pengujian penuh 60 turn hanya mengonsumsi **1.080 karakter** berkat peringkasan respons kasir. Sisa kuota aman pada **2.577 karakter** (penggunaan 27,1% dari sisa kuota awal Minggu 4, aman di bawah batas 60%).
4. **Ketahanan Jaringan Adapter:** Adapter Groq dan Deepgram diperkuat dengan penanganan diskoneksi server (`ServerDisconnectedError` / `ClientError`), backoff 429 otomatis, dan boundary try-except per turn, menjamin eksekusi benchmark tanpa crash tak tertangani.


---

## 6. Rangkuman Tindakan Minggu 5 (Web Simulator & Web Protocol v1)
1. **Mitigasi R4 & UX Latensi (NFR-07):** Panel transkrip langsung (*live partial transcript*) diimplementasikan pada antarmuka web, menampilkan teks sementara saat pengguna berbicara. Keranjang diperbarui seketika saat intent diterapkan (*real-time cart update*), memberi kepastian visual kepada pengguna dan meredam persepsi latensi audio bot (P50 3,6s).
2. **Mitigasi R17 (iOS Safari Audio & Mic Permissions):** Simulator menerapkan pola gestur pengguna eksplisit: tombol *"Mulai Pesan (Aktifkan Suara)"* menginisialisasi mikrofon dan resume AudioContext sebelum koneksi WebRTC aktif. Pengujian otomatis Playwright memverifikasi alur inisiasi audio ini.
3. **Penyekatan Keamanan R2 & R3 (Token API & Replay Mode):** Sesuai catatan Minggu 5, rute `/api/token` belum dilengkapi captcha atau rate-limiting (dijadwalkan Minggu 9). Mode Replay offline disediakan sebagai media showcase publik 100% aman tanpa konsumsi token LiveKit maupun biaya vendor. Panduan deployment (`docs/demos/week-05-deployment-guide.md`) mendokumentasikan pemisahan risiko ini secara gamblang.
4. **Verifikasi Aksesibilitas Web (WCAG 2.1 AA):** Seluruh elemen visual, fokus keyboard (`tabIndex={0}`), dan pembaca layar (`aria-live="polite"`, `role="log"`) diaudit secara otomatis dengan Playwright + axe-core dengan 0 pelanggaran.
