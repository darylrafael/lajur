# Lajur

> A public, transparently measured drive-thru voice ordering demo built for Indonesian-English code-switched speech.

[![CI](https://github.com/darylrafael/lajur/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Data License: CDLA-Permissive-2.0](https://img.shields.io/badge/Data_License-CDLA--Permissive--2.0-green.svg)](eval/LICENSE-DATA.md)

---

## English Overview

**Lajur** is a solo-developer portfolio project and technical demonstration of a drive-thru-style voice ordering assistant. It is specifically designed to handle real-world Indonesian speech patterns—in particular, informal Indonesian mixed with English food terms (code-switching) under challenging acoustic environments (motorcycle engine idle, traffic, and helmet acoustic dampening).

Unlike proprietary voice ordering systems that conceal operational metrics or fail outside quiet vehicle cabins and standard English, Lajur publishes open, transparent accuracy and latency benchmarks directly on its public interface.

### Measured Latency (Gate G1-v2b Benchmark — 2026-10-26) [PROPOSED]

Measured on a consumer laptop in Jakarta, Indonesia over residential Wi-Fi, interacting with LiveKit Cloud (Hyderabad, India), Deepgram Nova-3 (California, US), Groq Qwen-2.5-32b (US via Anycast edge), and ElevenLabs Flash v2.5:

- **End-to-End Voice Turn Latency (Valid Turns, n=17):**
  - **Median (P50):** 3.59 s (95% Bootstrap CI: [2.18 s, 5.86 s])
  - **95th Percentile (P95):** 7.72 s (95% Bootstrap CI: [5.86 s, 8.21 s])
  - **Mean:** 4.04 s (95% Bootstrap CI: [3.09 s, 5.07 s])
- **All Recorded Turns (n=20, includes 3 clock-reference anomalies):**
  - **P50:** 4.03 s | **P95:** Distorted by harness timer artifact (see `docs/gates/G1-v2b-validity-rule.md`)
- **Stage Breakdown (Valid Turns P50):**
  - STT turnaround (`speech_final` with 500ms endpointing): 1.28 s
  - Intent classification LLM (TTFT): 0.56 s
  - Cart state machine transition: 0.0005 s (0.5 ms)
  - TTS TTFB (ElevenLabs Flash): 0.16 s
  - Client playout detection / network residual: 0.95 s
- **Gate G1 Verdict:** The 1.2 s PRD target and the 1.8 s owner fallback target are **NOT DEMONSTRATED** on this distributed cloud topology. Per project rules, targets are acknowledged as failed and are not adjusted upward. Optimization is deferred to post-MVP hosting co-location.

### Key Architecture Invariants
1. **Cascade Streaming Pipeline**: STT &rarr; LLM &rarr; TTS. Every phase is individually benchmarked and replaceable via provider adapters.
2. **Deterministic Cart State Machine**: Pure, isolated state machine outside the LLM. The LLM never mutates the cart directly and never invents items.
3. **Menu Service Source of Truth**: All prices, combo slots, required modifiers, stock levels, and operating hours are enforced deterministically by the menu service.
4. **Privacy First**: Audio is never recorded or stored (ADR-0005). Only anonymized text transcripts and performance telemetry are logged.
5. **Rigorous Guardrails**: Hard limits on session duration (3 minutes), turns, output tokens, and per-vendor spend caps to prevent abuse.

### Documentation Index
- [**Project Plan (`docs/PROJECT_PLAN.md`)**](docs/PROJECT_PLAN.md): The single source of truth for scope, non-goals, architecture, evaluation criteria, and the 10-week roadmap.
- [**Product Requirements Document (`docs/PRD.md`)**](docs/PRD.md): 1-page summary of core functional requirements, personas, and SLOs.
- [**Architecture (`docs/ARCHITECTURE.md`)**](docs/ARCHITECTURE.md): Component diagrams, data flow, and pipeline design.
- [**Architectural Decision Records (`docs/decisions/`)**](docs/decisions/): Recorded engineering trade-offs (ADR-0001 through ADR-0008).
- [**Risk Register (`docs/RISKS.md`)**](docs/RISKS.md): Actively tracked technical, operational, and financial risks.
- [**Background Research (`docs/RESEARCH.md`)**](docs/RESEARCH.md): Competitor landscape and baseline hypotheses.

---

## Ringkasan (Bahasa Indonesia)

**Lajur** adalah proyek demo pemesanan suara (*voice ordering*) drive-thru yang dibangun untuk memahami percakapan lisan sehari-hari di Indonesia: percampuran Bahasa Indonesia dan istilah menu bahasa Inggris (*code-switching*, misalnya *"paket hemat satu, di-upsize ya, tanpa ice"*), dengan metrik akurasi (*Order Accuracy Rate*) dan latensi turn (*end-to-end*) yang dipublikasikan secara transparan.

### Prinsip Utama Rekayasa
- **Bukan API Wrapper Kosmetik**: Menggabungkan WebRTC streaming (LiveKit), parser intent LLM yang menghasilkan JSON terstruktur, dan mesin state keranjang deterministik yang mencegah halusinasi pesanan.
- **Eval-Driven Development**: Setiap perubahan kode dan prompt diuji secara otomatis terhadap dataset skenario pesanan sintetis (`eval/datasets/`) dengan simulasi derau lingkungan (suara knalpot motor, jalan raya, dan filter akustik helm).
- **Transparansi Tanpa Kompromi**: Metrik kegagalan dan keberhasilan dilaporkan apa adanya berdasarkan data run yang tersimpan di repositori.

---

## Repository Structure

```text
.
├── apps/web/              # Next.js simulator & public metrics dashboard
├── services/agent/        # Python LiveKit agent worker (orchestration)
├── packages/cart/         # Deterministic cart state machine & menu validation
├── eval/                  # Evaluation datasets, acoustic noise, & benchmark harness
├── prompts/               # Versioned LLM prompt templates
├── docs/                  # Architecture, PRD, ADRs, risk register, and spikes
├── infra/                 # Docker Compose & container deployment configurations
└── .github/               # CI/CD workflows and PR templates
```

---

## License

- Code and documentation: [Apache License 2.0](LICENSE)
- Evaluation datasets and benchmark artifacts: [CDLA-Permissive-2.0](eval/LICENSE-DATA.md)
