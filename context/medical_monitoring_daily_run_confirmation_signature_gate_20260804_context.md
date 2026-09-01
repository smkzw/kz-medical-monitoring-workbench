# Task Context: medical_monitoring_daily_run_confirmation_signature_gate_20260804

Created: 2026-08-04 00:37:17
Objective: 为日常增量运行 confirm 基线动作加入显式 reauthentication 与 signature evidence SHA-256 门槛，生产无 verified principal 或证据不全继续 fail-closed，不接入认证供应商
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_router.py`: current daily-run write
  authorization and confirm route.
- `services/api/app/monitoring_identity_authorization.py`: existing
  `CHANGE_RISK_DISPOSITION` high-risk reauthentication/signature decision.
- `services/api/app/monitoring_runtime_route_context.py` and
  `services/api/app/monitoring_runtime_principal.py`: request contract and
  SHA-256 evidence validation; no provider verifies the evidence yet.
- `tests/test_monitoring_daily_run_router.py`: daily-run route boundary tests.
- Current filesystem and P10/B6/C14 gates are authoritative; no live service,
  browser, provider, API login or real project may be started.

## Scope

- In scope: add explicit `reauthenticated` and `signature_evidence_sha256`
  fields to `MonitoringDailyRunConfirmRequest`; pass them as a high-risk
  `CHANGE_RISK_DISPOSITION` authorization request; reject incomplete or
  malformed evidence before repository baseline mutation; preserve the
  existing CAS/baseline conflict contract and explicit offline harness bypass.
- Add tests for missing principal, unauthorized role, missing reauthentication,
  missing signature, malformed signature and a fully supplied evidence request
  reaching the existing 404/normal path.
- Out of scope: authenticating the user, validating the signature with an IdP or
  e-signature provider, storing signature material, audit schema changes,
  frontend redesign, all other daily-run routes, B6/C14/approved-input gates,
  service/browser/provider login, runtime DB and real projects.

## Success Criteria

- A production confirm request without reauth or a lowercase 64-character
  SHA-256 evidence value is rejected with the existing ACL reason before
  repository lookup/mutation; no client actor is accepted as identity.
- With a verified medical manager, both explicit reauthentication and valid
  evidence hash reach the downstream route (including its existing 404/409
  semantics); the evidence hash is only a contract token, not proof of a real
  external signature.
- Legacy offline tests continue to pass through their explicit factory bypass;
  focused, adjacent and full monitoring tests plus Ruff/py_compile and
  review-gate pass. Reserved ports remain empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 00:37:17: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 00:38:xx: Confirm route and existing high-risk ACL semantics were
  inspected; this slice will add only the request gate, not a provider or
  signature verifier.
