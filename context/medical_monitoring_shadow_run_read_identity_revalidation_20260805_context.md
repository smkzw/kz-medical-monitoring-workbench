# Task Context: medical_monitoring_shadow_run_read_identity_revalidation_20260805

Created: 2026-08-05 03:27:35
Objective: Revalidate persisted monitoring shadow run identity on reads
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rule_repository.py`
  (`_shadow_run_from_row()` and shadow-run readers).
- `services/api/app/monitoring_protocol_rules.py`
  (`RuleShadowRun.create()` and deterministic content/hash helpers).
- `tests/test_monitoring_protocol_rule_repository_hardening.py` and adjacent
  shadow/lifecycle suites.
- Current filesystem gates under `records/active_slices/`; runtime/provider/
  real-project activation remains prohibited by the authoritative gate.

## Scope

- In scope: read-side shadow-run identity/content revalidation and one
  persisted semantic tamper regression.
- Out of scope: gold-case authoring, rule evaluation, clinical inference,
  schema migration, provider/browser/runtime startup, API login, real
  projects, B6/C14 and UI.

## Success Criteria

- A semantically valid persisted shadow-run edit fails closed before lifecycle,
  release or monitoring consumers receive it.
- Shadow-run content/count/hash identity is checked through the existing
  `RuleShadowRun.create()` factory; no medical outcome is inferred.
- Focused/adjacent tests, compileall, Ruff, reserved-port and review-gate
  checks pass without changing runtime activation gates.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 03:27:35: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: source audit found `_shadow_run_from_row()` reconstructs result
  objects but returns the persisted aggregate without recomputing its stable
  run ID, result counts, diagnostic-result hash or coverage hash. A valid
  persisted snapshot edit could therefore be read under the old run identity.
- 2026-08-05: completed the patch. Modern rows now rebuild through
  `RuleShadowRun.create()` and compare the full persisted identity/content;
  legacy rows lacking complete snapshot metadata and the explicit missing-gold
  hash retain downstream lifecycle diagnostics. Added a valid case-set hash
  tamper regression. Final focused hardening subset passed 47; adjacent groups
  passed 88 + 60 + 51 + 47 + 86 = 332; compileall, Ruff, reserved-port and
  review-gate checks passed. No provider/runtime/browser/real-project action
  occurred.

## Completion / resume boundary

- Product source changed only in
  `services/api/app/monitoring_protocol_rule_repository.py`; the focused
  regression was added to
  `tests/test_monitoring_protocol_rule_repository_hardening.py`.
- Evidence is recorded under
  `records/active_slices/medical_monitoring_shadow_run_read_identity_revalidation_20260805/`,
  with review and metrics under `reviews/` and `metrics/` and the P10 ledger
  append under `records/active_slices/medical_monitoring_goal_p10_20260730/`.
- Keep B6/C14, provider, runtime, browser/Playwright, real-project and
  commercial-release gates closed. The next safe action is another bounded
  source-only P7/P8/P9 integrity gap, not activation.
