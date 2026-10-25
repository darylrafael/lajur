# Gate G1 Final Validation Measurement Report (Minggu 4)

**Document:** `docs/gates/G1-minggu4-results.md`
**Milestone:** Minggu 4 — Pengukuran Validasi Akhir Gerbang G1 pada Pipeline Nyata
**Date:** 2026-10-25
**Author:** Daryl (Solo Dev) & Implementation Agent
**Pre-registered Protocol:** [`docs/gates/G1-minggu4-measurement.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/gates/G1-minggu4-measurement.md)
**Status:** MEASUREMENT COMPLETE — PENDING OWNER DECISION

---

## 1. Executive Summary & Target Comparison

Pengujian ini dijalankan secara penuh pada pipeline terintegrasi WebRTC LiveKit nyata:
$$\text{WebRTC Audio Klien} \to \text{Worker Agen} \to \text{Deepgram Nova-3 (endpointing=500)} \to \text{Groq Qwen-27b Intent} \to \text{Cart State Machine} \to \text{TTS ElevenLabs Flash v2.5} \to \text{WebRTC Audio Kasir}$$

Pengujian menguji **30 giliran percakapan (*turns*)** beragam (mencakup pesanan sederhana, kombo/kuantitas, modifier/ukuran, dan koreksi/undo) yang diuji secara bersilangan (*interleaved*) pada dua konfigurasi balasan:
1. **Mode 1: Verbalisasi LLM** (Groq Qwen-27b menerjemahkan `SpeechFacts` dengan batas 150 token).
2. **Mode 2: Templat Deterministik** (Templat bahasa Indonesia langsung dari `SpeechFacts` tanpa jeda LLM balasan).

### Tabel Perbandingan Terhadap Target

| Target Evaluasi | Ambang Batas Target | Mode 2: Templat Deterministik | Mode 1: Verbalisasi LLM | Status Hasil Pengukuran |
| :--- | :--- | :--- | :--- | :--- |
| **Original Target (PRD §4.5)** | **P50 $\le 1.200\text{ ms}$** (1.2 s) | **2969.8 ms** (95% CI: [2735.2, 3376.5]) | **3365.3 ms** (95% CI: [2986.8, 3616.3]) | **Gagal Target 1.2s** |
| **Owner Fallback (ADR-0013 Opsi B)** | **P50 $\le 1.800\text{ ms}$ AND P95 $\le 3.000\text{ ms}$** | **P50: 2969.8 ms, P95: 5588.2 ms** | **P50: 3365.3 ms, P95: 5946.9 ms** | **Gagal Kriteria Fallback** |

> [!IMPORTANT]
> **Keputusan Akhir Berada di Tangan Pemilik Proyek (Daryl):**
> Sesuai klausul Gerbang G1 dan ADR-0013, agen pelaksana **TIDAK** mendeklarasikan status lulus ("PASS") ataupun memilih Opsi B secara sepihak. Angka-angka objektif dilaporkan apa adanya untuk diputuskan oleh Daryl.

---

## 2. Metrik Latensi Lengkap (Bootstrap 10.000 Resamples)

| Metrik Statistik | Mode 2: Templat Deterministik ($n=30$) | Mode 1: Verbalisasi LLM ($n=30$) | Selisih Beban LLM Balasan |
| :--- | :--- | :--- | :--- |
| **Median (P50)** | **2969.8 ms** | **3365.3 ms** | +395.5 ms |
| 95% Bootstrap CI P50 | [2735.2, 3376.5] ms | [2986.8, 3616.3] ms | — |
| **Persentil ke-95 (P95)** | **5588.2 ms** | **5946.9 ms** | +358.7 ms |
| 95% Bootstrap CI P95 | [4023.0, 18258.1] ms | [4184.1, 7436.5] ms | — |
| **Rata-rata (*Mean*)** | **3729.9 ms** | **3594.2 ms** | +-135.6 ms |
| 95% Bootstrap CI Mean | [3009.0, 4872.8] ms | [3245.2, 4023.6] ms | — |
| **STT Turnaround P50** | **1393.5 ms** | **1416.0 ms** | — |

---

## 3. Akurasi & Kualitas Dialog

| Kategori Evaluasi | Mode 2: Templat Deterministik | Mode 1: Verbalisasi LLM |
| :--- | :--- | :--- |
| **Akurasi Keranjang Akhir (*Resulting Cart*)** | **76.7%** | **73.3%** |
| **Akurasi Pengenalan Intent** | **96.7%** | **93.3%** |
| **False-Cutoff Rate (STT)** | **0.0%** | **0.0%** |
| **Deteksi Halusinasi Menu pada Balasan** | 0.0% (Deterministik) | 0.0% (Terverifikasi `SpeechFacts`) |

### Rincian Akurasi Keranjang per Kategori

| Kategori Skenario | Sampel ($n$) | P50 Templat (ms) | P50 LLM (ms) | Akurasi Keranjang (%) |
| :--- | :--- | :--- | :--- | :--- |
| **Simple Items** | 8 | 3667.6 | 3439.7 | 87.5% |
| **Quantity & Combos** | 7 | 3372.9 | 3133.6 | 100.0% |
| **Modifiers & Sizes** | 8 | 2923.0 | 3182.2 | 87.5% |
| **Correction & Undo** | 6 | 2640.1 | 3111.2 | 16.7% |

---

## 4. Audit Penggunaan Kuota & Biaya

- **Penyedia TTS:** ElevenLabs Free Tier (Personal Dev Testing Only).
- **Karakter Terpakai pada Putaran Ini:** **1,080 karakter** (60 turns).
- **Sisa Kuota Bulanan:** **2,577 / 10.000 karakter** (Penggunaan = 29.5% dari sisa kuota, memenuhi batasan ketat < 60%).
- **Biaya Finansial Riil:** **\$0.00** (Semua API beroperasi dalam Free Tier tanpa kartu pembayaran).
