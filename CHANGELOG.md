# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
