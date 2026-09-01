# Task Context: monitoring_p10_v10_zero_submit_gate_20260801

Created: 2026-08-01 15:31:10
Objective: Prepare a fresh isolated 21-database v10 runtime, prove v9 retirement and historical preservation, and stop at the zero-submit gate before any POST
Task type: `code_open_audit`
Risk: `critical`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem and the latest global/workbench `AGENTS.md`.
- `context/monitoring_p10_v10_visit_semantic_corrective_pause_20260801.md`
- `context/monitoring_p10_v10_visit_semantic_corrective_20260801_context.md`
- `runs/execution/monitoring_p10_v9_isolated_canary_20260801/ATTEMPT2_TERMINAL_EVIDENCE.md`
- Frozen terminal v9 runtime:
  `runs/execution/monitoring_p10_v9_isolated_canary_20260801/runtime_attempt2/`
- Current governed product files and their accepted hashes:
  - `services/api/app/monitoring_ai_service.py`
    `f1e7276a7d6705d258203f879ea89d677a16659f3b36ba7c56a55a2495578ff6`
  - `tests/test_monitoring_ai_service.py`
    `a9d4b16799fa66c9688183269b686e7881a4b47e35469b90be0f66654729177f`
  - `tests/test_monitoring_protocol_preparation.py`
    `0bb75558acca3e91e77fba7da5cdee4b38f8b5b679a495efe2e09c1a003d0d5d`
  - `tests/test_monitoring_ai_api.py`
    `545b8bb74e888d1b5702f9fc0dee49ce72846df9a6e02a5dc247eb59a2c37bf6`
- The 21 current authoritative SQLite main files under
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/` are
  read-only comparison evidence only. Their monitoring DB/WAL hashes must
  remain:
  `5cb250891b0437e9cffc1121e6956136802f5557a66a0285f723822421db4ba3` /
  `a69b489d09a45a05e87a38cfa2399ca1d72eb2c757f3158760aacced97c48ead`.

External-discovery decision: no new web or package scan. The isolated
SQLite/Uvicorn route was already exercised and independently reviewed in the
immediately preceding v9 canary. This task changes no dependency, architecture
or external-tool choice.

## Scope

- In scope:
  - prove the four governed files have not drifted and no interrupted Kimi
    change crossed the accepted boundary;
  - take a per-database-consistent fresh snapshot of all 21 SQLite main files
    from the frozen terminal v9 runtime and create a distinct writable v10
    runtime clone;
  - copy only the already-frozen task-owned AI/source runtime components needed
    for readiness; do not read or print secret contents;
  - compute pre-start v4-v9 fingerprints and exact v9 terminal lineage;
  - start one task-owned backend on 8911 with the clone-bound
    `WORKBENCH_RUNTIME_DIR` and parallelism one;
  - before any POST, prove process identity, readiness, real RUX source
    resolution, v4-v9 retirement markers, zero active/retry surface, exact
    historical preservation and current v10 prompt identity;
  - stop 8911 immediately after the zero-submit assertions and re-hash the
    authoritative DB/WAL.
- Out of scope:
  - POST, provider call, worker job creation, candidate decision or retry;
  - any write to authoritative runtime or frozen v9 evidence;
  - contacting/stopping/adopting 18911 or starting 5174/browser;
  - real-project execution beyond read-only source resolution;
  - product-source or medical-writing edits;
  - release or full-Goal acceptance.

## Success Criteria

- Snapshot and clone each contain exactly 21 SQLite main files; all non-empty
  snapshot files pass `PRAGMA integrity_check=ok`, empty files remain empty,
  and all clone main-file hashes initially equal the snapshot.
- Pre-start evidence captures exact v4-v9 jobs, attempts and candidates,
  including v9 job `monai_5f66dc5d1c9c77c561a637389bc2`, its single attempt,
  initial+repair output lineage and zero persisted candidates.
- 8911 is the only task-owned listener; its process environment resolves to the
  exact new clone and `WORKBENCH_MONITORING_AI_PARALLELISM=1`.
- Readiness is ready with no missing AI capability, and the confirmed RUX
  protocol/source revision resolves without submitting work.
- Startup retires v9 under v10 with durable marker fields while preserving
  status, attempt/provider failure evidence, terminal timestamps and all
  pre-start fingerprints except the explicitly expected retirement fields.
- No v10 job, no queued/running job and no unmarked v4-v9 retry surface exists.
- 8911 is stopped before this task ends; 5174 remains stopped; 18911 remains
  untouched; authoritative DB/WAL hashes and state remain unchanged.

## Risk Boundaries

- Writable paths are limited to:
  - `runs/execution/monitoring_p10_v10_zero_submit_gate_20260801/`
  - this task's existing context/review/metrics/run record;
  - the active LOOP ledger after evidence is complete.
- The frozen terminal v9 runtime and authoritative runtime are read-only.
- Any hash, process identity, snapshot integrity or historical-fingerprint
  mismatch fails closed, stops 8911 if started, and performs no POST.
- Do not print credentials or full process environments.
- 18911 is a separate temporary runtime and must not be contacted or stopped.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Startup uses one bounded process launch and readiness wait. Do not duplicate
  or fixed-interval re-launch because of latency.
- This zero-submit gate is Codex-direct and does not dispatch an external
  execution route. Independent challenge is reserved for the subsequent
  runtime/POST decision after the gate evidence exists.
- A startup mismatch is terminal for this attempt; stop 8911 and revise the
  hypothesis before any fresh attempt.

## Loop Log

- 2026-08-01 15:31:10: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- Re-anchored the global/workbench instructions, v10 pause/context, v9 terminal
  evidence and LOOP ledger. The four product hashes match, no relevant Python
  file is newer than the pause checkpoint, and no active Kimi child task owns
  these files.
- 8911/5174 are stopped. PID 43191 remains on untouched 18911. Authoritative
  DB/WAL hashes match the checkpoint. The frozen v9 runtime contains exactly
  21 main SQLite files, integrity `ok`, the single terminal v9 failed job, one
  attempt and zero v9 candidates.
- The first zero-submit startup exposed a terminal-audit overwrite and was
  stopped before POST. A Pi initial pass plus two same-session recovery passes
  corrected startup audit-set and same-business-key preservation. Codex
  focused/adjacent verification passed `590` tests; Luna found no P0-P2 and
  authorized a fresh zero-submit rerun only.
- Attempt 2 started PID `15342` on 8911 with the exact isolated runtime and
  parallelism one. Readiness was ready/schema 16/no missing capability. The
  real RUX visit topic resolved to 200 source spans without submitting work.
- Post-start assertions passed: integrity `ok`, zero v10 jobs, zero
  queued/running, zero unmarked v4-v9, markers `3 job + 10 prompt`; all jobs
  excluding retirement fields, all attempts and all candidates were exactly
  equal to the pre-start snapshot in both `EXCEPT` directions. The terminal v9
  failure, timestamps, one initial+repair attempt and zero candidates remained
  exact.
- 8911 was stopped immediately. 5174 stayed stopped and 18911 stayed untouched.
  No POST or provider call occurred.
- Immediately before Attempt 2, the unrelated authoritative DB/WAL pair had
  already changed physical form to main
  `b98d5523e05c4cc0f688825bbd66f5cd6ce3b368cb110e1ea43a984c0c54fed7`
  and empty WAL. The pair was stable before/after this gate and the isolated
  runtime did not depend on it. Evidence is recorded without overstating the
  unobserved cause.
