# Task Context: medical_monitoring_legacy_read_action_contract_20260804

Created: 2026-08-04 13:34:59
Objective: Define a route-free exact read-action contract for dashboard, workbench inbox and AI-run surfaces without opening fail-closed HTTP routes
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_identity_authorization.py`: principal, project scope and action ACL.
- `services/api/app/monitoring_runtime_principal.py` and `monitoring_runtime_route_context.py`: server-verified identity seam.
- `services/api/app/monitoring_authorized_route_context.py`: non-persisted authorization/audit handoff.
- `services/api/app/monitoring_audit_contract.py`: immutable hash-linked audit event and aggregate/CAS version fields.
- `services/api/app/main.py`: dashboard/inbox/AI-run routes, which currently use legacy policy-gap guards and must remain closed.
- Existing dashboard, inbox and source-registration policy-gap records plus the current P10/B6/C14 gates.

## Scope

- In scope: exact read actions/surface mapping and a pure immutable read-action handoff binding server principal, tenant/project scope, authorization decision, audit ID, source snapshot SHA-256, response snapshot SHA-256, idempotency key and non-mutating aggregate/CAS version.
- In scope: focused unit tests and compile/focused/adjacent verification.
- Out of scope: HTTP route activation, authentication middleware, frontend behavior, source registration, AI execution/provider calls, database/schema/migration, real projects, B6/C14, and reserved ports 8911/5174/8910/4173.

## Success Criteria

- Contract tests accept dashboard/inbox/AI catalog/detail/artifact reads and reject action/surface mismatch, denied or non-read decisions, tenant/project/principal/audit drift, non-SHA evidence, unsafe idempotency keys and mutation claims.
- Existing identity, audit and authorized-route tests remain green; review gate is `ok: true` with no warnings/errors; reserved ports stay stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 13:34:59: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Inventory confirmed generic `READ_MONITORING` is used by dashboard, inbox and AI-run GET routes, while those routes intentionally fail closed before source/service access. Existing route-context and audit contracts already bind identity and non-mutating audit state but lack surface-specific action and source/response digest binding.
- 2026-08-04: Added explicit surface actions and the route-free read handoff; focused (38), adjacent (29) and full monitoring (2035) tests passed. Hermes review-gate returned `ok=true` with no warnings/errors. HTTP routes remain closed; B6/C14 unchanged.
