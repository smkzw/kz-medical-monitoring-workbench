# Task Context: monitoring_p10_v9_isolated_canary_20260801

Created: 2026-08-01 12:17:52
Objective: Run exactly one fresh v9 visit_window_and_order canary on a 21-database isolated real-runtime snapshot, with zero-submit migration gates, one long wait, terminal stop, independent review, and no impact to 18911 or authoritative runtime
Task type: `code_open_audit`
Risk: `critical`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem under this workbench.
- `context/monitoring_p10_v9_runtime_preflight_pause_20260801.md`
- `reviews/codex_monitoring_p10_v9_runtime_preflight_20260801_review.md`
- `runs/conference/monitoring_p10_v9_runtime_preflight_20260801/general_codex_luna.md`
- The 21 SQLite main databases directly under
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/`, read-only
  as the authoritative before-state.
- Real RUX project `proj_rux_03_002`, confirmed protocol
  `protov_21c4b5a4a3883a8119d74e18`, and only topic
  `visit_window_and_order`.
- Current governed source and tests:
  - `services/api/app/monitoring_ai_contracts.py`
  - `services/api/app/monitoring_ai_repository.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
  - `services/api/app/monitoring_protocol_preparation_router.py`
  - `tests/test_monitoring_ai_repository.py`
  - `tests/test_monitoring_protocol_preparation.py`
  - `tests/test_monitoring_ai_api.py`

External-discovery decision: no new web/package scan. The technical route was
already established and independently reviewed in the immediately preceding
preflight; this task exercises the existing open-source SQLite/Uvicorn product
runtime without choosing a dependency, architecture, or external tool.

## Scope

- In scope:
  - create a fresh per-database-consistent backup of all 21 authoritative
    runtime main databases;
  - create a separate writable clone under this task's run directory;
  - start exactly one current-code backend on 8911 with
    `WORKBENCH_RUNTIME_DIR` explicitly bound to that clone and worker
    parallelism one;
  - before any POST, prove child-process runtime identity, readiness/schema,
    provider identity, source integrity, marker columns, all 12 v4-v8 markers,
    exact historical preservation, zero old retry surface, zero queued/running
    and zero v9;
  - submit exactly one fresh v9 `visit_window_and_order` request for the
    confirmed real RUX protocol;
  - observe through one uninterrupted hard-wait controller, capture terminal
    evidence, and stop 8911 immediately;
  - verify authoritative runtime hashes/state and 18911 remain untouched;
  - obtain same-session independent read-only scientific/structural review and
    run proportionate focused/adjacent regression only after teardown.
- Out of scope:
  - any authoritative-runtime write or migration;
  - stopping, contacting or exercising the existing 18911 full app;
  - 5174, browsers, MY009, other real projects, other topics, retries, reuse,
    salvage, mapping or candidate decisions;
  - product-source or medical-writing edits;
  - provider-only identity/SQLite uniqueness remediation;
  - release or full-Goal acceptance.

## Success Criteria

- Backup contains exactly 21 main SQLite files; all 18 non-empty copies return
  `PRAGMA integrity_check=ok` and the three empty files remain zero bytes.
- Writable canary runtime is a distinct path whose initial main-file hashes
  match the backup.
- Only 8911 is started by this task; 5174 remains stopped and 18911 remains the
  untouched parallel full app.
- Child environment proves the exact isolated `WORKBENCH_RUNTIME_DIR`;
  readiness is ready/schema 16 with no missing capabilities and the independent
  product-AI route is configured.
- Before POST, current startup has added the three retirement marker columns;
  exactly 12 v4-v8 rows are marked with `3 job + 9 prompt`; exact statuses,
  attempts, provider failure evidence and eight proposed candidates match the
  before-state; unmarked retry surface, queued/running and v9 are zero.
- Exactly one 202 POST creates one fresh v9 job for only
  `visit_window_and_order`; no other v9 topic/project exists.
