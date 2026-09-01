# Task Context: medical_monitoring_risk_snapshot_integrity_revalidation_20260805

Created: 2026-08-05 01:49:16
Objective: Revalidate persisted medical risk snapshot payload hash and instance identity on reads
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_risk_repository.py`
- `tests/test_medical_risk_repository.py`
- adjacent risk projection, consumer handoff, assurance and module-contract
  tests
- current P10 completion matrix and release gate audit

## Scope

- In scope: on snapshot/current/history/instance reads, validate deterministic
  snapshot identity, resolution metadata, instance row-to-payload identity and
  the stored semantic payload hash; add persisted risk tamper regressions.
- Out of scope: medical inference, runtime startup, provider/browser/Playwright,
  real projects, B6/C14, schema migration, UI or medical-writing files.

## Success Criteria

- A semantically valid but tampered persisted risk payload or instance metadata
  cannot be returned to consumers or downstream assurance.
- Existing batch-delta/history, snapshot idempotency and boolean contracts
  remain precise; focused/adjacent tests, compile and Ruff pass.
- No authority or activation flag changes.

## Risk Boundaries

- Do not start or connect to 8911, 5174, 8910 or 4173; do not touch runtime
  databases or real projects.
- No provider or external model dispatch; Codex remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 01:49:16: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 01:50: source audit found risk snapshot reads trusted stored
  `payload_hash` and instance JSON without revalidation; runtime/provider gates
  remain closed.
- 2026-08-05: added read-side snapshot/instance identity and semantic-payload
  hash revalidation, plus persisted payload/row tamper regressions.
- 2026-08-05: focused 23 and adjacent 137 tests passed; compileall, Ruff and
  reserved-port checks passed. No provider/runtime/browser/real-project/B6/C14
  action occurred. Continue with a bounded source-only P7/P8/P9 gap.
