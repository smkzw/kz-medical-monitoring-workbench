# Codex Review: medical_monitoring_legacy_intake_write_authorization_20260804

Date: 2026-08-04 (Asia/Shanghai)
Delegated-agent output: `runs/codex_medical_monitoring_legacy_intake_write_authorization_20260804.md`

## Verdict

**PASS — direct Codex implementation and verification complete.** The three
legacy intake writes use the exact existing `INTAKE_BATCH` action; missing
server identity remains fail-closed and the server principal owns uploader
identity.

## Boundary Check

- Work is limited to the workbench; direct Codex only, no external agent.
- Only the three intake writes are in scope; lifecycle writes remain unchanged.
- No authentication provider, middleware, schema, migration, runtime or
  production service was started.

## Codex Verification

- `main.py` uses `_authorize_legacy_monitoring_action(..., write=True,
  action=INTAKE_BATCH)` before source/body/service work for JSON intake,
  batch-file intake and intake-file upload.
- JSON/file intake replaces payload/query `uploaded_by` with
  `principal.server_actor`; a focused test asserts the downstream request
  receives the verified actor.
- Focused intake/real-project/source-validation suite: **30 passed, 18
  existing warnings**.
- Integrated batch/contract/RUX/intake/source-validation suite: **69 passed,
  18 existing warnings**.
- Full `tests/test_monitoring*.py`: **1938 passed, 25 existing warnings in
  498.72s**, exit code 0.
- `python -m py_compile` passed for `main.py` and changed test modules.
- Hermes workflow guard review-gate with `--require-verification` is the final
  required check; browser/live checks are not applicable while P10/B6/C14
  remain closed.

## Delegated-Agent Output Review

No delegated-agent output was used; Codex remains final authority. The exact
existing role/action matrix was reused; no generic action shortcut, client
actor fallback, new action or unrelated batch lifecycle/write surface was
introduced.

## Residual Risk

The host principal/session middleware remains absent, so production intake
writes intentionally return 503 until an approved upstream adapter populates
`request.state.monitoring_principal`. Validation/confirm/verify/transition
writes, dispositions, dashboard/inbox/AI legacy surfaces and B6/C14/real-loop
gates remain outside this slice.