- Exactly one hard-wait observer returns terminal success or fail-closed
  failure without repeat POST/retry. Evidence includes job, attempt, request
  and response hashes, repair lineage, candidates/failure and diagnostics.
- 8911 is stopped immediately after terminal capture. Authoritative DB/WAL
  hashes and frozen counts remain unchanged.
- Independent review and Codex verification determine the next gate. No
  candidate decision is made.

## Risk Boundaries

- Authoritative runtime is read-only. Writable runtime paths are limited to:
  - backup:
    `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/backups/pre_loop316_protocol_v9_isolated_canary_20260801_1220CST/`;
  - task clone and runtime evidence:
    `runs/execution/monitoring_p10_v9_isolated_canary_20260801/`;
  - this task's existing `context/`, `runs/`, `reviews/`, `metrics/`, prompt and
    LOOP-ledger records.
- The backup is immutable evidence after creation; only the task clone may be
  mutated by startup and the single canary.
- An existing process on 18911 shares the authoritative runtime. Isolation is
  achieved only by the 8911 child's explicit task-clone runtime binding; do not
  rely on 18911 inactivity and do not stop or contact it.
- Do not print credentials or the full child environment.
- Any pre-POST mismatch stops 8911 and fails closed without a POST.
- The start endpoint may retry a same identity. It may therefore be called
  exactly once only after proving v9 count zero in the clone.
- No candidate decision, retry, reuse or salvage is authorized.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- One canary POST followed by one uninterrupted hard-wait observer with a
  30-minute ceiling. The observer may perform bounded read-only status checks
  internally, but the parent issues no fixed-interval controller polls.
- No repeat POST, retry, re-dispatch or provider status prompt. Terminal
  success, terminal failure or the hard-wait ceiling ends observation; 8911 is
  then stopped before analysis.
- Independent review reuses the existing native Luna session once and receives
  one hard wait.

## Loop Log

- 2026-08-01 12:17:52: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- The first init attempt used an unsupported descriptive task type and failed
  before creating files. Re-initialization used the guard's supported
  `code_open_audit` route at critical risk, retaining Codex direct authority.
- Re-anchored the latest unchanged global/workspace/workbench AGENTS and
  verification Skill by SHA-256, the preflight pause/review, governed source
  hashes, stopped 8911/5174 and untouched PID 43191 on 18911.
- Created the fresh backup and distinct writable clone at the declared paths.
  Exactly 21 main files exist in each. All 18 non-empty backup databases passed
  immutable read-only `PRAGMA integrity_check=ok`; three empty files remain
  zero bytes; all 21 clone files initially matched their backup byte-for-byte.
  The backup monitoring DB SHA-256 is
  `bca845bc43380663115c59169613fe9687e61da1d6f91278d4b0e67031edadee`.
- The standalone WAL-mode backup correctly required immutable read-only access
  in the integrity probe because no WAL/SHM sidecars are present. No backup
  file was changed by the failed plain read-only probe.
- Pre-start v4-v8 fingerprints, excluding future retirement-marker columns:
  - jobs:
    `85eb5fbc1d1354e643fd1c0792e098b60ffee99fac62a5d07e5bdc9e14715e97`;
  - attempts:
    `e5530e5e48e9cf7751cc5e141c17fa907b03516aaad7bb0ea0cab2f697430f63`;
  - candidates:
    `ddb85eca55c329da7db2e7747e23bd5613f46ca25b346ba0657c0b9d4aed8ee2`.
  Exact status is `2 completed + 7 failed + 3 stale_input`, with 12 attempts,
  eight proposed candidates, zero queued/running and zero v9.
