# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (Minggu 3 — Cart State Machine + Intent Schema v1)
- **Intent Schema v1 (`packages/cart/src/lajur_cart/intents.py` & `intent.schema.json`):** Pydantic discriminated union of 12 structured intents with `ConfigDict(extra="forbid")` and zero financial fields (`price`, `total`, `discount`), rendering price manipulation impossible by construction. Exported official JSON Schema.
- **Pure Deterministic State Machine (`packages/cart/src/lajur_cart/state_machine.py`):** Pure functional `apply_intent()` transition system with full dialog states (`ordering`, `awaiting_choice`, `confirming`, `done`, `handoff`), deep immutable history, undo capability, pending combo slot / required modifier resolution, and structured rejections.
- **Replay Dataset v2 (`eval/datasets/v0/gold_intents_v2.jsonl`):** 135 agent-authored scenarios conforming to Intent Schema v1, replacing abstract undo with real conversational correction intents (`replace_item`, `remove_item`, `modify_item`, `clear_cart`).
- **Human Review Document (`docs/spikes/week-03-human-review.md`):** Side-by-side comparison table of 20 scenarios (all 11 correction/undo scenarios plus 9 seeded random scenarios, seed=42) labeled `unverified: agent-authored for human review`.
- **Scenario Replay Test Suite (`test_scenarios_v2_replay.py`):** 136 tests validating that the state machine reproduces expected cart items, quantities, sizes, modifiers, slots, total price, and status with 100% pass rate across all primary categories.
- **Property-Based Testing (`packages/cart/tests/test_property_state_machine.py`):** Hypothesis tests asserting 8 core business invariants under randomized sequences of valid and invalid intents.
- **High Code Coverage:** Achieved 96% line coverage across `packages/cart` (target >= 95%).
- **Interactive REPL CLI (`packages/cart/src/lajur_cart/repl.py`):** Added `python -m lajur_cart.repl` allowing human testers to exercise the state machine via JSON intents or simplified commands.
- **Alias Coverage Report (`docs/eval/alias-coverage-report.md`):** Added missing menu aliases and achieved 100% coverage on all 135 evaluation utterances.

### Added (Minggu 1 & 2 Spikes)
- **`packages/cart` Package:** Pure Python cart and menu management module with Pydantic models (`Item`, `Modifier`, `Combo`, `Cart`, `CartLine`), deterministic clock injection for operational hours (breakfast 05:00–11:00), out-of-stock validation, nested combo slot choices validation, and §11.2 20-items-per-order cap.
- **Cart Test Suite:** 149 comprehensive pytest tests verifying all edge cases and validating all 135 evaluation dataset scenarios against exact integer rupiah totals.
- **Dataset v0.1 & Coverage Report:** Expanded dev dataset to 135 scenarios (54 mixed ID-EN / 40%, 11 helmet noise, 8 human handoff requests, 8 prompt injection/prank, and 35 natural handwritten scenarios) documented in `eval/datasets/v0/COVERAGE.md`.
- **`apps/web` Walking Skeleton:** Next.js 14 frontend using `@livekit/components-react` with real-time WebRTC audio rendering, mic toggle, connection status indicators, and live ping-pong RTT latency measurement over `lajur-control` data channel.
- **LiveKit Token Server Route:** Server route at `apps/web/src/app/api/token` generating ephemeral room tokens with reserved placeholders for Cloudflare Turnstile and IP rate limiting.
- **`services/agent` Worker:** Python agent worker using `livekit-agents` (1.8.x) that echoes microphone audio frames via `rtc.AudioStream` and `rtc.AudioSource`, and responds to data channel ping heartbeats without incurring STT/LLM/TTS vendor fees.
- **Infrastructure:** Added `infra/docker-compose.yml` (local LiveKit server + Redis + Web + Agent), `services/agent/Dockerfile`, and `apps/web/Dockerfile`.
- **ADR-0009:** Architectural Decision Record documenting hosting options for frontend (Vercel Preview) and worker (Fly.io / Railway / local dev).
- **Risk Register v1.1:** Updated `docs/RISKS.md` integrating pre-mortem failure scenarios R13 through R18 (helmet acoustic muffling, Indonesian slang handling, barge-in echo bleed, prompt injection pricing bypass, iOS Safari autoplay, and evaluation overfitting).
- **Demo Script:** Added 2-minute recording script in `docs/demos/week-01-demo-script.md` for weekly video demonstration.
- **CI Pipeline:** Extended `.github/workflows/ci.yml` to run security guards, menu/scenario validation, Python workspace lint/typecheck/pytest, and Next.js web application build.

### Previously Added (Minggu 0 Kickoff)
- Repository scaffolding adhering to §12.1 structure (`apps/web`, `services/agent`, `packages/cart`, `eval`, `prompts`, `infra`, `docs`).
- License files: Apache-2.0 (`LICENSE`) for code and CDLA-Permissive-2.0 (`eval/LICENSE-DATA.md`) for synthetic evaluation datasets.
- Initial project documentation: `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/RISKS.md`.
- Architectural Decision Records `ADR 0001` through `ADR 0008` in `docs/decisions/`.
- Pull request template (`.github/pull_request_template.md`) with §12.4 Definition of Done checklist.
- Issue templates for spikes, ADRs, evaluations, and bug reports.
- Menu definition (`eval/menu/menu.json`), JSON Schema, and Python integrity validation script (`eval/menu/validate_menu.py`).
- 100 starter evaluation scenarios (`eval/datasets/v0/scenarios.jsonl`) with scenario verification script (`eval/scripts/validate_scenarios.py`).
- Confidential brand-to-generic item mapping in `private/` with automated CI git-tracking guard.
- Vendor verification documentation (`docs/spikes/vendor-facts-2026-10.md`), cost model recomputation, and account setup checklist (`docs/spikes/account-setup-checklist.md`).
- Pre-mortem failure analysis draft (`docs/premortem-draft.md`).
