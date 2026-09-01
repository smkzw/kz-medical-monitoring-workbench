# Task Context: medical_monitoring_p9_ai_repository_hash_raw_20260805

Created: 2026-08-05 20:02:44
Objective: Require exact raw lowercase persisted hashes at the monitoring AI repository read boundary
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_repository.py`: persisted monitoring-AI job, candidate, attempt, repair and conversation hash readers.
- `tests/test_monitoring_ai_repository.py` and `tests/test_monitoring_ai_v7_deterministic_repair.py`: repository tamper and deterministic-repair regressions.
- `services/api/app/monitoring_ai_contracts.py`: canonical digest contract used by stored AI identity rows.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`, the P9 checkpoint and LOOP ledger.
- Current filesystem plus the latest global/workspace/workbench `AGENTS.md` files.

## Scope

- In scope: make `_required_sha256` reject raw padded/uppercase/non-string values without `str(...).strip()` coercion; add focused persisted-row regressions for the monitoring-AI repository.
- Out of scope: AI semantics, provider/runtime/browser activation, API login, real projects, clinical/scientific/visual/commercial acceptance, unrelated repositories or generic hash helpers.

## Success Criteria

- Persisted monitoring-AI hash fields fail closed on non-canonical raw bytes, while canonical rows and payload/replay semantics remain unchanged.
- Focused and selected repository/AI/readiness tests, targeted compilation, review-gate, exact manifest, gate and port checks pass.

## Risk Boundaries

- Do not activate providers, runtime, services, browser/Playwright/API login or real projects; do not cross the formal gate.
- Do not edit the runner-owned report path; Codex is final authority.

## Timeout Policy

- This is a direct Codex source-only slice; no external provider dispatch or sub-agent is allowed while the formal gate is blocked.

## Loop Log

- 2026-08-05 20:02:44: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 20:03:00: Direct Codex source-only route selected; no external provider dispatch is permitted by the formal gate.
- 2026-08-05 20:06:30: Strict raw persisted-hash validation implemented; focused, selected, and compile checks passed. No provider/runtime/browser/real-project path was activated.
- 2026-08-05 20:06:30: Durable checkpoint and LOOP ledger updated; final exact-byte manifest is `records/active_slices/medical_monitoring_p9_ai_repository_hash_raw_20260805/CHANGE_MANIFEST.md` (manifest excludes itself).
