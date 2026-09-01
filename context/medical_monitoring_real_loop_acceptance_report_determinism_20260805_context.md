# Task Context: medical_monitoring_real_loop_acceptance_report_determinism_20260805

Created: 2026-08-05 01:13 (Asia/Shanghai)
Objective: Canonicalize real-loop acceptance diagnostic issue ordering for
stable persisted report hashes under evidence replay
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes workflow guard because it
touches the P10 evidence replay/hash contract.

## Source Of Truth

- `services/api/app/monitoring_real_loop_acceptance.py`
- `tests/test_monitoring_real_loop_acceptance.py`
- adjacent real-loop execution, revalidation, manifest and mode-coverage
  contracts
- current P10 ledger and real-loop gate audit under `records/active_slices/`

## Scope

- In scope: canonicalize the diagnostic issue tuple used in
  `RealLoopAcceptanceReport` and add a reverse-run-order hash regression.
- Out of scope: executing Playwright/provider/login/real projects, changing
  acceptance criteria, medical/UAT authority, runtime activation, B6/C14,
  persistence migration or unrelated UI/medical-writing files.

## Success Criteria

- Equivalent run evidence produces identical report payload and hash regardless
  of input order, while issue contents and acceptance status remain unchanged.
- Existing acceptance/revalidation/execution/mode tests remain green;
  compile, Ruff and reserved-port checks pass.
- Evidence explicitly preserves blocked runtime gates.

## Risk Boundaries

- Do not start or connect to 8911, 5174, 8910 or 4173; do not touch runtime
  databases or real projects.
- No external model dispatch; Codex remains final authority.

## Loop Log

- 2026-08-05 01:13: reproduced different report hashes for the same two-dirty
  run evidence supplied in original versus reversed order; only diagnostic
  issue ordering differed.
- 2026-08-05 01:14-01:16: canonicalized report issues by code/subject/detail,
  added the reverse-run-order regression, and completed focused/adjacent
  offline acceptance-contract checks.

Created: 2026-08-05 01:13:12
Objective: Canonicalize real-loop acceptance diagnostic issue ordering for stable persisted report hashes under evidence replay
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

- 2026-08-05 01:13:12: Task initialized by `tools/hermes_workflow_guard.py init-task`.
