# Spike 03 Report Template: LLM Intent Parsing Benchmark

**Document:** `docs/spikes/spike-03-llm.md`  
**Milestone:** Minggu 2 — Gate G1  
**Status:** Template / In Progress (Minggu 2a Preparation)  
**Author:** Daryl (Solo Dev)

---

## 1. Goal and Questions

**Core Question:** Which fast LLM accurately extracts structured JSON intents without hallucinating prices/items, maintaining Time to First Token (TTFT) < 300ms, and respecting user privacy?

**Candidate Models:**
1. **Google Gemini 2.5 Flash-Lite (Paid Tier):** $0.10 in / $0.40 out per 1M tokens. Guaranteed zero prompt training on paid Cloud billing.
2. **Google Gemini 2.5 Flash (Paid Tier):** $0.30 in / $2.50 out per 1M tokens.
3. **OpenAI GPT-4o-mini:** $0.15 in / $0.60 out per 1M tokens.

---

## 2. Test Corpus & Evaluation Criteria

- **Corpus:** 135 evaluation scenarios from `eval/datasets/v0/gold_intents.jsonl`.
- **Metrics:**
  - **Schema Compliance (%):** Syntactically valid JSON matching `docs/spikes/intent-schema-draft.md`.
  - **Intent Accuracy (%):** Exact match against gold intent sequence (`add_item`, `modify_item`, `undo`, `handoff`).
  - **TTFT P50 & P95 (ms):** Streaming latency until first token emission.
  - **Adversarial Resilience:** Rejection rate of prompt injections and pranks (scenarios 86–100).
  - **Cost per Order Session:** Based on ~5,000 prompt tokens and ~600 output tokens.

---

## 3. Results Summary Table

| Model | Schema Compliance (%) | Intent Accuracy (%) | TTFT P50 (ms) | TTFT P95 (ms) | Anti-Injection Pass (%) | Cost / Session | Status |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Gemini 2.5 Flash-Lite** | TBD | TBD | TBD | TBD | TBD | ~$0.00074 | Pending |
| **Gemini 2.5 Flash** | TBD | TBD | TBD | TBD | TBD | ~$0.00300 | Pending |
| **GPT-4o-mini** | TBD | TBD | TBD | TBD | TBD | ~$0.00111 | Pending |

---

## 4. Qualitative Failure Analysis
<!-- Analisis halusinasi item, kegagalan modifier kompleks, dan kesalahan parse kuantitas -->

---

## 5. Architectural Decision & Recommendation
<!-- Tentukan model LLM terpilih untuk implementasi pipeline suara mandiri di Minggu 4 -->
