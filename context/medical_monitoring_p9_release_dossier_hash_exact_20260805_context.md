# Task Context: medical_monitoring_p9_release_dossier_hash_exact_20260805

Created: 2026-08-05 19:44:33
Objective: Require exact lowercase evidence hashes in the offline commercial release dossier contract without changing release readiness semantics
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_release_dossier.py`: offline commercial release-dossier evidence hash contract.
- `tests/test_monitoring_release_dossier.py`: dossier section/signoff/residual-risk construction and release-readiness regressions.
- `services/api/app/monitoring_release_dossier_revalidation.py` and its tests: downstream persisted-dossier exactness expectations.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`, the P9 checkpoint and LOOP ledger.
- Current filesystem plus the latest global/workspace/workbench `AGENTS.md` files.

## Scope

- In scope: remove `.strip().lower()` normalization from dossier evidence hash admission; add focused malformed-hash regressions and task evidence.
- Out of scope: release readiness policy, signoff roles, control partition semantics, persisted file I/O, provider/runtime/browser activation, API login, real projects and commercial release authorization.

## Success Criteria

- Padded, uppercase and non-string dossier evidence hashes fail closed; canonical complete/partial dossier status and gate binding remain unchanged.
- Focused and selected dossier/revalidation/release-gate/readiness tests pass; targeted compilation passes; review-gate is green.
- The formal real-loop gate remains `read_only / blocked` with all activation/provider/runtime/write flags false and ports 8911/5174/8910/4173 empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 19:44:33: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 19:45:00: Codex direct source-only route selected; no external provider dispatch is permitted by the formal gate.
- 2026-08-05 19:48:00: Exact dossier evidence hash validation and focused regression passed; selected adjacency and compilation passed. Review-gate is green, the nine-row manifest verifies exactly, the formal gate remains blocked/read-only, and all reserved ports are empty.
