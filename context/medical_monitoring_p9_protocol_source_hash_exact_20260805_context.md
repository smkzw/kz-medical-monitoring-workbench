# Task Context: medical_monitoring_p9_protocol_source_hash_exact_20260805

Created: 2026-08-05 10:47:01
Objective: Harden protocol source-version and source-reference hash admission so lineage bytes are exact lowercase SHA-256 values without altering clinical rule semantics
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rules.py`
- `tests/test_monitoring_protocol_rules.py`
- `tests/test_monitoring_protocol_rule_repository_hardening.py`
- `context/medical_monitoring_p9_source_only_checkpoint_20260805.md`
- `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`

The current filesystem and these contracts are authoritative for this bounded
source-only slice. The formal real-loop gate is blocked; no runtime/provider,
browser or real project may be activated.

## Scope

- In scope: exact canonical admission of protocol source-version content
  digests and source-reference evidence digests at the protocol lineage
  boundary; focused tests and evidence records.
- Out of scope: protocol interpretation, provider/runtime activation, ports,
  browser/Playwright or API login, real-project data, clinical acceptance,
  database migration, and the medical-writing subsystem.

## Success Criteria

- Non-empty source content/reference SHA-256 values are accepted only as exact
  lowercase 64-hex strings; no trim/lower/string coercion can convert a
  malformed lineage token into a canonical one.
- Existing calculated source-text hashes and revision-token semantics remain
  unchanged; invalid supplied evidence fails closed.
- Focused protocol rule tests and repository hardening tests pass; runtime,
  browser and clinical evidence remain explicitly unverified.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This slice is performed directly by Codex; the route recorded by task
  initialization is not dispatched because no external model call is needed.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 10:47:01: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 10:48: re-anchored P9 checkpoint, LOOP ledger and blocked gate;
  selected the upstream protocol source-hash boundary after rule-pack identity
  hardening.
- 2026-08-05 10:52: changed `ProtocolSourceVersion.create()` and
  `RuleSourceReference.create()` to reject padded, uppercase or non-string
  supplied SHA-256 values; added factory and persisted protocol-version
  tamper regressions.
- 2026-08-05 10:55: focused source/reference suite passed **55 tests**;
  protocol API/lifecycle/review/cross-project adjacency passed **57 tests, 1
  warning**; daily-run/record-resolver/repository adjacency passed **96 tests
  and 41 subtests**; compileall and source scan passed. Real MY008 collection
  remains blocked by missing `cryptography`; no dependency was installed.
