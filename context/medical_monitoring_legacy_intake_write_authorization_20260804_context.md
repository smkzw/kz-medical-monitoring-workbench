# Task Context: medical_monitoring_legacy_intake_write_authorization_20260804

Created: 2026-08-04 03:04:36
Objective: 为 main.py 三个医学监查 intake 写入面绑定既有 INTAKE_BATCH 服务器 principal/ACL，并以服务器 actor 替换客户端 uploaded_by，保持其他批次生命周期写入不变
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

The read-side legacy monitoring surfaces are now principal-bound. The remaining
intake entry points have an exact existing `INTAKE_BATCH` action and can be
closed without inventing a role or policy. This slice covers only those three
intake writes and replaces client-supplied uploader identity with the verified
server actor.

## Source Of Truth

- `services/api/app/main.py` intake route definitions and existing
  `_authorize_legacy_monitoring_action` identity seam.
- `MonitoringAction.INTAKE_BATCH`, role matrix and runtime route-context
  contract in `monitoring_identity_authorization.py` and related modules.
- `monitoring_intake.py`, batch/source services, and affected API test suites.
- Closed B6/C14 gates under `runs/execution/` as recorded by prior slices.

## Scope

- In scope: authorize JSON intake, batch-file intake and intake-file upload
  routes with `INTAKE_BATCH`; perform identity check before intake/source
  lookup/body processing; use `principal.server_actor` for `uploaded_by` and
  downstream audit identity; update test clients and fail-closed tests.
- Out of scope: validation-evidence, confirm/verify, transition or other batch
  lifecycle writes; risk disposition/workbench writes; dashboard/inbox/AI
  legacy surfaces; new action/role, auth middleware/provider, frontend,
  DB/schema/migration, B6/C14, real projects or browser/provider login.

## Success Criteria

- Missing/invalid principal returns HTTP 503 before service/source/repository
  lookup for all three routes.
- A scoped medical-manager principal can run existing intake behavior and the
  server actor, not payload/query `uploaded_by`, is persisted into downstream
  audit/batch fields.
- Focused, adjacent and full monitoring suites pass; changed Python compiles;
  Hermes review-gate passes with verification required.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Do not infer authorization from payload actors, query actors, headers, cookies
  or test-only flags; do not add generic write action shortcuts.
- Do not change unrelated lifecycle writes; if an operation has no exact action
  it stays outside this slice and must be inventoried separately.
- No service/browser/provider/API login/runtime DB/real project/external agent.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 03:04:36: Task initialized by `tools/hermes_workflow_guard.py init-task`.
