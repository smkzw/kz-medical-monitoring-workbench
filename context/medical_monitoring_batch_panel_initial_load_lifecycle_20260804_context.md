# Task Context: medical_monitoring_batch_panel_initial_load_lifecycle_20260804

Created: 2026-08-04 20:38:19
Objective: Fix the medical-monitoring batch panel initial-load request lifecycle so the real user-facing panel cannot leave its busy state stuck after a successful or failed load; preserve project-bound cancellation and fail-closed behavior.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/frontend/src/features/medical-monitoring/MedicalMonitoringBatchPanel.jsx` — real batch workspace lifecycle.
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/frontend/src/features/medical-monitoring/medicalMonitoringProjectRequestScope.mjs` — project-bound request cancellation contract.
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/tests/test_frontend_monitoring_contract.py` — static product contract tests.
- Current filesystem and the workbench AGENTS files are authoritative; no runtime, service, browser, provider, or real-project evidence is in scope while B6/C14 remain closed.

## Scope

- In scope: remove the duplicate initial request slot in the batch panel's first-load effect; keep the shared `batch-view` slot, project-bound abort on unmount, and existing error/fail-closed handling; add a focused source contract.
- Out of scope: API/service behavior, B6/C14 state, source-token/CAS/approved-input evidence, runtime/provider/browser/Playwright, real projects, databases, and medical-writing files.

## Success Criteria

- Initial load uses the same request slot as `loadBatches`, so a successful or failed load always clears `busy`.
- Unmount cancels the project-bound `batch-view` request and cannot permit a stale response to update the panel.
- Focused static contract and frontend build pass; existing monitoring frontend tests remain green.
- No authority flag, runtime gate, service, port, or protected subsystem changes.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 20:38:19: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Source-only lifecycle patch applied; focused and adjacent frontend contracts plus build passed; review-gate passed; no runtime or gate state changed.
