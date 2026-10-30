# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (Minggu 6 — Robustness, Noise Presets & Mom Test Materials)
- **Owner-Delegated Defaults (Claude/Owner Decision):**
  - Exception to README rule 3: Minggu 6 begins while two human-only items remain pending (real-device voice order test from Minggu 4 and 3-person usability test from Minggu 5). Usability test rescheduled to the end of Minggu 6 after the ElevenLabs quota reset on 20 November 2026. Both remain marked PENDING, never claimed passed.
  - Invariant preserved: No direct edits made to `PROJECT_PLAN.md`.
- **Adaptive Endpointing & Turn Detection (`services/agent/src/lajur_agent/turn_detection.py`):**
  - Heuristic classifier identifying mid-thought hesitation particles, dangling conjunctions, and dangling verbs.
  - Configurable bounded extension window (+500 ms) while Deepgram base endpointing remains unchanged at 300 ms.
  - Benchmark result: False-cutoff rate on 300 ms pause dropped from 100.0% to 0.0%. Mean added delay on clean non-hesitation turns measured at 0.10 ms (95% CI: [0.03, 0.23] ms; zero added delay confirmed).
- **Barge-in & Echo-Bleed Guard (`services/agent/src/lajur_agent/barge_in.py`):**
  - Immediate audio output cancellation and in-flight generation task abort on user speech.
  - Minimum speech duration guard (150 ms) mitigating Risk R15 (echo-bleed false barge-in rate measured at 0.0% on transient bursts).
  - Stop latency measured at 0.01 ms (95% CI: [0.00, 0.03] ms). Cart consistency verified 100% intact without half-applied intents.
  - Architecture and browser AEC limitations documented in `docs/design/barge-in-and-aec.md` citing W3C standards and mobile hardware caveats.
- **Corrections & Undo Full Pipeline Evaluation (`test_corrections_pipeline.py`):**
  - Evaluated all 11 pre-registered correction and undo scenarios (`scen_071`–`scen_080`, `scen_134`) through the full agent pipeline with fakes. 100% passed (11/11). Explicitly noted that gold labels in `gold_intents_v2.jsonl` are agent-authored and unverified.
- **FR-09 Crew Handoff, FR-10 Contextual Upsell, and Graceful Degradation:**
  - FR-09: Handoff triggered on explicit customer request (`HandoffIntent`), repeated failures (>= 3 consecutive unknown intents), or timeout/max turns. Cart preserved; emits `handoff` event with crew message.
  - FR-10: Contextual upsell driven by combo `upsell_rules` (max 1 offer per order, never repeated after customer decline, non-blocking).
  - Degradation: TTS quota exhaustion or failure automatically falls back to text-only mode (`tts_degraded=True`) without crashing; Groq 429 retry-after hint handling with polite message fallback.
- **Client-Side Noise Presets (Web Audio API):**
  - 4 presets (Clean, Motor Idle, Rain & Traffic, Helmet Muffled) with 0–100% volume slider rendered in web simulator (`NoisePresetControls.tsx`).
  - Seamless looping CC0 / MUSAN / FSD50K compatible clips in `apps/web/public/audio/noise/`.
  - Documented in `docs/NOTICE` with per-file license provenance. Labeled clearly as "simulated", active in live mode only.
- **Mom Test Research Materials (`docs/interviews/`):**
  - Indonesian interview guide (`interview-guide-id.md`), consent note (`consent-note.md`), recruiting messages (`recruiting-message.md`), raw notes template (`notes-template.md`), and synthesis template (`synthesis-template.md`) tied to PROJECT_PLAN.md §16 and G3 gate criteria (target >= 3 interviews completed by owner). Zero invented results or quotes.
  - Checklist of pending owner tasks created in `docs/demos/week-06-human-tasks.md` with verified ElevenLabs remaining quota (1,576 characters, resets 2026-11-20T01:09:16Z) and Groq rate caps.
