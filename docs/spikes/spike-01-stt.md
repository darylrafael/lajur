# Spike 01 Report Template: Speech-to-Text (STT) Benchmark

**Document:** `docs/spikes/spike-01-stt.md`  
**Milestone:** Minggu 2 — Gate G1  
**Status:** Template / In Progress (Minggu 2a Preparation)  
**Author:** Daryl (Solo Dev)

---

## 1. Goal and Questions

**Core Question:** Which STT engine best handles Indonesian-English code-switched speech under clean and noisy acoustic conditions with Keyterm Error Rate (KER) $\le 15\%$ and estimated turn latency $\le 1.2$s?

**Candidate Engines:**
1. **Soniox:** Native code-switching ID–EN ($0.002/min)
2. **Deepgram Nova-3:** `language=id` + menu keyterm boosting ($0.0077/min)
3. **Gladia (Solaria-1):** Native intra-sentential code-switching ($0.0125/min)
4. **Groq Whisper:** `whisper-large-v3-turbo` with prompt biasing ($0.00067/min)

---

## 2. Benchmark Dataset & Conditions

- **Real Human Voice Recordings:** 40 sampled utterances (`eval/audio/real/manifest.csv`)
  - Condition A: `quiet` (clean indoor)
  - Condition B: `noise` (fan / ambient street)
  - Condition C: `helmet` (muffled / cloth dampening)
- **Synthetic Speech Dataset:** 100 scenarios, 200 utterances (`eval/audio/synthetic/manifest.csv`)
  - Clean vs Noisy (MUSAN ambient noise at SNR 10 dB)

---

## 3. Results Summary Table

| Vendor | Clean WER (%) | Clean KER (%) | Noisy KER (%) | Helmet KER (%) | P50 Latency (ms) | P95 Latency (ms) | Cost / 3-min Session | Gate G1 Status |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Soniox** | TBD | TBD | TBD | TBD | TBD | TBD | ~$0.0060 | Pending |
| **Deepgram** | TBD | TBD | TBD | TBD | TBD | TBD | ~$0.0231 | Pending |
| **Gladia** | TBD | TBD | TBD | TBD | TBD | TBD | ~$0.0375 | Pending |
| **Groq Whisper** | TBD | TBD | TBD | TBD | TBD | TBD | ~$0.0020 | Pending |

---

## 4. Qualitative Failure Analysis

### 4.1 Code-Switching Errors (e.g. *"french fries"*, *"double cheeseburger"*, *"large"*)
<!-- Catat kegagalan spesifik per vendor saat menangani istilah bahasa Inggris di tengah kalimat Indonesia -->

### 4.2 Acoustic Degradation (Noise & Helmet Muffling)
<!-- Catat bagaimana akurasi berubah ketika derau ditambahkan -->

### 4.3 Streaming Latency & Connection Stability
<!-- Catat perilaku WebRTC / WebSocket streaming dan jeda antar-token -->

---

## 5. Architectural Decision & Recommendation
<!-- Tentukan vendor STT primer terpilih untuk dimasukkan ke ADR vendor di akhir Minggu 2 -->
