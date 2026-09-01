# Task Context: medical_monitoring_rule_definition_read_identity_revalidation_20260805

Created: 2026-08-05 02:20:47
Objective: Revalidate persisted monitoring rule definition source hash and immutable identity on reads
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- TODO: Add authoritative local files, extracts, datasets, screenshots, URLs, or user-provided materials.
- Do not add production paths unless the user has explicitly authorized reading them for this task.

## Scope

- In scope: TODO
- Out of scope: TODO

## Success Criteria

- TODO

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 02:20:47: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: source audit found direct rule hydration (`_rule_by_id()` and
  `rule_source()`) relied on `_rule_from_row()` without recomputing the
  source-text hash, stable revision ID or immutable rule payload. Runtime and
  provider gates remain closed.
- 2026-08-05: patch in progress rebuilds complete-identity rules and compares
  source hash, stable revision ID and immutable payload; partial identity is
  left for the existing downstream readiness diagnostic.
- 2026-08-05: completed the read-side patch. `_rule_from_row()` now rejects a
  mismatched persisted source-text digest before rebuilding complete-identity
  rules, then compares deterministic revision identity and immutable content;
  all-blank and partial mapping identities retain the existing downstream
  legacy/readiness diagnostic. Added a semantic persisted source-text tamper
  regression. Final focused hardening subset passed 44; adjacent groups passed
  329 (85 + 60 + 51 + 47 + 86), including the 12m16s shadow/gold-shadow
  fixture group. Compileall, Ruff, reserved-port and review-gate checks passed;
  no runtime/provider/browser/real-project action occurred.

## Scope

- In scope: read-side rule-definition hash/identity revalidation and one
  persisted semantic rule tamper regression.
- Out of scope: rule evaluation changes, clinical inference, schema migration,
  provider/browser/runtime startup, API login, real projects, B6/C14 and UI.

## Success criteria

- A semantically valid persisted rule edit fails closed before direct source,
  lifecycle, shadow, daily-run or AI consumers receive it.
- Existing partial mapping-identity diagnostics and legacy migration contracts
  remain precise; focused/adjacent tests, compileall and Ruff pass.

## Completion / resume boundary

- Product source changed only in `services/api/app/monitoring_protocol_rule_repository.py`;
  the focused regression was added to
  `tests/test_monitoring_protocol_rule_repository_hardening.py`.
- Evidence is recorded under
  `records/active_slices/medical_monitoring_rule_definition_read_identity_revalidation_20260805/`,
  with review and metrics under `reviews/` and `metrics/` and the P10 ledger
  append under `records/active_slices/medical_monitoring_goal_p10_20260730/`.
- Keep B6/C14, provider, runtime, browser/Playwright, real-project and
  commercial-release gates closed. The next safe action is another bounded
  source-only P7/P8/P9 integrity gap, not activation.
