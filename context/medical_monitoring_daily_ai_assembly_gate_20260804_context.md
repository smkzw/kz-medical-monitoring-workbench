# Task Context: medical_monitoring_daily_ai_assembly_gate_20260804

Created: 2026-08-04 16:02:42
Objective: Prevent the daily monitoring UI from offering risk assembly while the independent-AI progress ledger is missing, malformed, running, or inconsistent with the submitted job count.
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyRunPanel.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyRunView.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyAiEvidence.mjs`
- `services/api/app/monitoring_daily_run_analysis_service.py` (read-only backend contract)
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyRunView.test.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringProjectSwitchIsolation.test.mjs`
- Current P10 LOOP ledger and B6/C14 gate artifacts under `records/active_slices/` and `runs/execution/`.

## Scope

- In scope: a pure frontend view-model gate plus the smallest panel wiring and focused regression.
- Out of scope: API/service/repository/runtime/provider/browser/Playwright/real-project changes,
  medical conclusions, B6/C14/aggregate/CAS/source-token authority, and medical-writing files.

## Success Criteria

- The panel does not offer `汇总风险项` unless the submitted AI job count and the explicit
  progress ledger agree and the ledger is terminal (`completed`, `partial_completed`, `failed`),
  with the explicit zero-job case handled separately.
- Missing, malformed, running, queued/inconsistent, or unknown progress is visible as a blocked
  wait state and never treated as completion or no-risk evidence.
- Focused and adjacent frontend contracts, build, review-gate, and reserved-port checks pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Keep 8911/5174/8910/4173 stopped; do not dispatch providers or start a browser/service.
- Preserve unrelated work: the read-only scan saw `services/api/app/medical_writing_authoring_prefill_ai.py`
  mtime `2026-08-04 16:00:49 +0800` before this slice; it is outside scope and was not modified.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 16:02:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
