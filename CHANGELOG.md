# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
