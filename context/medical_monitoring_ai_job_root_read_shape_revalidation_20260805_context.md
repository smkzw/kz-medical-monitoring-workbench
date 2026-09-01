# Task Context: medical_monitoring_ai_job_root_read_shape_revalidation_20260805

Created: 2026-08-05 04:55:00
Objective: Fail closed on malformed persisted monitoring AI job scalar root fields
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_repository.py` (`_job`,
  `_validated_job_inputs`, persisted job schema and lifecycle fields).
- `services/api/app/monitoring_ai_contracts.py` plus existing AI repository,
  worker, service, API, startup-recovery, evidence and module tests.
- Current filesystem state and
  `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`.
- Real-loop/release gates remain authoritative and blocked; this slice is
  source-only and cannot activate runtime or external providers.

## Scope

- In scope: reject non-integral persisted attempt/max-attempt counters and
  malformed job status/time fields on root reads, preserve valid stale/list
  semantics, add focused tamper regressions, run AI adjacency, compile/Ruff,
  hashes, evidence and review gate.
- Out of scope: services, ports, browsers/Playwright, real project data,
  external providers, medical judgments, new job identity/schema schemes, and
  runtime/release activation.

## Success Criteria

- Valid AI jobs round-trip unchanged across get/list/restart and existing
  lifecycle paths remain green.
- A valid-looking non-integral counter or malformed persisted status/time fails
  closed before queue or audit consumers receive the job.
- Focused/adjacent tests, compileall, Ruff and reserved-port checks pass; the
  evidence records exact counts, hashes, warnings and residual limits.
- Review gate reports `ok: true` with no warnings/errors.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- No provider/sub-agent dispatch is permitted in this turn; Codex performs the
  bounded change and final verification directly.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 04:55:00: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Codex direct execution selected; no external provider or
  sub-agent dispatch.
- 2026-08-05: Implemented and verified strict AI-job root counters/enums/time
  reads; focused 55 and adjacent 822 passed, compileall/Ruff passed, reserved
  ports remained free, and the Hermes review gate returned `ok: true`.
- 2026-08-05: Next action is another bounded source-only P7/P8/P9 integrity
  gap; provider/runtime/real-loop gates remain closed.
