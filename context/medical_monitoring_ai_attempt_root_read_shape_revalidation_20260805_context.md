# Task Context: medical_monitoring_ai_attempt_root_read_shape_revalidation_20260805

Created: 2026-08-05 05:24:10
Objective: Fail closed on malformed persisted monitoring AI attempt root fields
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_repository.py` (`attempts`,
  `_attempt_payload_from_row`, attempt schema and `record_attempt` writes).
- `tests/test_monitoring_ai_repository.py` plus monitoring AI module-contract,
  risk-bridge and release-adjacent suites.
- Current filesystem state and
  `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`.
- Real-loop and release gates remain authoritative and blocked; this slice is
  source-only and cannot activate runtime or external providers.

## Scope

- In scope: validate persisted attempt root IDs/counter/owner/outcome/time and
  parent job binding on read; preserve request/response payload hash checks and
  legacy empty-payload compatibility; add focused tamper regressions, run AI
  adjacency, compile/Ruff, hashes, evidence and review gate.
- Out of scope: services, ports, browsers/Playwright, real project data,
  external providers, medical judgments, new attempt hash/schema schemes,
  runtime/release activation and provider execution.

## Success Criteria

- Valid attempts round-trip unchanged after restart.
- A malformed attempt counter/identity/owner/outcome/timestamp or non-empty
  payload with an empty hash fails closed before callers receive the attempt.
- Focused/adjacent tests, compileall, Ruff and reserved-port checks pass; the
  evidence records exact counts, hashes, warnings and residual limits.
- Review gate reports `ok: true` with no warnings/errors.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 05:24:10: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Codex direct source-only implementation selected; no Hermes
  execution session, provider call or sub-agent dispatch.
- 2026-08-05: Added strict AI attempt root/parent reads and retained empty
  payload legacy compatibility; added five isolated tamper regressions.
  Focused 82 and adjacent 827 passed (17 pre-existing warnings); compileall/
  Ruff passed; ports remained free.
- **Residual/next**: attempt read integrity does not prove provider quality,
  clinical correctness, browser usability, formal B6 review, C14 activation or
  commercial release. Continue with a bounded structural P7/P8/P9 source-only
  gap; keep runtime gates closed.
