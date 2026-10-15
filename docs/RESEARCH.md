# Riset: AI Voice Ordering untuk Drive-Thru

> [!WARNING]
> Data di bawah dikumpulkan subagent via web search dan **belum saya verifikasi satu per satu**. Angka akurasi, harga, dan beberapa klaim (mis. status "tidak ada voice AI di KFC/Pizza Hut Indonesia", detail putusan hukum, jumlah store Wendy's) harus dicek ulang ke sumber primer sebelum dipakai untuk pitch atau wawancara. Angka Wendy's pun tidak konsisten antar sumber (75–86% autonomous).

## 1. Lanskap Kompetitor

| Pemain | Status | Pelajaran |
|---|---|---|
| Wendy's FreshAI (Google) | Rollout ratusan store | Autonomous ~75–86%, hemat ~22 detik. Berhasil karena ada layar konfirmasi + fallback ke crew |
| McDonald's + IBM | Dihentikan Juli 2024 | Akurasi mandek ~80–85% → 1 dari 6 order salah. Viral error (nugget berlebihan, dll.) |
| Taco Bell / Yum (Nvidia) | Scale ratusan store | Kena prank (order 18.000 gelas air) → butuh guardrail & fallback |
| Hi Auto (Checkers) | 350+ store | ~93–96% completion, bilingual EN/ES. **Paling relevan untuk code-switching** |
| SoundHound (SYNQ3) | Ribuan lokasi | ~90% autonomous |
| ConverseNow, Vox AI | Aktif (phone + drive-thru) | Upsell > manusia |
| Presto Automation | Delisted, SEC settlement 2025 | "AI-washing": mayoritas order sebenarnya diketik manusia offshore. Unit economics hancur |

**Kesimpulan:** ambang minimum operasional adalah ~95% akurasi tanpa intervensi. Di bawah itu, lane malah melambat.

## 2. Pasar & Pricing

- Pasar global ~\$1–1.5 miliar (2024), proyeksi \$12B+ di 2030 (angka riset pasar, treat as rough).
- Model harga global: \$200–500/bulan/store (software), \$800–1.500/lane (turnkey), atau \$0.50–1.50/order.
- Hardware per lane: \$2.500–10.000+.
- **Indonesia:** upah kru ~Rp3–5 juta/bulan, jadi pitch "ganti karyawan" tidak masuk akal. Jual **peningkatan average order value (upsell), tidak ada order terlewat saat peak, throughput**. Estimasi harga lokal: Rp1,5–3,5 juta/store/bulan atau Rp250–500/order (asumsi subagent, belum divalidasi ke pasar).

## 3. Celah Pasar (Peluang Nyata)

1. **Chain menengah (10–150 outlet) & franchisee independen.** Vendor besar fokus ke mega-chain.
2. **Indonesia/SEA:** drive-thru motor (helm, knalpot dekat mic), code-switching ID–EN ("di-upsize", "jangan pake salt"), dialek daerah. STT standar sering gagal di sini → ini diferensiasi teknis sekaligus moat.
3. **Channel non-drive-thru** (lihat bagian 6) yang jauh lebih murah untuk mulai.

## 4. Arsitektur Teknis yang Direkomendasikan

**Pipeline modular (cascade)**, bukan end-to-end realtime API.

```
Mic → [Edge: AEC, noise suppression, VAD] → STT streaming → LLM + tool calling → Cart state machine (deterministik) → TTS streaming → Speaker
                                                                          ↓
                                                        POS injection + layar konfirmasi
```

| Layer | Pilihan | Alasan |
|---|---|---|
| Framework | **LiveKit Agents** atau **Pipecat** (open source) | Kontrol penuh audio frame; Vapi/Retell terlalu mahal & kaku untuk hardware lane |
| STT | Deepgram Nova-3 (keyterm boosting menu) atau Whisper via Groq | Streaming, latensi 150–250ms. **Wajib benchmark dengan audio Bahasa Indonesia campur Inggris sebelum memilih** |
| LLM | Gemini Flash / GPT-4o-mini | TTFT 120–280ms, function calling andal |
| TTS | Cartesia Sonic atau Azure | TTFA ~100ms. Cek ketersediaan suara Bahasa Indonesia |
| Order logic | State machine deterministik di luar LLM | LLM hanya mem-parse intent ke JSON (`addItem`, `removeModifier`); tidak boleh mengarang item |

**Kenapa cascade, bukan realtime API:** order harus divalidasi terhadap menu & stok sebelum bot mengonfirmasi. Di realtime audio-to-audio, kamu tidak bisa menyisipkan guardrail teks sebelum suara keluar. Ini poin yang kuat untuk dijelaskan ke reviewer.

**Target latensi:** P50 < 650ms, P95 < 900ms.

**Masalah keras yang harus dipecahkan:**
- Noise mesin/hujan/helm: hardware mic direksional + RNNoise/DeepFilterNet.
- Echo (speaker dekat mic): AEC dengan referensi sinyal output.
- Jeda bicara pelanggan: VAD adaptif (perpanjang timeout jika kalimat menggantung).
- Barge-in: potong TTS < 80ms, batalkan generasi LLM.
- "Undo": "hapus kentangnya" tidak boleh menambah item (kegagalan klasik IBM).
- Handoff ke manusia: setelah confidence rendah 2 turn berturut, minta manusia, atau pelanggan ulang item 3×. Hardware bypass relay agar lane tidak mati bila cloud putus.

**Biaya per order (estimasi):** ~\$0.03 (modular) vs ~\$0.03 (OpenAI Realtime). Estimasi kasar subagent, kemungkinan underestimate; hitung ulang dengan trafik nyata.

**Evaluasi:** WER saja menyesatkan. Ukur Keyword Error Rate (item/modifier), Slot Error Rate, dan **Order Accuracy Rate end-to-end (target > 95%)**. Buat simulator "LLM sebagai pelanggan" + audio dicampur noise di berbagai SNR sebagai regression test.

## 5. Hardware & Integrasi

- Edge box fanless (mini PC) di back-of-house: AEC, VAD, loop detector (GPIO), bypass relay.
- Intercom: HME NEXEO punya interface digital; sistem lama lewat analog line-in/out + gateway audio-over-IP (mis. Barix).
- **Ini bagian tersulit & termahal untuk solo developer.** Akses ke headset system, instalasi di lapangan, dan sertifikasi POS butuh partner/restoran yang mau kerja sama.
- POS: Indonesia → ESB (enterprise), Moka, iSeller, Olsera; global → Toast, Square, NCR Aloha, Simphony. Cek ketersediaan API publik **sebelum** memilih target.

## 6. Strategi Rekomendasi (Fase Bertahap)

Rekomendasi saya: **jangan mulai dari hardware drive-thru.** Mulai dari software, buktikan akurasi, baru naik ke hardware.

| Fase | Output | Target "selesai" |
|---|---|---|
| 1. Simulator web (2–4 minggu) | Demo browser: menu board, mic, noise mesin/hujan, layar konfirmasi, POS mock | Order accuracy > 90% pada 100 skenario skrip, termasuk code-switching ID–EN, latensi P50 < 800ms |
| 2. Benchmark & eval harness | Dataset audio campur noise, metrik KER/SER/OAR | Angka terukur & dipublikasikan di README (talking point portofolio terkuat) |
| 3. Channel murah dulu | Voice ordering lewat telepon (SIP) atau **voice note WhatsApp** → keranjang + link QRIS | 1 restoran nyata pakai, 50+ order nyata |
| 4. Pilot drive-thru | 1 restoran independen dengan lane, edge box + mic | Pilot 60 hari, SLA jelas (akurasi, completion rate, waktu per order), fallback manusia selalu ada |
| 5. Scale | Chain menengah, integrasi POS, harga per store | Bergantung hasil fase 4 |

## 7. Deployment

- **Cloud:** region Jakarta (AWS `ap-southeast-3` / GCP `asia-southeast2`) atau Singapore (+20–30ms). LiveKit server + worker agent di Docker (1 worker ≈ 10–20 sesi konkuren, angka estimasi). Mulai dengan satu VM/ECS; Kubernetes baru perlu saat banyak store.
- **Edge:** mini PC fanless dengan Docker + watchdog.
- **Observability:** OpenTelemetry + Grafana. Metrik wajib: latensi turn, WER/KER, barge-in rate, escalation rate, **autonomous completion rate yang jujur**.
- **Reliability:** fail-safe wajib; jika koneksi/cloud putus, lane kembali ke headset manusia.
- **Publish demo:** simulator web → deploy ke Vercel/Cloudflare + backend voice di VM Jakarta/Singapore. Cocok untuk portofolio tanpa butuh restoran.

## 8. Legal & Privasi (verifikasi dengan ahli hukum sebelum komersial)

- **UU PDP No. 27/2022:** klaim subagent, suara bisa tergolong data biometrik/spesifik. Konsekuensi desain: beri notifikasi (papan + sapaan audio), jangan simpan audio mentah, simpan hanya teks order, siapkan DPIA.
- **Illinois BIPA (jika target AS):** kasus McDonald's/Presto soal voiceprint. Jangan lakukan speaker identification/voiceprint.
- **GDPR (jika EU):** dasar hukum pemrosesan + hak penghapusan.
- **PCI:** jangan pernah menerima nomor kartu lewat suara. Pembayaran di jendela atau link QRIS lewat gateway (Midtrans/Xendit).
- **Transparansi:** jangan klaim "full AI" jika ada manusia di belakang (pelajaran Presto/SEC).

## 9. Risiko Jujur

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Akurasi < 95% di kondisi nyata | Lane lebih lambat, brand rusak | Eval harness, fallback manusia, layar konfirmasi |
| Akses hardware/intercom/POS | Tidak bisa pilot | Mulai dari WhatsApp/telepon; cari 1 restoran mitra lebih awal |
| STT Bahasa Indonesia campur Inggris | Salah item | Benchmark multi-vendor, keyterm boosting, fuzzy match ke menu |
| Siklus penjualan chain besar 6–18 bulan | Tidak ada revenue | Target independen & chain kecil |
| Kompetitor besar masuk SEA | Moat hilang | Spesialisasi lokal: motor, dialek, harga lokal |
| Solo developer: beban hardware + sales + dev | Burnout / tidak selesai | Fase bertahap di atas |

## 10. Penilaian Jujur untuk Tujuan Portofolio

- **Sebagai produk komersial:** sulit untuk solo dev karena hardware, integrasi POS, dan siklus penjualan. Layak hanya jika ada mitra restoran nyata.
- **Sebagai proyek portofolio:** sangat kuat **jika** kamu punya angka terukur (latensi, OAR, KER) pada audio ID–EN bernoise, plus arsitektur yang bisa dijelaskan (kenapa cascade, kenapa state machine di luar LLM, kenapa fallback). Demo tanpa angka evaluasi hanya setara wrapper API.
- Poin terkuat yang bisa dijelaskan ke interviewer: (1) cascade vs realtime dan alasan guardrail, (2) cart state machine deterministik, (3) metrik evaluasi di luar WER, (4) desain privasi zero-retention, (5) pelajaran dari kegagalan IBM dan Presto.

## Sumber Utama (dari subagent, perlu dicek)

- AP News: McDonald's ends IBM test
- SEC: Presto Automation enforcement (2025)
- Jones Day: Carpenter v. McDonald's (BIPA)
- Forbes / Restaurant Dive: Wendy's FreshAI
- Business Wire: Checkers & Hi Auto
- QSR Magazine: biaya drive-thru AI
- HME NEXEO, LiveKit Agents, Pipecat, Deepgram, Cartesia, OpenAI Realtime docs
- UU 27/2022 (peraturan.bpk.go.id)
