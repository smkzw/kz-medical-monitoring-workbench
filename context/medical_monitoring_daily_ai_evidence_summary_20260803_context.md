# Task Context: medical_monitoring_daily_ai_evidence_summary_20260803

Created: 2026-08-03 21:16:34
Objective: 在日常医学监查主流程中增加只读独立AI进度证据摘要，严格展示后端显式账本字段，不推导风险结论、不改变状态机
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_router.py::_ai_progress_dict` is the authoritative API shape for the independent-AI progress response.
- `services/api/app/monitoring_daily_run_ai_service.py::MonitoringDailyAiProgress` is the authoritative server-side ledger shape and status vocabulary.
- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyRunPanel.jsx` is the current read-only daily-run consumer and must remain the only integration surface for this slice.
- Existing focused model/component patterns in `medicalMonitoringDailyDiffView.mjs`, `MedicalMonitoringDailyDiffSummary.jsx`, and `medicalMonitoringAssuranceRemediation.mjs/.jsx` define the local strict-normalization and UI conventions.
- Current release gates remain authoritative: B6/C14 are blocked; no service, port, real project, browser login, or external test loop may be started in this slice.

## Scope

- In scope: a strict frontend normalizer and compact read-only card for explicit independent-AI progress fields (`status`, job counters, `candidate_count`, `failures`) plus explicit run/batch/rule-engine lineage already present in the run detail.
- In scope: focused Node assertions, the existing medical-monitoring Node regression set, Vite production build, static boundary review, and durable evidence records.
- Out of scope: backend/API changes, AI model execution, candidate promotion, risk calculation, status transitions, remediation writes, B6/C14 activation, real project onboarding, browser/Playwright acceptance, services, and external model dispatch.

## Success Criteria

- The card displays only values present and shape-valid in the API response; missing or malformed values remain `待核对` and create a visible partial/unavailable state.
- The UI explicitly says AI candidates are review clues, not confirmed medical risks, and exposes failure/incomplete counts without treating them as zero-risk.
- Focused tests, the full current frontend medical-monitoring Node suite, Vite build, and empty-port checks pass.
- A review-gate record and LOOP ledger entry capture hashes, evidence, scope, and remaining release blockers.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- No backend behavior or persisted state may change; this is a read-only consumer.
- Do not infer model quality, clinical severity, safety signals, or completeness from counts or status.
- The delegated-agent route is not used; Codex is implementing and remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 21:16:34: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 21:21:46: Codex completed the read-only AI progress consumer, focused/full tests, build and static boundary checks; no external route was dispatched.
- 2026-08-03 21:29:00: Codex completed the read-only daily-run step ledger consumer, focused/full tests, build and static boundary checks; no external route was dispatched.
