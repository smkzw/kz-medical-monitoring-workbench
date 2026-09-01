# Task Context: medical_monitoring_daily_diff_summary_20260803

Created: 2026-08-03 20:56:30
Objective: Expose the existing immutable daily-run diff snapshot as a strict read-only summary for medical monitors without changing backend facts or release gates
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Frontend consumer: `frontend/src/features/medical-monitoring/MedicalMonitoringDailyRunPanel.jsx` and `medicalMonitoringDailyRunView.mjs`.
- Existing API contract: `services/api/app/monitoring_daily_run_router.py::_diff_dict` exposes an immutable detail snapshot whose `payload` is produced by `MonitoringBatchService.detailed_diff`.
- Existing payload producer: `services/api/app/monitoring_batch_service.py` and `services/api/app/monitoring_batch_diff.py` (`row_diff`, `field_changes`, `schema_diffs`, removal-resolution and `full_snapshot_proven`).
- Existing tests/build: `frontend/src/features/medical-monitoring/medicalMonitoringDailyRunView.test.mjs`, the medical-monitoring Node test set, and the frontend Vite build.
- Release boundary: B6/C14 remain fail-closed (`write_permitted=false`, activation blocked); no live service, real project, browser, or external provider may be started by this slice.
- Current filesystem is authoritative. The output is a read-only presentation consumer; it must not create or infer risk facts.

## Scope

- In scope: strict normalization of the existing `detail.diff` payload; compact counts for new/changed/persisting/removed rows, field/schema changes, identity matches, and removal evidence; clear missing/invalid evidence states; mount the read-only summary in the daily-run panel; focused and existing frontend regressions.
- Out of scope: backend/API schema changes, diff algorithm changes, risk disposition or persistence changes, release-gate changes, live services, browser/Playwright tests, real project batches, and clinical interpretation.

## Success Criteria

- A malformed or absent diff is never coerced into a clean/zero result; the panel states when the snapshot or evidence is unavailable.
- Valid payloads expose only explicit non-negative counts and provenance fields, with removal blockers kept distinct from eligible removals.
- The panel remains concise for a senior monitor and preserves the existing state machine/action controls.
- New focused model assertions, all medical-monitoring Node tests, Vite build, static review, and empty-port check pass.
- Durable task context, review, metrics, and LOOP ledger record the evidence and next safe action.

## Risk Boundaries

- Only the workbench source and its task records may change. Do not touch production project data, product runtime stores, B6/C14 evidence, or unrelated worktrees.
- Do not reinterpret count absence as zero or absence of a row as absence of a risk.
- Do not claim clinical causality, data completeness, or release readiness from the summary.
- Codex is the final authority; no delegated agent is dispatched for this direct slice.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 20:56:30: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Direct Codex implementation planned after inspecting the existing immutable diff payload and daily-run panel. External execution is intentionally not dispatched; the prompt remains a guard-compatible record only.
- 2026-08-03: Added strict read-only diff normalizer and compact summary to the daily-run panel. Focused model, all 26 medical-monitoring Node files and Vite build passed; no service, browser, runtime, real project or release-gate action occurred.
