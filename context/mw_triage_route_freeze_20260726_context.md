# Task Context: mw_triage_route_freeze_20260726

Created: 2026-07-26 14:03:13
Objective: Freeze competitor-triage durable job independent-AI route at creation; fail closed on profile drift; add compatibility and recovery tests
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/handoffs/codex_retake_20260726/evidence/SUBAGENT_BACKEND_DIFF_AUDIT.md`
- `services/api/app/medical_writing_competitor_triage.py`
- `services/api/app/ai_runtime_settings.py`
- `services/api/app/ai_gateway.py`
- `services/api/app/medical_writing_durable_jobs.py`
- focused tests under `tests/`

## Scope

- In scope: competitor-triage durable route snapshot, runtime profile
  revisioning needed by that snapshot, legacy blocking, focused tests.
- Out of scope: prefill, frontend, translation, shared durable-store schema,
  security/backdoor review.

## Success Criteria

- Jobs execute on their creation-time profile after active-profile switching.
- Profile modification/deletion fails closed without using another route.
- Payload is auditable and contains no credential.
- Legacy behavior is explicit.
- Switch, concurrency and restart recovery tests pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-26 14:03:13: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-26: Implemented route snapshot and store-owned profile revisions.
- 2026-07-26: Added switch, concurrent dual-profile, profile drift/deletion,
  cold-restart, direct factory and legacy-job tests.
- 2026-07-26: 261 focused and 180 adjacent regression tests passed.
