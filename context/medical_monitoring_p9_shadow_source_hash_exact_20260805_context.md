# Task Context: medical_monitoring_p9_shadow_source_hash_exact_20260805

Created: 2026-08-05 11:28:50
Objective: Harden shadow sample frozen source hash comparison so source lineage digests remain exact lowercase SHA-256 bytes
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_shadow_sample_service.py`: frozen batch source reconciliation and source hash projection.
- `services/api/app/monitoring_rule_authoring_service.py`: usable-source and applicability-evidence content-hash handoff guards.
- `tests/test_monitoring_shadow_sample_service.py`, `tests/test_monitoring_rule_authoring_service.py`, and adjacent batch/protocol suites.
- The active real-loop gate at `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` remains read-only/blocked.

## Scope

- In scope: make source registry, validation, frozen-batch binding, and shadow-source projection comparisons require exact raw lowercase 64-hex SHA-256 values; add focused regressions and evidence.
- Out of scope: evaluation-state/diagnostic-code normalization, clinical rule semantics, provider/runtime/browser activation, real projects, dependency installation, and medical-writing paths.

## Success Criteria

- Padded, uppercase and non-string source hashes fail closed at authoring and shadow-source boundaries.
- Valid canonical source hashes continue to load and are projected without normalization.
- Focused and adjacent suites pass; changed modules compile; preflight and review-gate pass.
- No services/providers/browsers/real projects or dependency activation while the gate is blocked.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 11:28:50: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 11:29-11:33: Codex direct route selected; no external Hermes/provider dispatch. Replaced authoring and frozen shadow-source hash normalization with exact raw validation and added focused handoff regressions.
- 2026-08-05 11:33: Focused shadow-sample suite **41 passed, 1 warning**; authoring suite **9 passed**; gold-shadow suite **16 passed**; protocol-rule/repository suite **63 passed**; batch/authoring adjacency **73 passed, 27 subtests**; protocol adjacency **57 passed, 1 warning**; daily adjacency **96 passed, 41 subtests**.
- 2026-08-05 11:33: Gate remains `read_only / blocked`; authority flags remain false and ports 8911/5174/8910/4173 remain empty.
