# Task Context: medical_monitoring_daily_ai_candidate_preview_20260803

Created: 2026-08-03 21:31:50
Objective: 在日常医学监查运行中只读展示 source-bound AI 候选线索及声明证据/置信度摘要，不改变候选或风险状态机
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_analysis_service.py::MonitoringDailyAiProgress` is the authoritative in-memory progress shape.
- `services/api/app/monitoring_daily_run_router.py::_ai_progress_dict` is the daily-run response serializer; generic `monitoring_ai_router.py::_public_candidate` is the existing public source-bound candidate contract.
- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyRunPanel.jsx` and `medicalMonitoringDailyAiEvidence.mjs` are the current consumer and progress model.
- B6/C14 and real-loop release artifacts remain authoritative blockers; no runtime or real project may be started in this slice.

## Scope

- In scope: expose existing source-bound candidates in the read-only daily-run AI progress response and render a compact preview with explicit claims/evidence/locator/confidence state.
- In scope: backend route regression, strict frontend normalization, full frontend regression, Vite build, static boundary review and durable evidence.
- Out of scope: candidate decision endpoints, accept/reject controls, promotion to risk, risk/disposition writes, new AI jobs, backend state transitions, B6/C14 activation, services, browser/Playwright/scientific/UAT and external models.

## Success Criteria

- The daily-run response reuses the existing public candidate shape and adds no write behavior.
- The UI verifies candidate/source input revision binding, source content hashes, locator, claim/evidence graph and confidence summary; malformed or missing data remains visible as partial/unavailable.
- The UI explicitly labels candidates as review clues requiring user confirmation and never treats them as confirmed risks or no-risk evidence.
- Focused/backend/full frontend tests, Vite build, ruff, syntax, empty ports, review-gate and records pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Candidate projection is GET/read-only; no accept, reject, retry, assemble, transition or disposition action is exposed by this slice.
- Do not infer candidate severity, clinical correctness, source authenticity, no-risk or automation permission from text, order or count.
- No external/delegated route is used; Codex implements and remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 21:31:50: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 21:40:00: Codex completed the read-only candidate projection/preview, focused/backend/frontend/build checks and static boundary review without external dispatch.
