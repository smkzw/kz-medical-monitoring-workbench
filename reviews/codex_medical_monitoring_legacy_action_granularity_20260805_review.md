# Codex Review: medical_monitoring_legacy_action_granularity_20260805

Date: 2026-08-05
Route: direct Codex (codex-main / high); no delegated model output was used.

## Verdict

Pass for the declared source-only slice. The legacy monitoring risk, workbench
inbox, and AI read seams now select the existing exact READ_* actions, and
the new regression tests prove role rejection before backing service access.
This is not a runtime, medical, real-project, or commercial release approval.

## Boundary Check

- Changed source: services/api/app/main.py.
- Changed regression surface: tests/test_monitoring_risk_index_api.py.
- Added only task-scoped context/evidence/review/metrics and LOOP records.
- No action ACL membership, medical fact/disposition, batch/source identity,
  request schema, persistence, runtime database, frontend, or medical-writing
  surface was changed.
- No service, browser/Playwright/API login, provider/external model, real
  project, or 8911/5174/8910/4173 listener was started.

## Codex Verification

- Hermes workflow guard review-gate is the required task-record validator;
  the first pass correctly flagged the missing literal route marker, which is
  now recorded here and rechecked below.
- Focused read-action/identity/risk suite: 42 passed, 17 warnings.
- Adjacent monitoring/API/AI/batch/identity suite: 88 passed, 17 warnings.
- Full tests/test_monitoring_*.py: 2550 passed, 25 warnings in
  1084.05s (0:18:04), exit code 0.
- python -m compileall -q for the changed source and test: passed.
- Scoped Ruff for the changed test: passed. System Ruff reports 118
  pre-existing baseline findings in main.py (historic E402/F401/F841);
  those were not changed or treated as regressions.
- Direct listener checks: 8911, 5174, 8910 and 4173 all stopped.
- Authoritative real-loop gate remains read_only / blocked; activation,
  provider, runtime and write authority remain false.

## Implementation Review

Risk catalog/index/history/evidence reads bind READ_RISK_AUDIT; the legacy
workbench inbox binds READ_WORKBENCH_INBOX; legacy AI run catalog/detail binds
READ_AI_RUN; and AI artifacts bind READ_AI_ARTIFACT. Existing explicit
policy-gap responses remain fail-closed. A medical-writer principal is rejected
before risk/inbox/artifact service access, while the manager path and prior
409/403 contracts remain covered by the full regression.

## Residual Risk

The current gate still requires five formal hash-bound B6 reviewer outcomes,
source-token byte lineage, aggregate/CAS expected-version revalidation,
approved-input and controlled-runtime authorization, then the serial
five-project Playwright/scientific/UAT loop and commercial dossier. None of
those claims is made by this source slice.

## Next Safe Action

Keep 8911/5174/8910/4173 and all runtime/provider/browser activity stopped.
After formal reviewer outcomes are authorized, revalidate the source-token and
CAS evidence before any controlled activation or real-project loop.

## Hermes Review-Gate

Run after this record was completed: ok=true with no warnings. The gate
validates record completeness only and does not authorize runtime activation.
