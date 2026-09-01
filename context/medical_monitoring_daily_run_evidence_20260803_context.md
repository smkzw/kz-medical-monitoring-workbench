# Task Context: medical_monitoring_daily_run_evidence_20260803

Created: 2026-08-03 21:28:43
Objective: 在日常医学监查主流程中增加只读步骤账本摘要，严格展示显式步骤状态、尝试次数和输出证据，不改变状态机
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_router.py::_step_dict` is the authoritative API serializer for `detail.steps`.
- `services/api/app/monitoring_daily_run_repository.py::MonitoringDailyRunStep` defines the durable step fields and status vocabulary.
- `services/api/app/monitoring_daily_run_service.py` and `monitoring_daily_run_analysis_service.py` define the five standard step names and their explicit details.
- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyRunPanel.jsx` is the single integration surface for this read-only consumer.

## Scope

- In scope: strict normalization and compact rendering of standard step status, attempt count, update time, input/output hash binding and selected explicit detail fields.
- In scope: baseline/diff alternative semantics, malformed/duplicate/unknown step warnings, focused/full frontend regression, Vite build and static boundary review.
- Out of scope: backend/API/state-machine changes, retries, status transitions, step writes, B6/C14 activation, services, real projects, browser/Playwright/scientific/UAT and external models.

## Success Criteria

- Existing explicit steps are shown in stable workflow order; absent steps are not presented as complete.
- Initial baseline and batch diff are represented as an explicit alternative, not as a false missing-step failure.
- Missing/invalid attempt/timestamp/hash/detail fields stay visible as `待核对` and generate a partial warning.
- Focused tests, all current medical-monitoring Node tests, Vite build, empty ports, review-gate and durable evidence pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- No status is inferred from row order, missing fields or UI position; no step is upgraded to completed by the consumer.
- No backend, runtime, project, clinical, risk or authority state may change.
- No delegated route is used; Codex implements and remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 21:28:43: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 21:29:00: Codex completed the bounded step-ledger consumer and deterministic verification without external dispatch.
