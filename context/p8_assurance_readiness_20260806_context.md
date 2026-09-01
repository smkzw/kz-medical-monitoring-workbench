# Task Context: p8_assurance_readiness_20260806

Created: 2026-08-06 02:52:02
Objective: 在真实 LOOP 门禁保持 read_only/blocked 时，补齐医学监查 P8 锁库前/核查前保障工作区的只读 readiness 覆盖契约与可见状态，不启动运行时、不触碰 Safety/PV、B6/C14、真实项目或医学写作。
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringAssurance.mjs`, `medicalMonitoringAssuranceApi.mjs`, `medicalMonitoringAssuranceView.mjs`, `MedicalMonitoringAssurancePanel.jsx/.css` and their focused tests.
- Existing backend contract: `services/api/app/monitoring_assurance_router.py` readiness endpoint and `main.py` principal wiring; backend files are read-only inputs for this slice.
- Gate audit: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (`read_only / blocked`).
- Current filesystem is authoritative; no provider, service, browser, API login, runtime or real-project evidence may be inferred.

## Scope

- In scope: add a read-only frontend readiness input builder, strict response normalizer, API method, task-detail state and focused tests/styles.
- Out of scope: backend/schema changes, Safety/PV actions, B6/C14, source-token/CAS, runtime/SQLite, real projects, providers, browser/Playwright, medical-writing sources.

## Success Criteria

- Explicit subject/site coverage and task version are required; missing values remain visible blockers rather than implicit zeroes.
- Readiness response is project/task/version/mode/status/boolean validated before render.
- Request is principal-gated, project-scoped, cancellable and does not introduce client actor identity.
- Focused and adjacent offline tests plus Vite build pass; no protected boundary changes.

## Risk Boundaries

- This is a Codex direct patch; no delegated provider/subagent was dispatched. The guard route is recorded only for auditability.
- Do not start blocked runtime or write production/runtime paths; do not infer clinical, medical, browser or commercial acceptance.
- Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 02:52:02: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 02:56:00: Codex implemented the bounded P8 readiness slice; no route dispatch.
- 2026-08-06 02:58:00: 37 frontend Node test files, 116 assurance/identity Python tests and Vite build passed; runtime boundary rechecked.
