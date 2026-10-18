# Gate G1 Review: Speech Viability Decision Record

**Document:** `docs/gates/G1-review.md`  
**Milestone:** End of Minggu 2 (Gerbang G1)  
**Status:** DRAFT / Template (To be finalized after vendor benchmarks in Minggu 2b)  
**Author:** Daryl (Solo Dev)

---

## 1. Exact Gate G1 Criteria (PROJECT_PLAN.md §3.2 Verbatim)

> **Kondisi Kegagalan (Kill / Pivot Trigger):**  
> *"Tidak ada vendor STT dengan KER ≤ 15% pada set ucapan ID–EN bersih dan latensi turn estimasi ≤ 1,2s"*
> 
> **Tindakan jika Gagal:**  
> *"Pivot ke normalisasi LLM pasca-STT atau turunkan klaim (\"mostly Indonesian + English item names\") dan perluas menu dengan alias. Jika tetap gagal: pindah ke bahasa Inggris saja + ID parsial, dan ubah narasi portofolio"*

---

## 2. Evaluation Evidence Summary

### 2.1 STT Accuracy & Latency (Spike 01)
- **Evaluation Dataset:** 40 clean human recordings (`eval/audio/real/`) + 100 clean synthetic utterances.
- **Metric Enforcement:** Keyword Error Rate (KER) with sequence alignment per `docs/eval/metrics.md`.

| Candidate Engine | Clean KER (%) | Turn Latency Estimate (ms) | Condition Pass? (KER $\le$ 15% & Latency $\le$ 1.2s) |
|---|:---:|:---:|:---:|
| **Soniox** | TBD | TBD | Pending |
| **Deepgram Nova-3** | TBD | TBD | Pending |
| **Gladia (Solaria-1)** | TBD | TBD | Pending |
| **Groq Whisper** | TBD | TBD | Pending |

### 2.2 TTS Quality & Concurrency (Spike 02)
- Winner: `[Azure S0 / Cartesia / ElevenLabs]` (TTFT: `TBD` ms, Cost: `$TBD`)

### 2.3 LLM Intent Parsing (Spike 03)
- Winner: `[Gemini 2.5 Flash-Lite / GPT-4o-mini]` (Intent Accuracy: `TBD`%, TTFT: `TBD` ms, Cost: `$TBD`)

---

## 3. Formal Gate Decision

- [ ] **PASS:** Setidaknya satu vendor memenuhi kriteria (KER $\le$ 15% pada audio bersih dan latensi $\le$ 1,2 detik). Lanjut ke Minggu 3 (Cart State Machine Selesai).
- [ ] **PIVOT:** Tidak ada vendor yang memenuhi batas 15% KER secara langsung; aktifkan mitigasi normalisasi LLM pasca-STT dan perluas kamus alias.
- [ ] **KILL / SCOPE DOWN:** Ubah narasi portofolio ke bahasa Inggris dominan dengan pengenalan item Indonesia parsial.

---

## 4. Vendor Selection Table for Architecture (ADR-0010)

| Pipeline Phase | Selected Primary Vendor | Backup / Fallback Vendor | Monthly Budget Impact |
|---|---|---|:---:|
| **STT** | TBD | TBD | < $5.00 |
| **LLM** | TBD | TBD | < $2.00 |
| **TTS** | TBD | TBD | < $5.00 |
| **WebRTC Transport** | LiveKit Cloud (Build Tier) | Self-hosted LiveKit (Docker) | $0.00 |

---

## 5. Next Steps
- Implementasi vendor adapters resmi di `services/agent/src/lajur_agent/adapters/`.
- Memperbarui CHANGELOG dan mengunci baseline vendor sebelum memulai Minggu 3.
