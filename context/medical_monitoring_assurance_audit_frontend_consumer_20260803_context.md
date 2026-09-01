# Task Context: medical_monitoring_assurance_audit_frontend_consumer_20260803

Created: 2026-08-03 23:30:52
Objective: 将已验证身份保护的医学监查保障审计链只读消费接入现有前端保障面板，明确加载、空链、身份阻断和读取失败状态，不创建登录或写入回退
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringAssuranceApi.mjs`:
  existing project-scoped assurance API factory and error contract.
- `frontend/src/features/medical-monitoring/medicalMonitoringAssuranceView.mjs`:
  strict project/task/evidence response normalizers.
- `frontend/src/features/medical-monitoring/MedicalMonitoringAssurancePanel.jsx`
  and `.css`: current desktop-first assurance workbench and request-scope
  lifecycle.
- `services/api/app/monitoring_assurance_router.py`: the verified-principal
  `READ_RISK_AUDIT` route and safe public audit event shape.
- `frontend/src/features/medical-monitoring/medicalMonitoringPrincipal.mjs`:
  frontend representation of a server-verified, project-scoped principal.

## Scope

- In scope: add a project/task-scoped `getAudit` API helper; strictly normalize
  the public audit response; fetch it only for the selected task when the
  frontend has a valid project-scoped server principal; render a compact audit
  chain block with loading, empty, identity-blocked, read-failure and success
  states; add focused Node/static contract coverage and styling that preserves
  desktop density and avoids page overflow.
- Out of scope: authentication/session middleware, creating or refreshing
  identities, client headers/tokens/cookies, task/audit writes, denied-attempt
  persistence, backend schema/routes, source/clinical data, App-wide refactor,
  service/browser/provider/real-project runs and B6/C14 or approved-input
  gates.

## Success Criteria

- The API path exactly matches `GET
  /api/projects/{project_id}/monitoring/assurance/tasks/{task_id}/audit`, with
  project/task encoding and caller-provided cancellation signal.
- A malformed, cross-project, cross-task or unsafe audit payload is rejected
  before React state commit; raw session material is not rendered.
- Without a valid principal the panel clearly says audit reading is blocked by
  server identity, rather than showing a false empty chain or silently retrying.
- A 503/403/read failure is visible but does not erase already validated task
  and evidence detail; a valid response shows ordered event action/time/version
  and truncated hash evidence without mutation controls.
- Existing assurance and frontend contract suites plus Vite build remain green;
  no service/browser/provider/real-project process is started.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- The frontend is not permitted to infer `principal_id`, manufacture a read
  permission, call the route with a client actor, or treat 503 as an empty
  audit chain.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 23:30:52: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 23:31:xx: Reopened frontend AGENTS.md, assurance API/panel/view/
  principal contracts and backend public audit route. Selected the smallest
  read-only consumer slice; no live runtime action is allowed.
