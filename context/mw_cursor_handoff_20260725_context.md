# Task Context: mw_cursor_handoff_20260725

Created: 2026-07-25 16:21:12
Objective: Create a complete lossless handoff prompt for Cursor Agent #1 to audit and continue the medical writing workbench
Task type: `unknown`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_writing_production_rebaseline_20260722/SOFT_PAUSE_RESUME.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/CURRENT_GAP_MATRIX.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/END_TO_END_PROGRESS_AUDIT.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/POST_RESTART_REAL_ACCEPTANCE_20260725.md`
- Current filesystem, current runtime state, and user corrections.

## Scope

- In scope: one complete Cursor handoff contract covering requirements, current state, known
  counterexamples, authoritative sources, exact recovery sequence, verification, and diff records.
- Out of scope: further feature development, service restart, v13 product runs, conference dispatch,
  or Word acceptance during this handoff-only task.

## Success Criteria

- Cursor can reconstruct the task from local files without relying on the prior chat.
- The prompt requires a full project inventory and challenges false completion claims.
- The product independent-AI boundary and E1-E5 acceptance levels are explicit.
- Exact current recovery steps and lossless return records for Codex are explicit.

## Risk Boundaries

- Do not restart current services or resume product jobs while preparing the handoff.
- Do not modify product source code.
- Preserve the current lossless pause boundary.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-25 16:21:12: Task initialized by `tools/hermes_workflow_guard.py init-task`.