- Attempt 1 started only 8911 on the declared isolated clone, with child PID
  92501 proving the exact `WORKBENCH_RUNTIME_DIR` and parallelism one. The
  zero-submit gate failed before any POST:
  - readiness was blocked only on missing `independent_ai`;
  - the clone contained the 21 main SQLite databases but omitted the
    runtime-root AI settings/secret/binding files and source registry/artifacts,
    so the gateway was disabled and the real protocol source returned 404;
  - startup correctly produced all 12 markers (`3 job + 9 prompt`), zero
    unmarked rows, zero queued/running and zero v9;
  - attempts and candidates matched the before fingerprints, but every
    historical job's `updated_at` changed to the startup-retirement timestamp.
- The `updated_at` delta is a newly observed product audit issue, not merely a
  harness omission. `_apply_contract_supersession()` always updates
  `updated_at` while adding markers even to preserved terminal/already-stale
  rows, despite the separate `contract_retired_at`. This destroys the original
  terminal/stale last-transition timestamp. The canary remains fail-closed
  until a separate offline corrective is reviewed and verified.
- Attempt 1 received zero POSTs and zero provider calls. 8911 was gracefully
  stopped immediately. Its clone is preserved read-only-by-convention at
  `runs/execution/monitoring_p10_v9_isolated_canary_20260801/runtime_attempt1_zero_submit_failed/`.
- Current process evidence corrected the preceding preflight assumption about
  18911: PID 43191 explicitly uses its own temporary
  `WORKBENCH_RUNTIME_DIR=/private/var/folders/.../runtime_glm_retest4`, not the
  authoritative project runtime. It remains untouched and is not a shared
  queue surface for this canary.
- The timestamp corrective passed Pi execution, Codex regression,
  real-snapshot replay, Luna review and its review gate. Attempt 2 was built
  fresh from the frozen 21-DB backup plus a task-owned supplemental snapshot of
  the required runtime-root AI/source components.
- Attempt-2 zero-submit gate passed:
  - child PID 17767 proves `runtime_attempt2` and parallelism one;
  - readiness ready/schema 16/no missing capability;
  - independent AI
    `alibaba_token_plan/qwen3.8-max-preview`;
  - real RUX protocol/source revision resolved;
  - integrity `ok`, three marker columns, `3 job + 9 prompt`, zero unmarked,
    zero queued/running/v9;
  - all three historical fingerprints exactly equal the frozen before-state.
  Exactly one visit-topic POST is now permitted; no other mutation is allowed.
- Exactly one permitted POST returned HTTP 202 and created v9 job
  `monai_5f66dc5d1c9c77c561a637389bc2`. One uninterrupted bounded observer
  returned terminal `failed / invalid_ai_output` after approximately nine
  minutes. There was no repeat POST, retry, reuse, salvage or candidate
  decision.
- The sole terminal error is candidate 3
  (`计划访视改期与补访原则`): `visit protocol candidate must contain exactly
  one visit action family`. The attempt contains exactly the initial provider
  output plus one controlled repair, and zero persisted candidates.
- Task-owned 8911 was stopped immediately after terminal capture. 5174 remains
  stopped. The unrelated 18911 process remains on its separate temporary
  runtime and was never contacted or stopped.
- Authoritative monitoring DB/WAL hashes remain exactly
  `5cb250891b0437e9cffc1121e6956136802f5557a66a0285f723822421db4ba3`
  and
  `a69b489d09a45a05e87a38cfa2399ca1d72eb2c757f3158760aacced97c48ead`.
- Read-only reproduction localizes the false dual-family result to one sentence:
  `该原则适用于方案规定的访视，并应以试验流程表规定的时间窗为原始参照`.
  The complete candidate returns `reschedule + schedule`; this sentence alone
  returns `schedule`, while each of the other three sentences does not create
  a second family. Detailed terminal evidence is recorded in
  `runs/execution/monitoring_p10_v9_isolated_canary_20260801/ATTEMPT2_TERMINAL_EVIDENCE.md`.
- v9 is now a preserved terminal failure and is ineligible for retry or reuse.
  Independent scientific/classifier review is in progress before any source
  correction is considered. Any accepted correction must use a fresh prompt
  identity v10.
