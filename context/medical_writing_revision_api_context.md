# Task Context: medical_writing_revision_api

Created: 2026-07-07 21:02:00
Objective: Implement minimal in-memory medical writing revision API without frontend or unrelated subsystem changes
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected Hermes route: `deepseek-v4-flash` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `README.md`
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/demo_repository.py`
- `services/api/app/main.py`
- `tests/test_contracts.py`
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/logs/subsystems/medical_writing_log.md`

## Scope

- In scope: minimal in-memory medical writing revision API for protocol sections, deterministic AI revision suggestion generation, accept/reject/request_rewrite action handling, audit-style event records, focused unittest.
- Out of scope: frontend changes, real LLM calls, DOCX export, medical monitoring, eligibility, approval center, persistent database, backend state machine for approved-section rollback.

## Success Criteria

- Contract layer exposes reusable protocol section/revision thread models plus request/result/action models for revision API.
- FastAPI exposes endpoints to submit revision instructions and act on suggestions.
- DemoRepository stores created/updated revision threads and audit events in memory.
- Tests pass with focused coverage for submit and accept/reject/request_rewrite actions.

## Risk Boundaries

- Do not modify frontend files.
- Do not modify medical monitoring, eligibility, or approval center behavior.
- Do not connect a real LLM or fabricate external clinical evidence.
- Do not apply accepted suggestions into protocol section content in this minimal API; leave formal content approval/application to a later state machine.
- Hermes is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark Hermes failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-07 21:02:00: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-07 21:05:00: Codex read README, contract models, repository/service/API files, tests, demo protocol seed, and medical writing subsystem log; decided to implement a scoped in-memory API only.
- 2026-07-07 21:20:00: Codex implemented contract models, repository persistence methods, medical writing revision service, FastAPI endpoints, README API entries, focused tests, and repeated full unittest verification.
