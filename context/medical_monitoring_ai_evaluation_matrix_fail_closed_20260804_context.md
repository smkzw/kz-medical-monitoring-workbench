# Task Context: medical_monitoring_ai_evaluation_matrix_fail_closed_20260804

Created: 2026-08-04 22:40:27
Objective: Make independent-AI evaluation matrix completeness structural rather than trusting caller-supplied pair and status summary fields; block direct empty/orphan matrices while preserving builder output.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_evaluation_matrix.py`: immutable cross-project/task evidence matrix and completeness predicates.
- `services/api/app/monitoring_ai_release_gate.py`: offline release gate consuming matrix completeness.
- `tests/test_monitoring_ai_evaluation_matrix.py` and `tests/test_monitoring_ai_release_gate.py`: deterministic matrix/release regressions.
- Existing P10/B6/C14/approved-input/host-identity records: no provider/runtime/browser/real-project/medical-approval activation is permitted.
- Current filesystem is authoritative; no product runtime or external source is in scope.

## Scope

- In scope: make matrix completeness prove the exact project×task×track pair shape, unique observation-ID conservation, per-pair outcome classification, and stored missing/unreviewed/failed summaries; add a direct empty/orphan matrix regression and run adjacent offline contracts.
- Out of scope: changing observation generation, source ingestion, provider/runtime/browser/API login, real projects, UI, database state, or commercial release authority.

## Success Criteria

- A directly constructed matrix with no pairs or orphan observation IDs cannot report `evidence_matrix_complete=True`.
- A builder-produced complete matrix remains complete and deterministic.
- An incomplete matrix blocks the independent-AI release gate through the existing matrix condition; runtime/provider/write flags remain false.
- Related AI, release, real-loop/assurance, syntax, and port checks pass without starting a service.

## Risk Boundaries

- Only the matrix module, directly related tests, and task evidence surfaces may change.
- Do not touch production paths, persisted release artifacts, real projects, provider configuration, runtime state, browser state, or medical-writing files.
- No delegated agent/provider/Hermes session; Codex remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 22:40:27: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 22:42:00: Reproduced the direct empty/orphan matrix path and confirmed the builder's complete matrix remains valid.
- 2026-08-04 22:44:00: Added structural matrix proof and release-gate regression; focused, full AI, real-loop/assurance, compile and port checks passed.
