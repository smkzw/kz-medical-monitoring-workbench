# Task Context: medical_monitoring_p9_mapping_draft_raw_hash_20260805

Created: 2026-08-05 20:09:47
Objective: Reject non-canonical persisted mapping-draft and chunk hash identities without string coercion
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_mapping_draft_repository.py`: persisted mapping chunk/revision/draft readers and hash admission points.
- `tests/test_monitoring_mapping_draft_repository.py`, `tests/test_monitoring_mapping_batch_lifecycle.py` and mapping activation/source tests: existing mapping persistence and identity regressions.
- `services/api/app/monitoring_ai_contracts.py`: canonical input/source digest contract used by mapping rows.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`, the P9 checkpoint and LOOP ledger.
- Current filesystem plus the latest global/workspace/workbench `AGENTS.md` files.

## Scope

- In scope: remove persisted-hash `str(...)` coercion in mapping chunk and draft readers; preserve raw string bytes and fail closed on non-canonical values; add focused regressions.
- Out of scope: mapping semantics, provider/runtime/browser activation, API login, real projects, clinical/scientific/visual/commercial acceptance, unrelated repositories or generic hash helpers.

## Success Criteria

- Persisted mapping chunk/draft/revision hash fields reject padded, uppercase and non-string values at the repository boundary; canonical mapping lifecycle behavior remains unchanged.
- Focused and selected mapping/protocol/readiness tests, targeted compilation, review-gate, exact manifest, gate and port checks pass.

## Risk Boundaries

- Do not activate providers, runtime, services, browser/Playwright/API login or real projects; do not cross the formal gate.
- Do not edit the runner-owned report path; Codex is final authority.

## Timeout Policy

- This is a direct Codex source-only slice; no external provider dispatch or sub-agent is allowed while the formal gate is blocked.

## Loop Log

- 2026-08-05 20:09:47: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 20:10:00: Direct Codex source-only route selected; no external provider dispatch is permitted by the formal gate.
- 2026-08-05 20:12:30: Raw mapping digest admission implemented; focused, selected, and compile checks passed. No provider/runtime/browser/real-project path was activated.
- 2026-08-05 20:12:30: Durable checkpoint and LOOP ledger updated; final exact-byte manifest is `records/active_slices/medical_monitoring_p9_mapping_draft_raw_hash_20260805/CHANGE_MANIFEST.md` (manifest excludes itself).
