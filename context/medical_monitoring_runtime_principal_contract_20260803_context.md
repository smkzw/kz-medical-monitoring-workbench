# Task Context: medical_monitoring_runtime_principal_contract_20260803

Created: 2026-08-03 14:50:46
Objective: Implement and verify a provider-neutral server-verified monitoring principal envelope without wiring routes or mutating runtime
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

Phase G identity review found that the existing monitoring authorization model is offline
only and that API/frontend writes still accept a role-like client actor. The existing
medical-writing principal ACL was inspected as a local design reference; it was not edited.

## Source Of Truth

- `services/api/app/monitoring_identity_authorization.py`
- `services/api/app/monitoring_audit_contract.py`
- `services/api/app/medical_writing_principal_acl.py` (reference only)
- `context/medical_monitoring_identity_boundary_audit_20260803_context.md`
- B6/C14 gate JSON and `context/medical_monitoring_offline_boundary_checkpoint_20260803.md`

## Scope

- In scope: a provider-neutral, server-verified principal envelope; validity window;
  explicit project/role scope; session/verification hashes; server-derived actor helper;
  focused negative tests; full monitoring regression.
- Out of scope: token/cookie/header parsing; FastAPI dependency wiring; real auth provider;
  router writes; B6/C14, CAS/source-token operations; service/browser/provider/API login;
  real projects; medical-writing source changes.

## Success Criteria

- A future route can consume an explicit verified envelope without trusting client actor.
- Invalid/unverified/expired/not-yet-valid/wildcard/forged-actor inputs fail closed.
- Existing identity, audit and all monitoring tests remain green.
- The contract is documented as non-runtime and not commercial acceptance evidence.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 14:50:46: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Direct Codex implemented `monitoring_runtime_principal.py` and its focused
  tests; no delegated route was dispatched.
- 2026-08-03: Focused 7, identity/audit 24, and latest full monitoring 1826 tests passed;
  25 existing warnings were retained in 473.99s. `compileall` and `python -m ruff` passed.
