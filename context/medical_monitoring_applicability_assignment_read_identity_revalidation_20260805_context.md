# Task Context: medical_monitoring_applicability_assignment_read_identity_revalidation_20260805

Created: 2026-08-05 03:11:23
Objective: Revalidate persisted protocol applicability assignment identity on reads
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rule_repository.py`
  (`_applicability_assignment_with_state()` and assignment readers).
- `services/api/app/monitoring_protocol_rules.py`
  (`ProtocolApplicabilityAssignment.create()` is the deterministic identity
  authority).
- `tests/test_monitoring_protocol_rule_repository_hardening.py` and adjacent
  protocol-applicability suites.
- Current filesystem gates under `records/active_slices/`; runtime/provider/
  real-project activation remains prohibited by the authoritative gate.

## Scope

- In scope: read-side protocol applicability-assignment identity revalidation
  and one persisted semantic tamper regression.
- Out of scope: protocol-version changes, rule/fact evaluation, clinical
  inference, schema migration, provider/browser/runtime startup, API login,
  real projects, B6/C14 and UI.

## Success Criteria

- A semantically valid persisted assignment edit fails closed before
  applicability resolution, protocol preparation or downstream monitoring
  consumers receive it.
- Assignment state fields remain governed by the existing state table while
  immutable assignment identity is checked against its factory.
- Focused/adjacent tests, compileall, Ruff, reserved-port and review-gate
  checks pass without changing the runtime activation gates.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 03:11:23: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: source audit found `_applicability_assignment_with_state()`
  returns a persisted assignment directly, without recomputing its stable
  `assignment_id`. A valid evidence-text or effective-date mutation could
  therefore be returned under the stored assignment identity; state overlays
  must remain separate from this check.
- 2026-08-05: completed the patch. Assignment rows now rebuild through
  `ProtocolApplicabilityAssignment.create()` and compare the deterministic
  `assignment_id` before state is overlaid. A valid evidence-text tamper fails
  closed. Final focused hardening subset passed 46; adjacent groups passed
  87 + 60 + 51 + 47 + 86 = 331; compileall, Ruff, reserved-port and
  review-gate checks passed. No provider/runtime/browser/real-project action
  occurred.

## Completion / resume boundary

- Product source changed only in
  `services/api/app/monitoring_protocol_rule_repository.py`; the focused
  regression was added to
  `tests/test_monitoring_protocol_rule_repository_hardening.py`.
- Evidence is recorded under
  `records/active_slices/medical_monitoring_applicability_assignment_read_identity_revalidation_20260805/`,
  with review and metrics under `reviews/` and `metrics/` and the P10 ledger
  append under `records/active_slices/medical_monitoring_goal_p10_20260730/`.
- Keep B6/C14, provider, runtime, browser/Playwright, real-project and
  commercial-release gates closed. The next safe action is another bounded
  source-only P7/P8/P9 integrity gap, not activation.
