# Task Context: medical_monitoring_p9_daily_rule_binding_raw_hash_20260805

Created: 2026-08-05 20:17:19
Objective: Reject non-canonical persisted daily-run record-rule binding hashes without string coercion
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_repository.py`, especially
  `_validate_record_rule_snapshot_payload` and `save_rule_snapshot`.
- `tests/test_monitoring_record_rule_resolver.py` and
  `tests/test_monitoring_daily_run_repository.py` for record-applicability
  snapshot validation and persistence behavior.
- The active P9 gate and prior checkpoint/LOOP ledger in this workbench.
- No production paths, services, providers, browsers, or real study projects
  are in scope while the formal real-loop gate remains blocked.

## Scope

- In scope: remove string coercion from the four persisted SHA-256 fields at
  the record-applicability daily-run snapshot boundary and add regression
  coverage proving non-string values fail closed.
- Out of scope: changing snapshot identity semantics, runtime activation,
  provider calls, browser/Playwright testing, real projects, or unrelated hash
  validators.

## Success Criteria

- Mapping and rule-pack content hashes are passed to the strict raw SHA-256
  validator without `str(...)` coercion.
- Focused tests prove malformed non-string mapping and binding hash values are
  rejected with the existing controlled conflict/error boundary.
- Adjacent daily-run service/API/readiness tests and compilation pass.
- Review gate with `--require-verification` and the active-gate/port checks pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 20:17:19: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Source audit found four `str(...)` wrappers around persisted
  record-applicability SHA-256 fields; the strict validator already rejects
  non-string raw values, so the bounded repair is to remove those wrappers and
  test both mapping and binding boundaries.
- 2026-08-05: Removed the four coercions; 3 boundary, 71 focused, and 112
  adjacent tests passed; compileall and ruff passed; Hermes review-gate with
  `--require-verification` passed. The formal gate stayed read-only/blocked and
  all four reserved ports stayed empty.
