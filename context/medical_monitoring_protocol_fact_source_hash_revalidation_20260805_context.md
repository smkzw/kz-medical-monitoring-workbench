# Task Context: medical_monitoring_protocol_fact_source_hash_revalidation_20260805

Created: 2026-08-05 02:17:14
Objective: Revalidate persisted monitoring protocol fact source text hash and immutable identity on reads
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

- 2026-08-05 02:17:14: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: source audit found `_fact_from_row()` trusted persisted
  `source_text_sha256` and reconstructed a fact without checking its
  immutable revision identity. Runtime/provider gates remain closed.
- 2026-08-05: patch in progress rebuilds the fact and compares source hash,
  deterministic revision ID and immutable payload before return.
- 2026-08-05: focused protocol-fact/repository 43 and adjacent lifecycle/API/
  resolver/release/shadow/authoring/template 290 tests passed; compileall,
  Ruff and reserved-port checks passed. No provider/runtime/browser/
  real-project/B6/C14 action occurred. Continue with a bounded source-only
  P7/P8/P9 gap.

## Scope

- In scope: read-side protocol-fact source-text hash and immutable identity
  revalidation; one persisted source-text tamper regression.
- Out of scope: protocol inference, rule logic, schema migration,
  provider/browser/runtime startup, API login, real projects, B6/C14 and UI.

## Success criteria

- A semantically valid persisted protocol-fact source edit fails closed before
  rule authoring, shadow, daily-run or AI consumers receive it.
- Existing fact status/state and legacy migration contracts remain precise;
  focused/adjacent tests, compileall and Ruff pass.
