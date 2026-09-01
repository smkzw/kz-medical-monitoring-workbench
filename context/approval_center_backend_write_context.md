# Task Context: approval_center_backend_write

Created: 2026-07-07 21:02:30
Objective: Implement minimal Approval Center backend write interface with contracts, FastAPI endpoint, in-memory audit persistence, and focused unittest
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected Hermes route: `deepseek-v4-flash` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `README.md`
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/main.py`
- `services/api/app/demo_repository.py`
- `tests/`
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/logs/subsystems/approval_center_log.md`

## Scope

- In scope: minimal Approval Center backend write contract, FastAPI action endpoint, demo in-memory approval state/audit persistence, and focused unit tests.
- Out of scope: electronic signature, frontend changes, medical writing implementation changes, enrollment review implementation changes, medical monitoring implementation changes, persistent database/audit immutability.

## Success Criteria

- Contract layer exports `ApprovalActionRequest`, `ApprovalActionResult`, `ApprovalDecisionRecord`, and supporting approval action/blocker models.
- `POST /api/projects/{project_id}/approvals/{approval_id}/actions` supports `approve`, `return_for_revision`, `reject`, and `view_quality_gate`.
- `approve` returns a backend 409 and does not mutate the approval gate when blockers exist.
- Demo repository appends approval decision records and audit events in memory.
- Focused approval tests and full existing unittest suite pass.

## Risk Boundaries

- Do not touch `frontend/`.
- Do not implement electronic signature, permission model, immutable audit storage, or cross-subsystem writes.
- Do not alter medical writing, enrollment review, or medical monitoring behavior beyond reading their current contracts/state for approval blockers.

## Timeout Policy

- Do not mark Hermes failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-07 21:02:30: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-07: Read README, contracts, backend services, tests, and approval center subsystem log.
- 2026-07-07: Added approval action contracts, repository state machine, FastAPI endpoint, and focused approval center tests.
- 2026-07-07: Verified with `python3 -m unittest tests.test_approval_center -v` and `python3 -m unittest discover -s tests -v` after adding blocked and successful approval paths.
