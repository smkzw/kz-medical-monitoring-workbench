# Task Context: monitoring_p10_v9_runtime_preflight_20260801

Created: 2026-08-01 11:57:57
Objective: Read-only preflight for one future fresh v9 protocol canary: verify frozen hashes, stopped ports, runtime counts, old-job eligibility, startup migration/backfill ordering, and parallel medical-writing isolation without starting services or mutating runtime
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem and read-only SQLite state under the project-level
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/`.
- `implementation/workbench/runtime/medical_monitoring_ai.sqlite3` is a
  zero-byte local stub and is not the runtime authority.
- `context/monitoring_p10_protocol_v9_cutover_direct_tests_pause_20260801.md`
- `reviews/codex_monitoring_p10_protocol_v9_cutover_direct_tests_20260801_review.md`
- `runs/conference/monitoring_p10_protocol_v9_contradiction_review_20260801/general_codex_luna_round4.md`
- `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`
- `services/api/app/main.py` startup hooks and
  `services/api/app/monitoring_ai_repository.py` initialization/recovery.
- Latest applicable AGENTS and `multi-agent-verification-loop` Skill.

External-discovery decision: no web/package scan. This is a bounded audit of
local persisted state and existing startup code; no dependency, architecture,
tool adoption or external factual claim is being selected.

## Scope

- In scope:
  - verify frozen governed hashes and stopped ports/processes;
  - inventory the exact runtime databases without opening them writable;
  - query monitoring job/attempt/candidate counts by prompt version and status;
  - identify any v4-v8 row that could be claimed, retried, reused or restored;
  - audit schema version/columns and startup ordering for marker migration,
    prompt/workflow retirement and lease recovery;
  - compare runtime state with the last frozen counts;
  - read-only confirm parallel medical-writing drift remains outside scope.
- Out of scope:
  - starting 8911/5174 or any worker/provider;
  - applying the schema migration to runtime databases;
  - creating/retrying/reusing jobs, touching candidates, running a canary,
    launching real projects or making release decisions;
  - fixing provider-only uniqueness or medical-writing drift.

## Success Criteria

- Governed hashes match the offline PASS checkpoint.
- 8911/5174 have no listeners and no slice-owned process remains.
- Every runtime query is read-only (`mode=ro`/immutable where appropriate) and
  produces an auditable inventory.
- v4-v8 frozen counts match prior evidence; no old job is currently claimable,
  retryable/reusable under the intended startup contract, or silently selected
  as fresh v9.
- Startup order proves schema backfill and prompt/workflow retirement occur
  before worker recovery/claim, or any gap is recorded as a blocker.
- Independent read-only review agrees on the preflight gate.
- A durable pause/preflight record exists and 8911/5174 remain stopped.

## Risk Boundaries

- Writable paths are limited to this task's `context/`, `runs/`, `reviews/`,
  `metrics/` and LOOP ledger records.
- Runtime SQLite files and medical-writing files are read-only. Do not invoke
  repository constructors against runtime paths because initialization can
  migrate schemas.
- One task-created `/tmp` SQLite backup may be mutated to replay current
  initialization/startup behavior, then removed after evidence capture. It is
  not a runtime authority and must never replace the source database.
- Do not retry/reuse/salvage v4-v8 or make any candidate decision.
- Do not start 8911/5174, provider calls, browsers, workers or real projects.
- Provider-only identity/unique P2 remains a separate schema task.
- Codex owns final verification and acceptance.

## Timeout Policy

- Codex performs the audit directly. Any independent reviewer is launched once
  and receives one hard wait; no fixed-interval polling or duplicate dispatch.
- A slow review remains pending until terminal return or the configured hard
  wait.

## Loop Log

- 2026-08-01 11:57:57: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- Latest global/project AGENTS and verification Skill were read in full.
  Hashes: global `28029e...cd79`, Codex x Hermes overlay
  `606d4a...eb1`, workbench `31d8b1...b001`, Skill
  `40feb6...43a4`.
- Re-anchored from the offline PASS pause, Codex review, Luna round 4 and LOOP
  ledger. Runtime remains frozen pending read-only inspection.
- Read-only path resolution established that `services/api/app/main.py` uses
  `Path(__file__).resolve().parents[5] / "runtime"` unless
  `WORKBENCH_RUNTIME_DIR` is set. The authoritative monitoring database is
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/medical_monitoring_ai.sqlite3`,
  not the workbench-local zero-byte stub.
- Authoritative source database evidence:
  - main database size `123252736`, SHA-256
    `5cb250891b0437e9cffc1121e6956136802f5557a66a0285f723822421db4ba3`;
  - WAL size `692192`, SHA-256
    `a69b489d09a45a05e87a38cfa2399ca1d72eb2c757f3158760aacced97c48ead`;
  - `PRAGMA integrity_check = ok`, journal mode `wal`, `user_version = 0`;
  - the source schema is pre-marker and lacks all three
    `contract_retirement_*` columns.
