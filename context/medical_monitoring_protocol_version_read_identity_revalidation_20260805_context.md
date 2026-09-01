# Task Context: medical_monitoring_protocol_version_read_identity_revalidation_20260805

Created: 2026-08-05 02:52:42
Objective: Revalidate persisted protocol source version identity on reads
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rule_repository.py`
  (`_protocol_version_from_row()` and protocol-version readers).
- `services/api/app/monitoring_protocol_rules.py`
  (`ProtocolSourceVersion.create()` is the deterministic identity authority).
- `tests/test_monitoring_protocol_rule_repository_hardening.py` and adjacent
  protocol-rule suites.
- Current filesystem gates under `records/active_slices/`; runtime/provider/
  real-project activation remains prohibited by the authoritative gate.

## Scope

- In scope: read-side protocol source-version hash/identity revalidation and
  one persisted semantic tamper regression.
- Out of scope: applicability-assignment changes, rule/fact evaluation,
  clinical inference, schema migration, provider/browser/runtime startup, API
  login, real projects, B6/C14 and UI.

## Success Criteria

- A semantically valid persisted protocol-version edit fails closed before
  protocol/fact/rule, preparation, resolver or release consumers receive it.
- State fields remain governed by the existing state table while immutable
  source identity is checked against `ProtocolSourceVersion.create()`.
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

- 2026-08-05 02:52:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: source audit found `_protocol_version_from_row()` returns a
  persisted `ProtocolSourceVersion` directly, without recomputing its stable
  `protocol_version_id` from the immutable source/version fields. A valid
  content digest mutation could therefore be returned under the stored
  revision; state overlays must remain separate from this check.
- 2026-08-05: completed the patch. `_protocol_version_from_row()` now rebuilds
  through `ProtocolSourceVersion.create()` and compares the deterministic
  revision ID plus immutable payload before returning. A valid 64-character
  content digest tamper fails closed. Final focused hardening subset passed
  45; adjacent groups passed 86 + 60 + 51 + 47 + 86 = 330; compileall, Ruff,
  reserved-port and review-gate checks passed. No provider/runtime/browser/
  real-project action occurred.

## Completion / resume boundary

- Product source changed only in
  `services/api/app/monitoring_protocol_rule_repository.py`; the focused
  regression was added to
  `tests/test_monitoring_protocol_rule_repository_hardening.py`.
- Evidence is recorded under
  `records/active_slices/medical_monitoring_protocol_version_read_identity_revalidation_20260805/`,
  with review and metrics under `reviews/` and `metrics/` and the P10 ledger
  append under `records/active_slices/medical_monitoring_goal_p10_20260730/`.
- Keep B6/C14, provider, runtime, browser/Playwright, real-project and
  commercial-release gates closed. The next safe action is another bounded
  source-only P7/P8/P9 integrity gap, not activation.
