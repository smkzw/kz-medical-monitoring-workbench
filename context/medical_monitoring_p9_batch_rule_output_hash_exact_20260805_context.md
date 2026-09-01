# Task Context: medical_monitoring_p9_batch_rule_output_hash_exact_20260805

Created: 2026-08-05 20:26:10
Objective: Reject non-canonical persisted batch-rule output hashes without string coercion
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_batch_rule_runner.py`, especially
  `BatchRuleRunResult.from_dict` and its persisted output identity check.
- `tests/test_monitoring_batch_rule_runner.py` plus adjacent daily-run resolver
  and repository tests.
- The active P9/P10 checkpoint, LOOP ledger and real-loop gate in this
  workbench; the gate remains read-only/blocked.

## Scope

- In scope: remove raw `output_sha256` string coercion at persisted batch-rule
  result restoration and add malformed numeric/uppercase/padded regressions.
- Out of scope: changing rule evaluation, output canonicalization, runtime
  activation, provider/browser/Playwright testing, real projects, or unrelated
  result field normalization.

## Success Criteria

- Persisted `output_sha256` must be a raw lowercase 64-hex string before the
  canonical output payload is rehashed.
- Existing round-trip, tamper, resolver and daily-run behavior remains green.
- Compile, Ruff, review-gate `--require-verification`, gate and reserved-port
  checks pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 20:26:10: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Source scan found `BatchRuleRunResult.from_dict` coercing
  persisted `output_sha256` with `str(...)` before comparing the output hash;
  this leaves the same raw-type boundary seen in adjacent P9 slices.
- 2026-08-05: Added raw canonical validation; 4 boundary, 97 focused, and 112
  adjacent tests passed; compileall and Ruff passed; Hermes review-gate with
  `--require-verification` passed. The formal gate remained blocked and all
  reserved ports remained empty.
