# Task Context: medical_monitoring_authoring_strict_inputs_20260805

Created: 2026-08-05 00:57:37
Objective: Harden medical-monitoring protocol/rule authoring CAS and reauthentication request contracts against Pydantic coercion without changing authorization or runtime behavior
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- services/api/app/medical_monitoring_router.py authoring request models and
  route consumers.
- tests/test_medical_monitoring_module_contract.py and the existing
  medical-monitoring protocol/rule authoring tests.
- Current P10 ledger and completion audit under records/active_slices/.
- Current filesystem is authoritative; this is source-only and must not
  activate runtime or real-project gates.

## Scope

- In scope: make protocol/rule authoring CAS fields StrictInt or Optional
  StrictInt and reauthentication fields StrictBool for applicability,
  protocol-fact, rule-pack, automatic-shadow and shadow-confirmation requests;
  add direct model regressions; preserve valid values and authorization flow.
- Out of scope: provider calls, service/API startup, browser/Playwright tests,
  real-project data, database migration, B6/C14 review or activation, medical
  conclusions, and unrelated medical-writing files.

## Success Criteria

- Every changed request model rejects bool and numeric-string CAS values and
  rejects 0/1/string boolean reauthentication values at validation.
- Optional pack revisions accept None and strict positive integers.
- Existing main medical-monitoring authoring and protocol/rule suites remain
  green; compile, Ruff and reserved-port checks pass.
- Evidence explicitly states this is offline source-only hardening and leaves
  B6/C14 and real LOOP gates unchanged.

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

- 2026-08-05 00:57:37: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 00:58: source audit identified nine request fields in the main
  authoring router that still used coercive int/bool types. Next: strict types
  plus model-level negative regressions only.
- 2026-08-05 01:01: StrictInt/StrictBool fields and model-level regressions were
  added. Focused 193 and adjacent 244-test groups passed; compile, Ruff and
  reserved-port checks passed. No runtime/provider/browser/real-project action
  occurred.
- 2026-08-05 01:02: review and metrics prepared. Next safe action is another
  bounded P7/P8/P9 source-only gap; runtime remains blocked by formal B6 and
  source-token/CAS/identity gates.