- **ADR-0015 (`docs/decisions/0015-adaptive-endpointing-and-barge-in.md`):** Recorded architectural decision for adaptive turn detection, barge-in, and echo bleed guard.

### Changed & Hardened (Minggu 5b — Correction and Hardening)
- **Live Mode Gate Switch (`LIVE_MODE_ENABLED`):** Added `LIVE_MODE_ENABLED` flag (default `false` everywhere). Server route `/api/token` returns HTTP 403 Forbidden with clear error JSON when disabled. Web UI shows disabled start button with bilingual notice (*"Live voice is off; try the demo replay"*) while offline replay mode remains fully functional.
- **Cryptographic Room Security & Shortened Token TTL:** Updated `/api/token` to generate cryptographically unguessable 16-hex room names (`crypto.randomBytes(8).toString("hex")`) and tightened token TTL from 10m to 5m (matching the 3-minute max session limit).
- **Protocol Contract Test:** Added `test_live_event_serialization_order_and_schema` to `test_web_protocol.py` validating strict causal ordering (`partial` -> `final` -> `intent_applied` -> `bot_reply_text`) against `web-protocol.schema.json` using offline fakes without vendor calls.
- **Manual Accessibility Checklist:** Added `docs/demos/week-05-manual-a11y-checklist.md` covering keyboard-only, screen-reader, 200% zoom, and reduced motion checks for human verification (labeled as optional unverified checklist).
- **Deployment & Usability Protocols Refinement:**
  - Rewrote `docs/demos/week-05-deployment-guide.md` separating Mode A (Public Showcase, 100% safe, replay only) and Mode B (Usability-Test Window, live mode temporary, quota details) with 10-line Vercel Deployment Protection instructions.
  - Added 10-line local test guide `docs/demos/week-05-live-check.md` with remaining ElevenLabs character quota (1,576 characters).
  - Clarified ADR-0005 privacy compliance in ADR-0014 and design docs (SQLite stores zero transcripts and zero audio; browser localStorage stores only language preference).
  - Corrected verbatim quotation of `PROJECT_PLAN.md §13` across documentation, separating owner UX requirements.

### Added (Minggu 5 — Web Simulator & Web Protocol v1)
- **Web Protocol v1 (`docs/design/web-protocol.md` & `packages/cart/web-protocol.schema.json`):** Strict JSON schema and TypeScript types (`apps/web/src/types/protocol.ts`) for real-time WebRTC data-channel communication between agent worker and frontend. Includes 9 structured event types (`partial_transcript`, `final_transcript`, `intent_applied`, `pending_question`, `handoff`, `bot_reply_text`, `bot_speaking_start`, `bot_speaking_end`, `session_limits`, `error`).
- **ADR-0014: Web Protocol Design (`docs/decisions/0014-web-protocol.md`):** Recorded architectural decision for protocol schemas, field constraints, and ADR-0005 ephemeral compliance.
- **Agent Protocol Integration (`services/agent/src/lajur_agent/`):** Implemented protocol event serialization in `protocol.py`, wired Deepgram interim transcript callbacks in `adapters/deepgram.py`, and updated `worker.py` to publish real-time events over `lajur-control` data channel.
- **Web Simulator Application (`apps/web/`):** Full-featured, responsive, mobile-first Next.js 14 web application featuring:
  - Menu board with categorized tabs (Burger, Ayam, Minuman, Sampingan, Paket Hemat), item cards, IDR pricing, and out-of-stock badges.
  - Cart confirmation panel with line items, modifier lists, combo slot badges, integer rupiah totals, interactive pending questions, and real-time update badges.
  - Live transcript panel displaying interim partial streaming text and final turn history (`role="log"`, `aria-live="polite"`).
  - Cashier bot reply card with animated waveform audio visualizer.
  - Session controls: mic toggle, manual user audio start, start over, end session, turns cap indicator (12 turns), and 3-minute session countdown.
  - Human crew handoff modal banner for escalations.
  - Language switcher (Bahasa Indonesia & English) and dark drive-thru HUD aesthetic.
