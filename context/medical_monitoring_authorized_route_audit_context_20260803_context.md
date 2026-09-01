# Task Context: medical_monitoring_authorized_route_audit_context_20260803

Created: 2026-08-03 15:59:26
Objective: 将 server-derived monitoring route context 绑定现有 identity authorization decision 与 hash-bound audit event，形成纯离线、不可写入、可审计的 Phase G 路由决策上下文；不改变旧路由、不越过 B6/C14、不启动服务/浏览器/provider/真实项目。
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_runtime_route_context.py`
- `services/api/app/monitoring_identity_authorization.py`
- `services/api/app/monitoring_audit_contract.py`
- `tests/test_monitoring_runtime_route_context.py`
- `tests/test_monitoring_identity_authorization.py`
- `tests/test_monitoring_audit_contract.py`
- Current P10 checkpoint and B6/C14 gate files. These remain boundary evidence only.

## Scope

- In scope: add one pure in-memory authorized route context; convert a verified runtime
  principal to the existing ACL snapshot; evaluate the canonical request; create a
  non-mutating hash-bound audit event; add focused regression and task evidence.
- Out of scope: FastAPI dependency/provider wiring, token/cookie/header parsing, route
  mutation, SQLite/CAS/source admission, e-sign persistence, B6/C14 outcome, browser,
  provider, real project, frontend or medical-writing changes.

## Success Criteria

- A server-bound route context produces a decision and a hash-bound audit event that
  agree on principal, project, action and status.
- Allowed write actions remain explicitly non-executing: no mutation, no aggregate version
  advance, no persistence and a separate `execution_write_permitted=false` signal.
- Denied actions remain auditable; client actor, malformed identity, missing source/audit
  binding and sensitive payloads fail closed.
- Focused/adjacent tests, compile and Ruff pass; B6/C14 and 8911/5174 are unchanged.

## Risk Boundaries

- This is a provider-neutral, diagnostic-only handoff; it cannot authenticate a caller,
  persist an audit event, grant runtime write permission or replace the pending B6 gate.
- Do not wire the existing assurance route or remove its transitional actor until a real
  session provider and the formal B6 → source-token/CAS → approved-input chain are ready.
- Do not start 8911/5174, a service, provider, browser/API login or real project.
- Do not touch medical-writing sources.
- Do not write to production paths until the Codex review gate passes and paths are explicit.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 15:59:26: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Reused existing identity/ACL/audit contracts; no external dependency or
  web discovery was needed because the selected route is a local provider-neutral seam.
- 2026-08-03: Added `monitoring_authorized_route_context.py` and focused tests. The builder
  converts only a live server principal in memory, evaluates authorization and creates a
  non-mutating audit event; it never calls a repository or runtime.
- 2026-08-03: Focused route/identity/authorization/audit regression passed **40 tests**;
  full `tests/test_monitoring_*.py` passed **1842 tests with 25 existing warnings in
  498.95s**; compile and Ruff passed. Review-gate is the remaining record check.