- Read-only frozen protocol inventory, including the WAL:
  - v4: `8 jobs / 8 attempts / 8 candidates`;
  - v5: `1 / 1 / 0`;
  - v6: `1 / 1 / 0`;
  - v7: `1 / 1 / 0`;
  - v8: `1 / 1 / 0`;
  - v9: `0 / 0 / 0`.
  These values match the prior frozen evidence. Across all versions there are
  zero queued and zero running jobs. The 12 v4-v8 rows comprise two completed,
  seven failed `invalid_ai_output`, three `stale_input` with
  `superseded_job_contract`, no live lease, and eight v4 candidates still
  `proposed`.
- The failed historical v4/v5/v8 rows have no durable retirement marker because
  the source is still pre-migration. They are not automatically claimable, but
  old-process user retry would remain possible until current initialization
  backfills the markers. This is the principal reason runtime startup must not
  be skipped or reordered.
- Static startup-order audit:
  - module initialization constructs `MonitoringAiRepository` first, which
    creates/backfills the marker columns transactionally;
  - the worker constructor starts no thread;
  - startup then retires obsolete task prompt versions, explicitly including
    protocol v3-v8, applies workflow/lease recovery, and only then calls
    `monitoring_ai_worker.wake()`;
  - `retry_terminal()` rejects either a durable marker or any historical
    `superseded_*` code;
  - the startup hook catches exceptions broadly, so a future live start still
    requires immediate post-start schema/marker/count verification rather than
    trusting static order alone.
- A WAL-consistent read-only SQLite `.backup` of the authoritative monitoring
  database was created at
  `/tmp/monitoring-v9-preflight-20260801/medical_monitoring_ai.sqlite3`.
  Current repository initialization plus the current startup retirement
  sequence were replayed only against this disposable copy:
  - integrity remained `ok`;
  - all three marker columns were added;
  - all 12 v4-v8 jobs received a durable marker
    (`3 superseded_job_contract`, `9 superseded_prompt_contract`);
  - job status, attempts, failure evidence and all eight proposed candidates
    remained unchanged;
  - old unmarked retry surface became zero;
  - queued/running remained zero and lease expiry changed zero rows.
  Before and after replay, the authoritative source DB and WAL hashes and
  mtimes were unchanged. The source SHM mtime changed during read-only SQLite
  access, which is an expected WAL shared-memory side effect and not a database
  content mutation.
- Process boundary:
  - ports 8911 and 5174 have no listeners;
  - PID 43191 is an unrelated pre-existing full-app process on port 18911,
    cwd at this workbench, started for the parallel medical-writing lane;
  - its read-only readiness reports ready/schema 16 and its configured
    independent-AI route, but it must not be stopped or exercised through
    monitoring endpoints;
  - its monitoring worker is wake-on-demand and the frozen database has no
    queued/running work. A future v9 canary must explicitly isolate this
    concurrent old-code surface or keep its monitoring routes quiescent.
- The disposable `/tmp` replay copy is pending precise cleanup after the
  independent review. No service, provider, browser, real project, job,
  candidate decision, retry, reuse or salvage action has been invoked.
- The existing native Luna reviewer completed one confirmatory read-only pass
  after one hard wait. It found:
  - a P1 conditional gate because the startup hook swallows prompt-retirement
    exceptions; live readiness cannot substitute for post-start marker/count
    verification;
  - a P1 conditional concurrency gate because the old full app on 18911 shares
    the authoritative database and could become material after a v9 queue row
    exists; passive reliance on nobody calling its monitoring routes is not
    sufficient isolation;
  - a P3 summary omission in the first context draft. A direct read-only
    reconciliation closed it: `2 completed + 7 failed + 3 stale_input = 12`;
  - the provider-only stable-ID/SQLite-unique mismatch remains a separate P2
    and does not block a prompt-version v8-to-v9 canary.
- Luna's exact decision is **CONDITIONAL PASS only for preparing a separately
  controlled one-topic v9 canary**, not permission to run it. Mandatory future
  prerequisites are: resolve the project-level runtime explicitly; create a
  new consistent before-state backup; establish a single controlled monitoring
  execution surface or enforceable fence against 18911; start current code
  without submitting work; and immediately prove integrity, all marker columns,
  the `3 job + 9 prompt` distribution, exact preservation, zero unmarked retry
  surface, zero queued/running and zero v9 before any POST. Any failure is
  fail-closed.
- Final read-only freeze at 2026-08-01 12:14 CST:
  - the five governed offline-cutover hashes still exactly match the accepted
    checkpoint;
  - authoritative DB and WAL hashes, sizes and mtimes still exactly match the
    pre-replay values;
  - 8911 and 5174 have no listeners;
  - the unrelated PID 43191 remains the sole observed listener on 18911 and was
    not contacted or stopped;
  - the disposable replay directory was removed precisely after review;
  - no product source, test, runtime database, medical-writing file, service,
    provider, job, project or candidate state was changed by this task.
