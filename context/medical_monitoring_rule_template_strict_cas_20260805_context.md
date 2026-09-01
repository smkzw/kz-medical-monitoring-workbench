# Task Context: medical_monitoring_rule_template_strict_cas_20260805

Created: 2026-08-05 01:01:08
Objective: Harden rule-template recommendation write CAS request fields against boolean/string coercion and verify the adjacent recommendation workflow
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- services/api/app/monitoring_rule_template_recommendation_router.py
  request models and route consumers.
- tests/test_monitoring_rule_template_recommendation.py and adjacent AI/rule
  workflow tests.
- Current P10 ledger and completion audit under records/active_slices/.
- Current filesystem is authoritative; this slice is source-only and must not
  activate runtime or real-project gates.

## Scope

- In scope: make the two recommendation write CAS request fields StrictInt;
  add direct model and API boundary regressions; preserve valid request and
  recommendation behavior.
- Out of scope: provider calls, service/API startup, browser/Playwright tests,
  real-project data, database migration, B6/C14 review or activation, medical
  conclusions, and unrelated medical-writing files.

## Success Criteria

- Recommendation start and decision models reject bool and numeric-string CAS
  values before service mutation.
- Existing recommendation workflow tests remain green; compile, Ruff and
  reserved-port checks pass.
- Evidence states source-only scope and leaves B6/C14 and real LOOP gates
  unchanged.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- No external model dispatch is used; Codex remains final authority.
- Do not start or connect to 8911, 5174, 8910 or 4173; do not touch runtime
  databases or real projects.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 01:01:08: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 01:02: inspected the recommendation router and found two
  write-side expected_fact_state_version fields still using coercive int.
- 2026-08-05 01:04-01:06: changed both fields to StrictInt, added direct
  bool/numeric-string boundary regressions, corrected an initial test-placement
  mistake before final verification, and completed focused/adjacent checks.
