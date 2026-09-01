# Task Context: medical_monitoring_p9_record_aggregate_hash_exact_20260805

Created: 2026-08-05 20:22:15
Objective: Reject non-canonical record-rule aggregate identity hashes before constructing the frozen aggregate
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_record_rule_resolver.py`, especially
  `aggregate_identity` and the frozen aggregate components.
- `tests/test_monitoring_record_rule_resolver.py` and adjacent daily-run
  service/repository tests.
- The active P9/P10 checkpoint, LOOP ledger and real-loop gate in this
  workbench; the gate is authoritative and remains read-only/blocked.

## Scope

- In scope: strict raw lowercase SHA-256 validation for the three mapping /
  capability hashes carried by published record rules and the pack content hash
  used in aggregate identity construction; add offline regressions.
- Out of scope: changing aggregate component semantics, source-token/CAS state,
  runtime activation, provider/browser/Playwright testing, real projects, or
  unrelated text/identity normalization.

## Success Criteria

- Non-string, padded, uppercase, or otherwise non-canonical aggregate hash
  values fail closed with the existing `monitoring_rule_pack_identity_unverifiable`
  code before an aggregate is returned.
- Existing exact aggregate identity and record-resolution behavior remains
  green in focused and adjacent tests.
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

- 2026-08-05 20:22:15: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Bounded source scan found the resolver still normalized three
  rule-level hashes and one pack content hash with `str(...).strip()`/`str(...)`;
  repository read-side validation is strict for complete identities, but the
  aggregate boundary should fail closed independently.
- 2026-08-05: Added the aggregate raw-value guard; 15 boundary, 111 focused,
  and 103 adjacent tests passed; compileall and Ruff passed; Hermes review-gate
  with `--require-verification` passed. The formal gate remained blocked and
  all reserved ports remained empty.
