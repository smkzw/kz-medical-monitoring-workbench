# Task Context: monitoring_p10_v10_isolated_canary_20260801

Created: 2026-08-01 16:31:05
Objective: Execute exactly one isolated v10 visit_window_and_order canary, freeze terminal evidence, and stop before any candidate decision or broader run
Task type: `code_open_audit`
Risk: `critical`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem and latest global/workbench `AGENTS.md`.
- `runs/execution/monitoring_p10_v10_zero_submit_gate_20260801/ATTEMPT2_ZERO_SUBMIT_EVIDENCE.md`
- `runs/execution/monitoring_p10_v9_isolated_canary_20260801/ATTEMPT2_TERMINAL_EVIDENCE.md`
- Isolated writable runtime:
  `runs/execution/monitoring_p10_v10_zero_submit_gate_20260801/runtime_attempt2/`
- Current reviewed product hashes recorded in the zero-submit context.
- Luna zero-submit review: PASS for exactly one v10
  `visit_window_and_order` POST only.

No new external discovery is needed. The route, dependency, provider and
isolated runtime were already exercised and independently reviewed immediately
before this task.

## Scope

- In scope:
  - re-confirm ports, product hashes, authoritative physical file baseline,
    exact runtime path/parallelism, readiness, zero v10/zero active and frozen
    v9 history;
  - start one task-owned 8911 on the existing isolated Attempt 2 runtime;
  - submit exactly one POST for only `visit_window_and_order`;
  - run one long hard-wait observer without resubmission or controller retry;
  - freeze job/attempt/provider-output/candidate terminal evidence and stop
    8911 immediately.
- Out of scope:
  - any second POST, retry, reuse, salvage, candidate decision or reclassification;
  - second topic/project, MY009, release, production migration or source edit;
  - authoritative runtime writes, 5174/browser, or contact/stop of 18911;
  - medical-writing lane changes.

## Success Criteria

- Pre-POST gates all pass, then exactly one v10 job is created by one HTTP POST.
- The job reaches a terminal state after no more than the allowed
  initial-plus-one-repair provider lineage and exactly one attempt.
- No other v10 job/topic appears and no frozen v9 evidence changes.
- Terminal evidence includes request/response hashes, provider-output lineage,
  candidates and relevant source locators.
- 8911 is stopped at terminal freeze; 5174 remains stopped; 18911 remains
  untouched; authoritative main/WAL file hashes remain at the new pre-canary
  physical baseline.

## Risk Boundaries

- Writable runtime is limited to the isolated Attempt 2 directory.
- Writable records are limited to this task's context/run/review/metrics,
  a canary evidence directory and the active LOOP ledger.
- Any pre-POST mismatch stops 8911 and performs no POST.
- HTTP error is terminal for the submit step and must not be resent.
- More than one v10 job, more than one attempt, more than two provider outputs,
  a second topic or a non-terminal hard-wait return freezes FAIL without retry.
- Do not open the authoritative SQLite database with a SQLite client; compare
  only its current main/WAL file hashes before/after.
- The delegated reviewer is not final authority; Codex owns acceptance.

## Timeout Policy

- Launch once. Use one observer command with a long wait; do not issue
  fixed-interval controller polls, resubmit, re-dispatch or force-kill for
  latency.
- Provider-side controlled repair may occur only inside the single job's
  existing contract. There is no controller retry.
- Stop only on terminal result, explicit failure, or hard-wait return.

## Loop Log

- 2026-08-01 16:31:05: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- Pre-POST process/runtime/readiness/zero-job/frozen-v9 checks passed on PID
  `18604`.
- Exactly one POST returned HTTP 202 and created v10 job
  `monai_60c8cc7e8b28602a9b4e7f292282`.
- The single long-wait observer returned after about nine minutes with terminal
  `failed/invalid_ai_output`: one attempt, initial plus one repair, zero
  candidates. The precise validation failure was candidate 2's reschedule
  payload containing more than one visit action family.
- 8911 was stopped immediately. No retry, reuse, salvage, candidate decision,
  second topic/project or further provider call occurred. 5174 remained
  stopped; 18911 and the authoritative runtime remained outside the isolated
  execution path.
- Terminal evidence:
  `runs/execution/monitoring_p10_v10_isolated_canary_20260801/TERMINAL_EVIDENCE.md`.
