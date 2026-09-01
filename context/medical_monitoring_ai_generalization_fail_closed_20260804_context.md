# Task Context: medical_monitoring_ai_generalization_fail_closed_20260804

Created: 2026-08-04 22:30:26
Objective: Ensure independent-AI generalization evidence cannot be manually constructed as empty/incomplete yet satisfy the release gate; preserve offline fail-closed boundaries and verify related contracts.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_generalization.py`: immutable structure-profile and anti-overfit evidence contract.
- `services/api/app/monitoring_ai_release_gate.py`: offline independent-AI release-gate builder; it must never grant runtime/provider/write permission.
- `tests/test_monitoring_ai_generalization.py` and `tests/test_monitoring_ai_release_gate.py`: deterministic regression contracts.
- Existing P10/real-loop gate records under `records/active_slices/`: runtime, provider, real-project and medical-approval gates remain closed and read-only.
- The current filesystem is authoritative; no real project data, browser, service, provider, API login, SQLite or Playwright is in scope for this slice.

## Scope

- In scope: make `MonitoringAiGeneralizationEvidence.complete` structurally fail closed when profiles are missing, outside the required real/unseen sets, duplicated, on the wrong track, insufficiently diverse, or duplicate a real structure; require that property in the release gate; add focused regressions and verification records.
- Out of scope: provider/runtime activation, medical approval, real-project ingestion, database changes, UI changes, broad refactors, external research, and modifying reserved-port state.

## Success Criteria

- A directly constructed evidence object with a valid empty profile snapshot cannot report `complete=True`.
- A valid builder-produced real/unseen evidence bundle remains complete.
- The offline release gate blocks structurally incomplete evidence with an auditable reason and keeps all runtime/provider/write flags false.
- Focused tests, related medical-monitoring backend tests, source syntax checks, frontend contracts, Node contracts, build, and reserved-port checks pass; no runtime is started.

## Risk Boundaries

- Only the workbench source/tests and task evidence surfaces may be changed; preserve unrelated user changes.
- Do not write to production paths, real project folders, databases, runtime state, or external systems.
- Keep `8911`, `5174`, `8910`, and `4173` stopped/empty.
- This slice is direct Codex work; no provider dispatch or sub-agent is used. Codex remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 22:30:26: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 22:32:00: Reproduced the direct-construction gap: a valid-hash empty profile snapshot had `issues=()` and previously reported complete.
- 2026-08-04 22:34:00: Added immutable structural completeness proof and required it in the release gate; added model and gate regressions.
- 2026-08-04 22:36:00: Focused/adjacent backend, frontend, Node, compile, build, and port checks passed; formal runtime/provider/write gates remain closed.
