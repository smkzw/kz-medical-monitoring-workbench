# Codex Review: medical_monitoring_r1_background_progress_shell_20260810

Date: 2026-08-10
Delegated-agent output: `runs/pi_medical_monitoring_r1_background_progress_shell_20260810.md`

## Verdict

**Pass after Codex correction and independent acceptance.** This verdict covers only the isolated synthetic background-progress shell.

## Boundary Check

- Delegated writes stayed within the task's isolated POC source, slice, focused test and slice evidence paths.
- Product code, the medical-writing subsystem, real project material, providers and port 8911 were not touched or started.
- The runner owned the `runs/` report; the worker did not write it directly.

## Codex Verification

- Reproduced the initial concurrency defect: three facades could call the real callback 24 times although the audit had only eight terminal events. Added process-local unit locks and verified exactly eight normal-path callback calls.
- Accepted the independent first-round VETO on the Store terminal-write fault. Added worker error capture/retry, a stable callback idempotency key and a deterministic failure-injection test. The corrected contract is at-least-once in this fault window.
- Current tests: focused 12, R1 core 285, AE/MH 18, Patient Journey 16; all passed. Ruff correctness rules and isolated compileall passed.
- Real Chromium at 1440×900 and 900×700 verified leave/return/reload recovery, exact numeric/bar ratios, distinct blocked/failed presentation, zero console error/warning and no overflow.
- Frozen hashes are recorded in `poc/medical_monitoring_ai_native_r1/docs/R1_BACKGROUND_PROGRESS_SHELL_EVIDENCE.md`; temporary HTTP processes are closed and 8911 has no listener.

## Delegated-Agent Output Review

The delegated handoff was useful but initially overclaimed duplicate-dispatch protection and visual correctness. Codex found the 24-call concurrency defect and stage-bar rendering defects before acceptance. The independent reviewer then found the harder Store-failure path. Both defects were corrected and rechecked; the worker's original self-review was not used as proof of done.

## Hermes Workflow Verification

The Hermes guard initialized and routed the tracked execution. Its runner-owned handoff, provider/model/session metadata and terminal completion record were reviewed, but acceptance rests on Codex checks and the independent conference rather than the delegated model's confidence.

## Residual Risk

- Scope is process-local and synthetic only.
- Persistent Store failure has no retry cap/backoff and grows `errors`.
- The stable idempotency key must be honored by a future real action adapter.
- Store read-snapshot API and unit-lock lifecycle remain later hardening work.
- A latest Ruff all-rule run produces non-gating style/modernization suggestions; correctness rules pass.
