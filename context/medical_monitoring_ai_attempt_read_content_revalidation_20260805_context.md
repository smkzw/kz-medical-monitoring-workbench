# Task Context: medical_monitoring_ai_attempt_read_content_revalidation_20260805

Created: 2026-08-05 04:43:27
Objective: Fail closed on persisted monitoring AI attempt request/response content hash drift on audit reads
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_repository.py` (`record_attempt`,
  `attempts`, `content_sha256`, and the immutable attempt table).
- `tests/test_monitoring_ai_repository.py` plus the existing AI repository,
  worker, API, startup-recovery, evidence, release and module-contract tests.
- Current filesystem state and
  `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`.
- Real-loop/release gates remain authoritative and blocked; this slice is
  source-only and cannot activate runtime or external providers.

## Scope

- In scope: revalidate persisted attempt request/response JSON shape and their
  existing SHA-256 columns on audit reads; preserve blank response semantics,
  attempt ordering and the existing job/lease contract; add focused regressions,
  run adjacent checks, compile/Ruff, hashes, evidence and review gate.
- Out of scope: services, ports, browsers/Playwright, real project data,
  external providers, medical judgments, new schema/identity schemes, and
  runtime/release activation.

## Success Criteria

- Valid attempt request/response payloads round-trip unchanged.
- A valid-looking persisted request or response mutation fails closed before an
  audit consumer receives it; malformed JSON also fails closed.
- Focused/adjacent tests, compileall, Ruff and reserved-port checks pass; the
  evidence records exact counts, warnings, hashes and residual limits.
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

- 2026-08-05 04:43:27: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Codex direct execution selected; no external provider or
  sub-agent dispatch.
- 2026-08-05: Implemented and verified the bounded attempt-payload read checks;
  focused 51 and adjacent 816 passed, compileall/Ruff passed, reserved ports
  remained free, and the Hermes review gate returned `ok: true`.
- 2026-08-05: Next action is another bounded source-only P7/P8/P9 integrity
  gap; provider/runtime/real-loop gates remain closed.
