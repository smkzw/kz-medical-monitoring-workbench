# Task Context: medical_monitoring_persistence_bool_boundary_20260803

Created: 2026-08-03 10:20:32
Objective: Harden only the remaining persisted monitoring boolean boundaries that can affect assurance completion or rule lifecycle, with focused and full regression evidence; keep all runtime/provider/browser/real-project paths stopped.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Workbench source under `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Primary modules: `services/api/app/monitoring_assurance_repository.py` and
  `services/api/app/monitoring_protocol_rule_repository.py`.
- Primary tests: `tests/test_monitoring_assurance.py`,
  `tests/test_monitoring_protocol_rule_repository_hardening.py`,
  `tests/test_monitoring_protocol_rule_review_boundaries.py`, and the full
  `.venv` `tests/test_monitoring*.py` suite.
- Current P10 ledger and B6/C14 gate artifacts remain authoritative for release
  boundaries; B6 is `pending_review`, C14 is `blocked_pending_b6_review`.

## Scope

- In scope: strict shape handling for SQLite-backed `medical_review_recorded`,
  rule-pack `legacy_read_only`, and gold-case `expected_match` fields, including
  any direct lifecycle/validation reads of those fields and focused regressions.
- Out of scope: frontend/App.jsx, styles, any other AI gateway or provider
  behavior, schema migration, database repair, runtime/service/provider/browser
  starts, API login, real-project files, B6 reviewer outcomes, CAS/source-token
  activation, and medical conclusions.

## Success Criteria

- Malformed persisted boolean values fail closed instead of being accepted by
  Python truthiness; canonical SQLite `0/1` values keep existing behavior.
- Focused and adjacent tests pass, then the full monitoring test suite passes.
- Ruff check and compile pass for changed modules; no unrelated formatter churn.
- Review evidence records exact changed files, tests, residual bool conversions
  that are intentionally data-presence normalization, and unchanged B6/C14 and
  runtime boundaries.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Product/runtime source changes are limited to the two named repository modules
  and their focused tests; isolated temporary SQLite files may be used only by
  existing tests and must not be reused as project data.
- No B6 outcome may be created or inferred; all gate/report authority remains
  diagnostic-only and false.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 10:20:32: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Added strict SQLite 0/1 readers for assurance
  `medical_review_recorded` and protocol `legacy_read_only`/`expected_match`;
  added three malformed-persistence regressions.
- 2026-08-03: Focused 49 passed; adjacent protocol/lifecycle/shadow/release set
  117 passed; full `tests/test_monitoring*.py` 1807 passed, 25 warnings in
  471.59s. Ruff check and compile passed; format check would reformat the four
  historical large files, so no formatter churn was introduced.
- 2026-08-03: B6 remains `pending_review`, C14 remains
  `blocked_pending_b6_review`; 8911/5174 have no listeners. No provider,
  browser, API login, service, CAS/SQLite project operation or real-project
  data was used.
