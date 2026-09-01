# Codex Review: medical_monitoring_legacy_risk_read_authorization_20260804

Date: 2026-08-04 (Asia/Shanghai)
Delegated-agent output: `runs/codex_medical_monitoring_legacy_risk_read_authorization_20260804.md`

## Verdict

**PASS — direct Codex implementation and verification complete.** The five
legacy reads now use the existing `READ_MONITORING` server-principal/ACL seam;
production remains fail-closed when no host principal exists. No B6/C14 gate
was changed or bypassed.

## Boundary Check

- Work stayed inside `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- No service, browser, provider, API login, runtime database, migration, real
  project, or external agent was started.
- Production changes were limited to the legacy read authorization seam and
  tests needed to model a verified, explicitly scoped principal. The
  subject-profile, dashboard, batch/intake, AI legacy, and disposition-write
  routes were not changed in this slice.
- The runner-managed report path was not written by tools; this review and the
  task records are the durable local evidence.

## Codex Verification

- `main.py` contains one shared `_authorize_legacy_monitoring_action` helper
  that reads only `request.state.monitoring_principal`, builds the existing
  runtime route context, evaluates `READ_MONITORING`, and maps identity/ACL
  failures to 401/403/503 without a client actor fallback.
- The five route handlers call the helper before registry/repository lookup:
  `monitoring/subjects`, `monitoring/risks`, risk history,
  risk evidence-fragment, and `monitoring/raw-intake`.
- A dedicated regression calls all five without a principal and observes HTTP
  503 with `monitoring_principal_unavailable`; the authorized real-project
  tests use only a test-server session principal scoped to the project.
- `python -m py_compile` passed for `main.py` and all changed test modules.
- Focused risk-index/legacy boundary: **3 passed**.
- Identity/runtime/authorization adjacent suite: **68 passed**.
- Real-project and frontend consumer adjacent suite: **129 passed, 20
  existing warnings**.
- Full `tests/test_monitoring*.py`: **1937 passed, 25 existing warnings in
  511.44s**, exit code 0.
- No browser/runtime visual check was run because the upstream P10/B6/C14 and
  real-loop gates remain closed and ports 8911/5174/8910/4173 must remain
  stopped.

## Delegated-Agent Output Review

No delegated-agent output was used. This was a bounded direct Codex slice; the
Hermes workflow guard was used only for task initialization and final
verification gate, not for external execution.
The implementation is traceable to the existing host adapter, runtime route
context, and ACL action; test-only middleware places the same principal in
ASGI `scope["state"]` and does not alter production code. The adjacent test
failures initially observed were the expected old no-auth harness calls; they
were corrected by explicit principal injection rather than weakening the
boundary. No unsupported completion claim is made for the untouched legacy
surfaces or for commercial/UAT readiness.

## Residual Risk

- The host/session authentication middleware that should populate
  `request.state.monitoring_principal` is still absent; production reads remain
  intentionally 503 until an approved upstream adapter is installed.
- `GET /api/projects/{project_id}/subjects/{subject_id}/monitoring`, dashboard,
  batch/intake, AI legacy surfaces, and direct disposition writes still require
  separate inventory/slices; this record does not claim they are protected.
- B6 remains `pending_review` and C14 remains `blocked_pending_b6_review`; no
  formal review outcome, aggregate/CAS replay, source-token validation, or
  real-project Playwright loop was performed.
- The full suite retains the same 25 deprecation/source-parser warnings; they
  are not new failures from this slice.
