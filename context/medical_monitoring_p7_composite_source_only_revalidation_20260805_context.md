# Task Context: medical_monitoring_p7_composite_source_only_revalidation_20260805

Created: 2026-08-05 07:18:48
Objective: Revalidate the P7 monitoring source-only stack without runtime activation
Task type: `finite_code_task`
Risk: `high`
Selected agent route: Codex direct; no delegated provider or sub-agent is permitted for this slice.

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- P7 source/test surfaces under `services/api/app/` and `tests/` for monitoring
  batch, protocol/rule, record applicability, and daily-run workflows.
- Current read-only real-loop gate under `records/active_slices/` is a hard
  constraint, not activation authority.
- No real-project data, service/browser startup, provider call, or runtime login
  is permitted.

## Scope

- In scope: one deterministic composite regression over the non-real P7 suite,
  compileall, port checks, and durable phase evidence.
- Out of scope: real-project tests, browser/Playwright, external models,
  service/API activation, medical claims, B6/C14 approval, and release status.

## Success Criteria

- The explicit P7 suite passes with real-project files excluded; no reserved
  runtime ports are listening; evidence states the exact exclusions and warnings.

## Risk Boundaries

- Only task evidence files may change. Keep runtime activation read-only/blocked.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 07:18:48: Task initialized by `tools/hermes_workflow_guard.py init-task`.