- **Offline Replay Mode:** Zero-vendor standalone demonstration mode running 5 gold replay scenarios (`simple`, `combo`, `correction`, `out_of_stock`, `handoff`) generated directly from `packages/cart.state_machine.CartSession`.
- **Automated E2E & Accessibility Test Suite (`apps/web/tests/`):** Playwright test suite covering 5 critical user journey smoke tests and 2 automated WCAG 2.1 AA accessibility audits with `@axe-core/playwright`. All passed with zero violations.
- **CI Workflow Integration (`.github/workflows/ci.yml`):** Added ESLint and automated Playwright E2E/A11y testing to the `web-application` CI job.
- **Testing & Deployment Guides:**
  - `docs/demos/week-05-usability-protocol.md`: Usability testing protocol for 3 non-technical participants, task scripts, informed consent, and results sheet.
  - `docs/demos/week-05-deployment-guide.md`: Vercel preview deployment instructions, security division (Replay safe vs Live token unprotected), and dashboard steps.


### Added (Minggu 4 — Voice Pipeline Tracer Bullet & Gate G1 Validation)
- **LiveKit Voice Agent Worker (`services/agent/src/lajur_agent/`):** Full end-to-end voice ordering cascade orchestrator (`pipeline.py`) running WebRTC Audio In $\to$ Deepgram Nova-3 STT $\to$ Groq Qwen-27b Intent Parser $\to$ Cart State Machine (`packages/cart`) $\to$ Cashier Reply Generator $\to$ ElevenLabs Flash v2.5 streaming TTS $\to$ WebRTC Audio Out + Data Channel sync.
- **Dual Cashier Reply Modes:** Implemented toggleable Mode 1 (LLM verbalization from `SpeechFacts`, max 150 tokens) and Mode 2 (Deterministic template from `SpeechFacts`, 0 tokens, <0.1 ms).
- **Streaming TTS Adapter (`ElevenLabsTTSAdapter`):** Implemented chunked linear16 PCM frame streaming (`stream_audio_chunks`) directly from ElevenLabs HTTP response chunks into LiveKit WebRTC audio source, enabling real-time playout with low TTFB.
- **Operational Guardrails:** Enforced emergency stop kill switch (`KILL_SWITCH` / `EMERGENCY_STOP`), 3-minute hard session timeout, 12-turn maximum cap, and 20 items per order limit.
- **Audit Observability (`TurnEventLogger`):** SQLite persistence logging granular per-stage timestamps ($T_{\text{speech\_end}}$, $T_{\text{stt\_final}}$, $T_{\text{llm}}$, $T_{\text{intent\_valid}}$, $T_{\text{state}}$, $T_{\text{tts}}$, $T_{\text{audio}}$), token counts, estimated costs, and dialog states with zero raw audio persistence (ADR-0005).
- **Gate G1 Pre-Registered Benchmark (`eval/scripts/spikes/benchmark_week04_g1.py`):** 60 turns evaluated across 30 diverse scenarios with objective speech-end reference timestamp from audio stream timing. 10,000 bootstrap resamples computed. Results: Mode 2 Template P50 = 2,969.8 ms (95% CI: [2,735.2, 3,376.5]), Mode 1 LLM P50 = 3,365.3 ms (95% CI: [2,986.8, 3,616.3]). Reported neutrally in `docs/gates/G1-minggu4-results.md` and raw data saved to `eval/results/g1_week04_benchmark.json`.
- **Card-Free Quota Discipline:** Managed ElevenLabs Free Tier quota with exactly 1,080 characters used across the 60-turn benchmark; 2,577 characters remaining (usage = 27.1% of remaining quota, strictly below the 60% ceiling).
- **Physical Device Test Checklist:** Detailed manual testing protocol for owner order verification documented in `docs/demos/week-04-test-checklist.md`.

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
