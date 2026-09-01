# Task Context: medical_monitoring_p9_release_evidence_hash_exact_20260805

Created: 2026-08-05 11:40:53
Objective: Harden release evidence revalidation source and gate digest admission so evidence hashes remain exact lowercase SHA-256 bytes
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_release_evidence_revalidation.py`: read-only release coverage source/gate digest revalidation.
- `tests/test_monitoring_release_evidence_revalidation.py` and adjacent release/readiness tests.
- The active real-loop gate at `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` remains read-only/blocked.

## Scope

- In scope: make declared source and gate evidence digests require exact raw lowercase 64-hex SHA-256 bytes at the read-only revalidation boundary; add focused regressions and evidence.
- Out of scope: release authority decisions, B6/C14 activation, filesystem scope rules, clinical semantics, provider/runtime/browser activation, real projects, dependency installation, and medical-writing paths.

## Success Criteria

- Uppercase, padded and non-string source/gate digests are rejected or unbound rather than normalized.
- Current canonical read-only coverage remains fresh/blocked as before.
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

- 2026-08-05 11:40:53: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 11:41-11:43: Codex direct route selected; no external Hermes/provider dispatch. Removed source/gate SHA lowercasing and added exact-shape regressions.
- 2026-08-05 11:43: Focused release revalidation suite **10 passed**; release gate/dossier/revalidation **25 passed**; runtime identity revalidation **7 passed**; LOOP readiness/revalidation **36 passed**.
- 2026-08-05 11:43: Gate remains `read_only / blocked`; authority flags remain false and ports 8911/5174/8910/4173 remain empty.
