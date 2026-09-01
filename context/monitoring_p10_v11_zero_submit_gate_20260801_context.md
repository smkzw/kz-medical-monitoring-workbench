# Task Context: monitoring_p10_v11_zero_submit_gate_20260801

Created: 2026-08-01 18:56:53
Objective: Prepare a fresh isolated v11 runtime from the frozen terminal v10 history, prove v10 retirement and exact historical preservation, and stop before any POST
Task type: `code_open_audit`
Risk: `critical`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem and latest global/workbench `AGENTS.md`.
- Frozen terminal v10 runtime (read-only source):
  `runs/execution/monitoring_p10_v10_zero_submit_gate_20260801/runtime_attempt2/`
- `runs/execution/monitoring_p10_v10_isolated_canary_20260801/TERMINAL_EVIDENCE.md`
- Accepted v11 offline hashes:
  - `monitoring_ai_service.py`:
    `ca7cdb2a93fe0687a0595170fd857d64ba8f5abb6835fa10dafe4f790c00c3b2`
  - `monitoring_protocol_preparation_service.py`:
    `b012a16c595c7c9c90fd0a4a0d86273581dbdf0a1abd42cb8f9e1729ed31b21f`
  - `test_monitoring_ai_service.py`:
    `d030937c74841581880d42fee69e6f4d26f90ac699d8167bf1570e4d48e6bae7`
  - `test_monitoring_protocol_preparation.py`:
    `7a072ee87f01333ecf02b1dbab1f0523eb8f50afc982099e44c37bad7a911d3d`
  - `test_monitoring_ai_startup_recovery.py`:
    `2b406c3445271986c289d54ae2cc48ada3dc44b34d42b942e69a6e521fe0d9bb`
  - `test_monitoring_ai_api.py`:
    `40f31a5b3cb599e5fb06f9cd4bc5dc329870e957bc636620a5a93ee5b6d7bc65`
- Luna final offline review: PASS/P0-P4 none; authority is zero-submit only.
- The unrelated authoritative monitoring main/WAL pair is hash-only
  comparison evidence:
  `b98d5523e05c4cc0f688825bbd66f5cd6ce3b368cb110e1ea43a984c0c54fed7`
  / empty WAL
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

## Scope

- In scope:
  - copy the stopped frozen v10 runtime into a task-owned raw snapshot without
    opening the frozen source through SQLite;
  - use SQLite backup only against that raw task-owned copy to produce a fresh
    21-main-file v11 runtime and copy the task-owned provider/source config
    files without printing their contents;
  - capture pre-start job/attempt/candidate fingerprints and the exact frozen
    v9/v10 terminal lineages from the fresh clone;
  - start one task-owned backend on 127.0.0.1:8911, parallelism one;
  - observe readiness, process/runtime identity, RUX protocol/source resolution,
    v10 retirement markers, zero v11 jobs, zero active/retry surface and exact
    historical preservation;
  - stop 8911 immediately and freeze evidence.
- Out of scope:
  - every POST, provider call, job creation, retry, candidate decision or
    salvage;
  - writes to the frozen v10 source or authoritative runtime;
  - 5174/browser, second topic/project, or contact/stop of 18911;
  - product-source edits, clinical acceptance or release acceptance.

## Success Criteria

- Raw snapshot and fresh clone each contain exactly 21 SQLite main files; all
  non-empty clone files pass integrity check and empty files remain empty.
- Before startup, the clone contains the exact terminal v9 and v10 jobs,
  attempts and zero candidates recorded in prior evidence.
- 8911 process environment points only to the new clone with monitoring AI
  parallelism one; readiness is ready/schema 16/no missing capability.
- RUX protocol `protov_21c4b5a4a3883a8119d74e18` resolves
  `visit_window_and_order` to 200 source spans without submission.
- Startup creates zero v11 jobs, zero active jobs and zero unmarked v4-v10
  jobs; non-retirement job fields, all attempts and all candidates remain
  exactly equal to pre-start snapshots in both EXCEPT directions.
- Frozen v9 and v10 terminal status/timestamps/attempt hashes/provider output
  counts/zero candidates remain exact; v10 gains only its expected immutable
  prompt-retirement marker if not already present.
- 8911 and 5174 are stopped at completion; 18911 remains untouched; the
  authoritative main/WAL hashes remain stable.

## Risk Boundaries

- Writable paths are limited to this task's `runs/execution/`, context,
  review, metrics and LOOP records.
- Any hash, count, process identity, integrity, readiness or historical
  mismatch fails closed, stops 8911 if started and performs no POST.
- Do not print credentials, provider secrets or a full process environment.
- Frozen v10 source, authoritative runtime, product source and 18911 are
  read-only/out of scope.
- Codex owns verification and acceptance.

## Timeout Policy

- One bounded startup and readiness wait only; do not duplicate/relaunch for
  latency.
- This is Codex-direct zero-submit work. Independent Luna review is required
  after evidence exists and before any future POST authority.
- A startup mismatch is terminal for this attempt.

## Loop Log

- 2026-08-01 18:56:53: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- Offline v11 corrective passed Codex pycompile, focused `17`, core `528`,
  adjacent `146` and full monitoring `1489` tests; Luna final review returned
  PASS with P0-P4 none and authorized only this zero-submit preparation.
- Pre-start read-only gate: frozen source has 21 SQLite main files; 8911/5174
  are stopped; 18911 PID 43191 remains separate and untouched; authoritative
  monitoring main/WAL hashes match the frozen comparison pair.
- A task-owned raw copy and fresh SQLite-backup clone were created. Both have
  21 main files; clone integrity is 18 `ok` plus 3 source-empty files.
- PID 85149 started once on 8911 with the exact clone and parallelism one.
  Health/readiness were ok/ready at schema 16, and the RUX visit topic resolved
  to revision `mpr_7c9e69d6aaf6697de37e8c96a95d` with 200 spans.
- Zero-submit database assertions passed: zero v11 jobs, zero active jobs,
  zero unmarked v4-v10; non-retirement job fields, attempts and candidates
  were bidirectionally identical to pre-start. Frozen v9/v10 terminal lineage
  remained exact and only v10 gained `superseded_prompt_contract`.
- 8911 was stopped immediately. 5174 stayed stopped, 18911 stayed untouched,
  and the authoritative main/WAL comparison hashes remained stable. No POST
  or provider call occurred. Evidence:
  `runs/execution/monitoring_p10_v11_zero_submit_gate_20260801/ZERO_SUBMIT_EVIDENCE.md`.
