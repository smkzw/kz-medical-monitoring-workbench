# Task Context: medical_monitoring_ai_availability_copy_guard_20260804

Created: 2026-08-04 15:44:28
Objective: 使医学监查批次与字段映射工作区在独立AI不可运行时准确区分确定性技术字段路径与语义AI路径，并通过静态、回归、构建和门禁验证
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx`: project monitoring route and the global `/api/ai-gateway/status` state.
- `frontend/src/features/medical-monitoring/MedicalMonitoringBatchPanel.jsx`: batch-to-field-mapping entry copy and prop boundary.
- `frontend/src/features/medical-monitoring/MedicalMonitoringFieldMappingPanel.jsx`: field-mapping start/header/progress copy.
- `frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs`: normalized independent-AI readiness and shared mapping copy.
- `services/api/app/monitoring_ai_service.py`: deterministic metadata-only mapping path and semantic-AI runtime gate.
- Current gates: B6 `pending_review`, C14 `blocked_pending_b6_review`, real LOOP `blocked`; reserved ports 8911/5174/8910/4173 must stay stopped.
- No real project data, database, provider, runtime, browser, or medical-writing source is in scope.

## Scope

- In scope: pass the already-read normalized AI readiness into the monitoring batch and field-mapping panels; centralize truthful ready/unavailable copy; add static/unit assertions; record offline verification.
- Out of scope: API/server behavior, provider configuration, AI calls, database/runtime activation, real-project intake, mapping confirmation, medical conclusions, Playwright, visual acceptance, B6/C14 or commercial-release authority.

## Success Criteria

- Ready state preserves the AI-lead wording.
- Unready state never claims that independent AI will identify semantic fields; it explicitly distinguishes deterministic technical metadata handling from semantic fields that remain blocked.
- Existing project isolation and monitoring UI tests remain green; full frontend Node suites and Vite build pass.
- Hermes review-gate is `ok=true` with no warnings/errors; reserved ports remain stopped; no medical-writing file changes.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 15:44:28: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 15:45:00: Audited the backend deterministic-only mapping path and the global/raw monitoring AI status sources. Chose a shared copy helper plus prop threading; no runtime or provider action is required.
- 2026-08-04 15:53:00: Implemented the status-driven copy guard and passed focused checks, all 31 medical-monitoring Node suites, the 30-test frontend contract, Vite build and Hermes review-gate (`ok=true`). B6/C14 and real-loop boundaries remain unchanged.
