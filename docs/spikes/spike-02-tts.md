# Spike 02 Report Template: Text-to-Speech (TTS) Benchmark

**Document:** `docs/spikes/spike-02-tts.md`  
**Milestone:** Minggu 2 — Gate G1  
**Status:** Template / In Progress (Minggu 2a Preparation)  
**Author:** Daryl (Solo Dev)

---

## 1. Goal and Questions

**Core Question:** Which TTS engine produces the highest naturalness for Indonesian-English food terms while keeping Time to First Audio (TTFT) < 200ms and avoiding concurrency blocks?

**Candidate Engines:**
1. **Azure Speech (S0 Pay-As-You-Go):** `id-ID-GadisNeural`, `id-ID-ArdiNeural` ($16.00 / 1M chars)
2. **Cartesia Sonic (Sonic 3.x):** Indonesian support (< 90ms latency, ~$30.00 / 1M chars)
3. **ElevenLabs (Flash v2.5):** Indonesian support (< 75ms latency, ~$40.00 / 1M chars)

---

## 2. Test Utterances & Evaluation Metrics

Test corpus: 40 short drive-thru cashier responses containing mixed terms:
- *"Totalnya tiga puluh sembilan ribu kak, mau di-upsize french fries dan colanya?"*
- *"Satu paket hemat cheeseburger dengan dipping sauce BBQ sudah masuk ya kak."*
- *"Maaf kak, burger ikan krispi sedang 86 atau out of stock."*

**Metrics:**
- **Time To First Audio Chunk (TTFT / ms):** Measured from text submission to first audio byte.
- **Mixed Pronunciation Naturalness (1–5 scale):** Subjective evaluation of English menu words spoken by Indonesian neural voices.
- **Cost / 3-min Session:** Based on ~600 response characters per session.
- **Concurrency & Rate Limits:** Behavior under simultaneous requests.

---

## 3. Results Summary Table

| Vendor / Voice | TTFT P50 (ms) | TTFT P95 (ms) | Pronunciation Score (1–5) | Audio Quality / Artifacts | Cost / Session (~600 chars) | Status |
|---|:---:|:---:|:---:|---|:---:|:---:|
| **Azure (`id-ID-GadisNeural`)** | TBD | TBD | TBD | TBD | ~$0.0096 | Pending |
| **Azure (`id-ID-ArdiNeural`)** | TBD | TBD | TBD | TBD | ~$0.0096 | Pending |
| **Cartesia Sonic** | TBD | TBD | TBD | TBD | ~$0.0180 | Pending |
| **ElevenLabs Flash v2.5** | TBD | TBD | TBD | TBD | ~$0.0240 | Pending |

---

## 4. Trade-off Analysis & Recommendation
<!-- Tentukan vendor TTS primer terpilih untuk dimasukkan ke ADR vendor di akhir Minggu 2 -->
