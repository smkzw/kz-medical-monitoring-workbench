# Task Context: medical_monitoring_p8_nonreal_composite_revalidation_20260805

Created: 2026-08-05 07:26:47
Objective: Revalidate the P8 assurance and release-contract source stack without runtime activation
Task type: `finite_code_task`
Risk: `high`
Selected agent route: Codex direct; no delegated provider or sub-agent is permitted for this slice.

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- P8 assurance, module-contract and release-dossier/gate tests named in the
  command below; current filesystem is the source of truth.
- The read-only real-loop gate under `records/active_slices/` is a hard
  constraint, not activation authority.
- No real-project data, service/browser startup, provider call or runtime login
  is permitted.

## Scope

- In scope: deterministic composite regression over assurance/proof/rollup,
  principal-route and release-contract tests, compileall, port checks and
  durable phase evidence.
- Out of scope: real-project tests, browser/Playwright, external models,
  service/API activation, clinical claims, B6/C14 approval and release status.

## Success Criteria

- The explicit non-real P8 suite passes with exact exclusions, no reserved
  runtime ports listen, and warnings/residual limits are recorded.

## Risk Boundaries

- Only task evidence files may change. Keep runtime activation read-only/blocked.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 07:26:47: Task initialized by `tools/hermes_workflow_guard.py init-task`.
