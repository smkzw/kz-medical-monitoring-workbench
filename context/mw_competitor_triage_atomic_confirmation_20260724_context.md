# Task Context: mw_competitor_triage_atomic_confirmation_20260724

Created: 2026-07-24 18:53:48
Objective: Atomically confirm final competitor triage classifications, support justified all-excluded baskets, and verify frontend/backend contracts without touching dynamic design typed objects
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/medical_writing_competitor_triage.py`
- `services/api/app/main.py`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- Focused competitor-triage and frontend contract tests.

## Scope

- In scope: formal final classifications, atomic confirmation/decisions/run/idempotency,
  all-excluded reason and corpus continuation, focused tests and Vite build.
- Out of scope: dynamic design typed objects/projection, unrelated repository
  refactors, security audit, D017 approval.

## Success Criteria

- Final classification changes are committed in the same transaction as the
  confirmation and relevance decisions.
- Exact partition, classification enum, stale snapshot and reason constraints
  remain fail-closed.
- Same request is idempotent; same key with changed classifications conflicts.
- All-excluded succeeds only with a substantive reason and advances the journey.
- Focused tests and Vite production build pass.

## Risk Boundaries

- Do not edit frozen dynamic design typed objects.
- Keep the existing replayable cross-database journey projection boundary.
- Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-24 18:53:48: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-24: Located HTTP post-confirm override loop and confirmed it ran after
  service confirmation and journey projection.
- 2026-07-24: Added formal final-classification/all-excluded contract and moved
  final decisions, run status and idempotency into one `BEGIN IMMEDIATE`.
- 2026-07-24: Removed HTTP post-write loop and added all-excluded frontend flow.
- 2026-07-24: 176 focused tests, 29 adjacent tests and Vite build passed.
