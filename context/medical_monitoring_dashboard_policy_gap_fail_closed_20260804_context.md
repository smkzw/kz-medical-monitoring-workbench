# Task Context: medical_monitoring_dashboard_policy_gap_fail_closed_20260804

Created: 2026-08-04 08:19:51
Objective: 为 canonical/reference 医学监查项目 dashboard HTTP 读取增加身份与项目范围校验及显式 policy-gap fail-closed，保护 user-created medical-writing 项目，完成聚焦/相邻/全量验证与 review-gate
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/main.py`: `_canonical_project_id`,
  `_reject_legacy_monitoring_read_policy_gap`, dashboard helpers and
  `GET /api/projects/{project_id}/dashboard`.
- `services/api/app/project_source_manifest.py`: canonical/reference versus
  user-created project classification.
- Dashboard API consumers and regressions in `tests/test_monitoring_risk_index_api.py`,
  `tests/test_rux_monitoring_service.py`, `tests/test_my009_monitoring_service.py`,
  `tests/test_contracts.py` and `tests/test_approval_center.py`.
- Prior LOOP 5.83/5.84 policy-gap records and the current P10/B6/C14 gates.
- Do not touch real project files, runtime databases, provider configuration or
  reserved service ports.

## Scope

- In scope: the legacy/reference-project dashboard HTTP GET boundary; perform
  server-principal and canonical-project-scope validation, then explicit
  `monitoring_read_action_unconfigured` denial before source/service/repository
  access while no exact dashboard read action exists. Add no new action/role.
- In scope: preserve user-created medical-writing project dashboard behavior,
  keep direct dashboard/service contracts available for unit assertions, and
  add no-principal/scoped-principal/no-service-call regressions.
- Out of scope: frontend redesign, new authorization actions or roles,
  dashboard service semantics, AI/source/inbox boundaries, DB/schema/migration,
  auth provider/middleware, browser/API login, external models, real projects,
  B6/C14 activation and 8911/5174/8910/4173 services.

## Success Criteria

- Reference/canonical dashboard GET returns 503 when the server principal is
  unavailable and 403 `monitoring_read_action_unconfigured` for a valid scoped
  principal, before dashboard/source/risk services are accessed.
- A user-created writing project is not incorrectly blocked by the legacy
  guard.
- Existing direct dashboard/service semantics remain covered, and focused,
  adjacent and full `tests/test_monitoring*.py` checks pass.
- Hermes `review-gate --require-verification` returns `ok: true` with no
  warnings/errors; reserved ports remain empty and B6/C14 stay closed.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 08:19:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Dashboard route inspection found the HTTP GET currently reaches
  RUX, MY009, demo repository and source-manifest summaries without the new
  legacy identity/policy-gap boundary. Existing dashboard tests that assert
  200 will be converted to direct service/helper assertions or explicit
  fail-closed checks; no dashboard semantics will be removed.
- 2026-08-04 implementation: `GET /api/projects/{project_id}/dashboard` now
  canonicalizes the project, preserves user-created writing projects, and for
  canonical/reference projects performs server-principal/project-scope
  validation followed by explicit `monitoring_read_action_unconfigured` 403
  before source, repository or monitoring-summary access. The shared error
  message was generalized from inbox-specific wording.
- 2026-08-04 focused regression: **72 passed, 19 existing warnings, 95.82s**.
  Adjacent suite first exposed one stale empty-project static assertion; the
  source already had the intended `unavailable` state, so the contract was
  updated and the rerun passed **71**, with **17 existing warnings, 1.45s**.
- 2026-08-04 full regression: clean `tests/test_monitoring*.py` passed
  **1949**, **25 warnings**, **484.72s**, exit code **0**. Log:
  `/private/tmp/medical_monitoring_dashboard_policy_gap_full_20260804.log`;
  exit code:
  `/private/tmp/medical_monitoring_dashboard_policy_gap_full_20260804.log.rc`.
- 2026-08-04: review-gate returned `{"ok": true, "warnings": [], "errors": []}`;
  LOOP 5.85 is closed. No services,
  browsers, providers, migrations, runtime DB writes, external agents, real
  projects or reserved ports were used.
