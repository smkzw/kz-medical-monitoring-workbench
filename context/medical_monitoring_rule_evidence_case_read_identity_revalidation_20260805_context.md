# Task Context: medical_monitoring_rule_evidence_case_read_identity_revalidation_20260805

Created: 2026-08-05 03:45:30
Objective: Revalidate persisted gold and diagnostic rule evidence case identities on reads
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rule_repository.py`
  (`_gold_case_from_row()`, `_diagnostic_case_from_row()` and case readers).
- `services/api/app/monitoring_protocol_rules.py`
  (`RuleGoldStandardCase.create()` / `RuleDiagnosticCase.create()` and stable
  case-content helpers).
- `tests/test_monitoring_protocol_rule_repository_hardening.py` plus adjacent
  lifecycle, shadow and P7C evidence suites.
- Current filesystem gates under `records/active_slices/`; runtime/provider/
  real-project activation remains prohibited by the authoritative gate.

## Scope

- In scope: read-side identity/content revalidation for modern gold and
  diagnostic evidence cases, with legacy gold-case compatibility and focused
  persisted tamper regressions.
- Out of scope: case authoring, rule evaluation, clinical inference, schema
  migration, provider/browser/runtime startup, API login, real projects,
  B6/C14 and UI.

## Success Criteria

- A semantically valid persisted gold or diagnostic case edit fails closed
  before shadow/release consumers receive it.
- Legacy gold rows with the pre-coverage-label shape retain their existing
  compatibility path.
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

- 2026-08-05 03:45:30: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: source audit found `_gold_case_from_row()` and
  `_diagnostic_case_from_row()` return persisted evidence rows directly. Their
  stable case IDs and normalized content are not recomputed on reads; modern
  evidence can therefore drift while retaining its stored case ID. Legacy gold
  rows with empty `coverage_labels_json` must remain readable for the existing
  migration diagnostic.
- 2026-08-05: completed the patch. Modern gold and diagnostic cases now rebuild
  through their validated factories and compare the deterministic case ID plus
  normalized content; legacy gold rows without coverage labels retain the
  compatibility path. Added valid case-label and diagnostic-code tamper
  regressions. Final focused case/repository/P7C suite passed 65; adjacent
  groups passed 90 + 60 + 51 + 47 + 86 = 334; compileall, Ruff,
  reserved-port and review-gate checks passed. No provider/runtime/browser/
  real-project action occurred.

## Completion / resume boundary

- Product source changed only in
  `services/api/app/monitoring_protocol_rule_repository.py`; focused
  regressions were added to
  `tests/test_monitoring_protocol_rule_repository_hardening.py`.
- Evidence is recorded under
  `records/active_slices/medical_monitoring_rule_evidence_case_read_identity_revalidation_20260805/`,
  with review and metrics under `reviews/` and `metrics/` and the P10 ledger
  append under `records/active_slices/medical_monitoring_goal_p10_20260730/`.
- Keep B6/C14, provider, runtime, browser/Playwright, real-project and
  commercial-release gates closed. The next safe action is another bounded
  source-only P7/P8/P9 integrity gap, not activation.
