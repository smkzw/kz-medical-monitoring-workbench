# Task Context: medical_monitoring_real_loop_batch_identity_20260802

Created: 2026-08-02 21:27:28
Objective: Require explicit distinct full-batch evidence in the three-project readiness contract so a scalar batch_count cannot satisfy the daily incremental gate
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

The readiness contract accepted a scalar `batch_count`, which could theoretically count one listing twice and satisfy the daily incremental gate without two independently traceable full snapshots.

## Source Of Truth

- `services/api/app/monitoring_real_loop_readiness.py` and its focused tests.
- `services/api/app/monitoring_real_loop_execution.py` consumer tests.
- Current `REAL_LOOP_READINESS.json` and P10 real-LOOP requirements.

## Scope

- In scope: add explicit batch identity/evidence rows, validate distinct references and listing SHA values, validate ISO snapshot dates and full-snapshot/source eligibility, and retain fail-closed authority boundaries.
- Out of scope: real source onboarding, runtime/SQLite/API/provider/service/browser/real-project execution, medical review or any product UI change.

## Success Criteria

- A ready synthetic manifest must provide at least two explicit `RealLoopBatch` rows per project.
- Scalar-only, duplicate, malformed, unproven or mismatched batch evidence must produce typed blockers.
- Existing complete synthetic readiness/execution fixtures remain valid after adding explicit batch rows.
- Focused tests, compile and Ruff pass; no authority flag becomes true.

## Risk Boundaries

- Only the readiness module, its tests and workbench evidence/context/review/metrics/ledger surfaces may change.
- The contract remains planning/preflight only and can never grant runtime, provider, write or medical confirmation authority.
- Codex handles directly; no Hermes dispatch or external provider is used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 21:27:28: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Added `RealLoopBatch`, explicit batch evidence validation and readiness-to-execution batch-ref binding; readiness/execution focused regression is 19 passed.
