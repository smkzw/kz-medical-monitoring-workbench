# Task Context: medical_monitoring_legacy_risk_read_authorization_20260804

Created: 2026-08-04 02:09:01
Objective: 为 main.py 旧版医学监查 subjects、risks、history、evidence-fragment、raw-intake 五个读取面接入现有 READ_MONITORING 服务器 principal/ACL，保留 dashboard/批次/AI 旧面不变
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

The previous identity-boundary slices protected the assurance, daily-run, primary
module, protocol/rule and exact write routes, but the legacy direct `main.py`
read surfaces still bypassed the shared server-principal/ACL boundary. This
slice closes only the five legacy risk/data reads named below; it does not
activate B6/C14 or introduce an authentication provider.

## Source Of Truth

- `services/api/app/main.py` legacy route definitions and shared monitoring
  authorization imports.
- `services/api/app/monitoring_identity_authorization.py`,
  `monitoring_runtime_principal.py`, `monitoring_runtime_route_context.py`, and
  `monitoring_principal_host_adapter.py` as the existing identity/ACL seams.
- `tests/test_monitoring_risk_index_api.py` plus the real-project consumer
  suites listed in the validation record.
- Upstream gates, which remain unchanged and closed:
  `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json`
  (`pending_review`) and
  `runs/execution/medical_monitoring_phase_c14_b6_activation_gate_20260802/B6_TO_C13_ACTIVATION_GATE_REPORT.json`
  (`blocked_pending_b6_review`).

## Scope

- In scope: require `READ_MONITORING` using the host-provided verified
  principal for `GET /monitoring/subjects`, `GET /monitoring/risks`, risk
  history, risk evidence-fragment, and `GET /monitoring/raw-intake`; preserve
  canonical project resolution and downstream read behavior; update affected
  test harnesses to inject an explicit project-scoped test principal; add a
  no-principal fail-closed regression.
- Out of scope: subject profile route, dashboard, monitoring batches/intake,
  AI legacy surfaces, direct disposition writes, auth/session middleware,
  provider/token parsing, frontend, database/schema/migration, B6/C14,
  approved-input or real-project LOOP, service/browser/provider login, and
  changes outside the workbench.

## Success Criteria

- All five named legacy reads reject a missing server principal with HTTP 503
  and `monitoring_principal_unavailable` before repository/service lookup.
- A valid verified medical-manager principal scoped to the canonical project can
  reach the existing read behavior without client actor fallback or private
  path leakage.
- Focused, adjacent, and full monitoring regression suites pass; source files
  compile; review-gate passes with verification required.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Do not relax production fail-closed behavior to make legacy tests pass.
- Do not infer authentication from headers, cookies, query parameters, payload
  actors, or test-only client state in production.
- The task is direct Codex work; no external agent, provider, browser, service,
  runtime database, or real clinical project is used.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 02:09:01: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Added `_authorize_legacy_monitoring_action` in `main.py`, bound
  the five named reads to `READ_MONITORING`, and preserved the older unscoped
  routes for a later explicit slice.
- 2026-08-04: Updated real-project API tests to inject a server-state
  `MonitoringAuthenticatedPrincipal` with explicit project scope; no production
  middleware was added.
- 2026-08-04: Added a five-route no-principal 503 regression and ran focused,
  adjacent, and full monitoring suites; all passed. See the slice record and
  `TEST_EVIDENCE.md` for exact counts.
