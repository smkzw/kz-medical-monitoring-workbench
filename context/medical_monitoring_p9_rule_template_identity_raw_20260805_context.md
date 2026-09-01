# Task Context: medical_monitoring_p9_rule_template_identity_raw_20260805

Created: 2026-08-05 19:57:13
Objective: Preserve raw persisted immutable mapping digest bytes during rule-template replay identity construction
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_rule_template_recommendation_service.py`: `_immutable_identity()` used when replaying a deterministic rule-template candidate.
- `tests/test_monitoring_rule_template_recommendation.py`: candidate decision/replay and source-drift regressions.
- `services/api/app/monitoring_rule_authoring_service.py`: downstream immutable-identity validation and rule compilation contract.
- `services/api/app/monitoring_ai_repository.py` and `services/api/app/monitoring_ai_contracts.py`: persisted payload/hash boundary used by replay.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`, the P9 checkpoint and LOOP ledger.
- Current filesystem plus the latest global/workspace/workbench `AGENTS.md` files.

## Scope

- In scope: preserve raw string bytes for the three immutable mapping digests in `_immutable_identity`; do not change intentional text normalization for `mapping_revision` and `recommendation_candidate_id`; add focused regression coverage and task evidence.
- Out of scope: rule semantics, provider/runtime/browser activation, API login, real projects, clinical/scientific/visual/commercial acceptance, unrelated hash helpers, and production paths.

## Success Criteria

- Padded, uppercase and non-string mapping identity digests are not coerced or trimmed into canonical values during replay identity construction; downstream strict rule validation can fail closed.
- Canonical valid values and existing replay/decision semantics remain unchanged.
- Focused and selected recommendation/authoring/protocol/readiness tests, targeted compilation, review-gate, exact manifest, gate and port checks pass.

## Risk Boundaries

- Do not activate providers, runtime, services, browser/Playwright/API login or real projects; do not cross the formal gate.
- Do not edit the runner-owned report path; Codex is final authority.

## Timeout Policy

- This is a direct Codex source-only slice; no external provider dispatch or sub-agent is allowed while the formal gate is blocked.

## Loop Log

- 2026-08-05 19:57:13: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 19:57:30: Direct Codex source-only route selected; no external provider dispatch is permitted by the formal gate.
- 2026-08-05 20:00:00: Raw immutable mapping digest preservation implemented; focused, selected, and compile checks passed. No provider/runtime/browser/real-project path was activated.
- 2026-08-05 20:00:00: Durable checkpoint and LOOP ledger updated; final exact-byte manifest is `records/active_slices/medical_monitoring_p9_rule_template_identity_raw_20260805/CHANGE_MANIFEST.md` (manifest excludes itself).
