# Task Context: medical_monitoring_frontend_principal_gate_20260803

Created: 2026-08-03 15:20:29
Objective: Expose a strict server-authenticated monitoring principal contract and fail-closed Assurance task-creation gate without wiring runtime auth
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

Phase G identity-boundary follow-up: the Assurance UI previously treated a frozen
identity plus `assurance_write_permitted` as sufficient to expose creation. The
server-derived principal contract now exists offline, so the user-facing creation
gate must visibly require that contract without pretending that runtime auth is wired.

## Source Of Truth

- `frontend/src/features/medical-monitoring/MedicalMonitoringAssurancePanel.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringPrincipal.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringPrincipal.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Existing offline identity contract: `services/api/app/monitoring_runtime_principal.py`
- B6/C14 gate JSON and the P10 LOOP ledger remain authoritative for runtime/write boundaries.

## Scope

- In scope: strict normalization of a server-verified `monitoring_principal`, project-scope and
  validity checks, visible Assurance identity status/blocker, and regression/build evidence.
- Out of scope: token/cookie/header parsing, provider/IdP integration, FastAPI route wiring,
  actor replacement, audit persistence, service/browser/API login, B6/C14 mutation and real projects.

## Success Criteria

- A malformed, unverified, expired, unauthenticated, wildcard or wrong-project principal fails
  closed in the frontend contract.
- Assurance task creation requires complete frozen identity, explicit authority and a currently
  valid server principal; the current runtime has no principal, so creation remains blocked.
- The user sees the principal state and a Chinese blocker rather than mistaking authority for identity.
- Focused and complete frontend tests, static contract checks and Vite build pass; no runtime writes occur.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- A frontend principal summary is a display/UX gate only; the eventual API route must independently
  verify the same envelope and derive the actor server-side.
- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated-agent route was recorded for traceability but not dispatched; Codex owns verification.

## Verification

- Principal focused Node test: 15 passed.
- Complete discovered frontend Node suite: 29 subtests/files passed.
- Frontend monitoring static contract pytest: 28 passed; Ruff passed.
- Vite production build: 1927 modules transformed; existing large-chunk advisory only.
- No service/provider/browser/API login, runtime database, B6/C14 action or real project ran.

## Loop Log

- 2026-08-03 15:20:29: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Added strict principal normalizer, expiry-aware visible gate and regression contracts;
  the current no-principal runtime remains fail-closed.
