# Task Context: medical_monitoring_primary_read_authorization_20260804

Created: 2026-08-04 00:49:42
Objective: 为医学监查主摘要、深链、当前风险快照、风险导出和风险分类读取面接入既有 READ_MONITORING 服务器 principal/ACL 边界，生产无 principal 继续 503
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_monitoring_router.py`: primary medical-monitoring
  route table and summary/risk projections.
- `services/api/app/monitoring_identity_authorization.py`,
  `monitoring_runtime_route_context.py`, `monitoring_runtime_principal.py` and
  `monitoring_principal_host_adapter.py`: existing verified-principal seam and
  `READ_MONITORING` action.
- `services/api/app/main.py`: production router wiring.
- `tests/test_medical_monitoring_module_contract.py`,
  `tests/test_medical_monitoring_risk_export.py` and related route tests:
  current offline harness semantics.
- Current filesystem and P10/B6/C14 gates are authoritative; no live service,
  browser, provider, API login or real project may be started.

## Scope

- In scope: add a provider-neutral server principal resolver and explicit
  production fail-closed switch to the medical-monitoring router; protect the
  module summary, deep-link, current risk snapshot, risk export and risk
  taxonomy reads with `READ_MONITORING` before data lookup. Summary uses the
  server-derived principal as its actor; client `actor` query text is ignored
  in production and retained only for the explicit offline harness.
- Add missing-principal, unauthorized-role, project-scope and scoped-medical-
  manager tests; preserve canonical project, query validation, 404/409 and
  export response contracts. Update only the five affected offline harness
  factories to opt out explicitly; production `main.py` opts in.
- Out of scope: protocol/rule-pack read/write surfaces, all authoring writes,
  auth/session middleware, IdP/JWT/cookie/header parsing, denied-attempt
  persistence, new ACL actions, frontend visual work, service/browser/provider
  login, runtime DB, B6/C14/approved-input gates and real projects.

## Success Criteria

- Every in-scope route invokes the server principal/ACL decision before its
  repository/summary/export lookup; absent or malformed identity returns 503,
  unauthorized role/scope returns 403, and a scoped medical manager retains
  existing 200/404/409 response semantics.
- Production never trusts the actor query field; no read route mutates state or
  accepts a client identity. Legacy tests remain explicit and green.
- Focused, adjacent and full monitoring tests, Ruff/py_compile and review-gate
  pass; reserved ports remain empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 00:49:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 00:50:xx: Inspected primary route table and found the five
  user-facing summary/risk reads had no server principal seam; protocol/rule
  reads are deliberately deferred to a later slice.
