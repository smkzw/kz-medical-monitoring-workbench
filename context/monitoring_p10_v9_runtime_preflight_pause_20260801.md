# Medical Monitoring P10 v9 Runtime Preflight - No-Loss Pause

Date: 2026-08-01 12:14 CST
State: **preflight closed; CONDITIONAL PASS to prepare a future controlled
canary; actual canary remains blocked**

## Goal Boundary

This checkpoint covers only the read-only runtime/startup preflight after the
offline v8-to-v9 durable-cutover PASS. It is not runtime acceptance, canary
acceptance, release clearance, full P10 completion or full-Goal completion.

## Completed

- Re-read the latest global, workspace and workbench AGENTS plus the
  multi-agent verification Skill.
- Re-anchored the frozen offline cutover evidence and five governed hashes.
- Established the authoritative project-level monitoring runtime database and
  identified the workbench-local zero-byte stub.
- Read-only reconciled all v4-v9 job/attempt/candidate counts and all 12 v4-v8
  status rows.
- Audited repository initialization, marker backfill, prompt/workflow
  retirement, lease recovery, retry failure and worker-wake ordering.
- Replayed current initialization and retirement on one WAL-consistent
  disposable copy of the actual monitoring database.
- Proved the replay adds all markers while preserving historical statuses,
  attempts, provider failure evidence and candidates.
- Reused the existing Luna session once for a read-only contradiction review
  and waited once to terminal completion.
- Precisely removed the disposable copy and confirmed the source DB/WAL remained
  byte-hash and mtime stable.

## Frozen Evidence

- Authoritative database:
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/medical_monitoring_ai.sqlite3`
- Source schema: pre-marker; integrity `ok`; journal mode WAL.
- Source DB SHA-256:
  `5cb250891b0437e9cffc1121e6956136802f5557a66a0285f723822421db4ba3`
- Source WAL SHA-256:
  `a69b489d09a45a05e87a38cfa2399ca1d72eb2c757f3158760aacced97c48ead`
- Protocol inventory:
  - v4 `8 jobs / 8 attempts / 8 candidates`
  - v5 `1 / 1 / 0`
  - v6 `1 / 1 / 0`
  - v7 `1 / 1 / 0`
  - v8 `1 / 1 / 0`
  - v9 `0 / 0 / 0`
- v4-v8 exact statuses:
  - `2 completed`
  - `7 failed / invalid_ai_output`
  - `3 stale_input / superseded_job_contract`
- All versions queued/running: `0 / 0`.
- Isolated replay: all 12 marked as
  `3 superseded_job_contract + 9 superseded_prompt_contract`; zero unmarked
  retry surface; history/candidates unchanged.
- Ports 8911 and 5174: stopped/no listeners.
- Port 18911: pre-existing unrelated full app, PID 43191, left running and
  untouched for the parallel medical-writing lane.

## Independent Gate

Luna decision:
**CONDITIONAL PASS only for preparing a separately controlled one-topic v9
canary.**

Material conditions:

1. The startup hook swallows monitoring-retirement exceptions. Readiness is
   insufficient; immediate post-start database assertions are mandatory.
2. 18911 shares the authoritative database. Once a fresh queue row exists it is
   a material old-code execution surface. Passive reliance on inactivity is
   insufficient.
3. `WORKBENCH_RUNTIME_DIR` must resolve explicitly to the authoritative
   project-level runtime.
4. Provider-only stable identity versus SQLite unique tuple remains a separate
   P2 and must not be folded into this prompt-version canary.

## Next Safe Action

Only when the user next asks to continue, initialize a new Controlled canary
task. Before any POST:

1. Re-read this checkpoint, the task context, Codex review and Luna report.
2. Confirm the five governed hashes and exact source DB before-state.
3. Create a new consistent backup of all 21 runtime main databases.
4. Establish one controlled monitoring execution surface:
   - authorized coordinated stop/maintenance boundary for 18911; or
   - genuinely isolated writable runtime; or
   - enforceable route/worker fence that prevents 18911 from touching the
     shared queue.
5. Start only current code on 8911 without submitting work and explicitly prove
   its resolved runtime path.
6. Immediately read-only assert integrity, all marker columns, all 12 markers
   with `3 job + 9 prompt`, exact historical preservation, zero unmarked retry
   surface, zero queued/running and zero v9.
7. Fail closed and stop 8911 on any mismatch.
8. Only after those gates pass may the new task submit exactly one fresh v9
   `visit_window_and_order` topic, perform one long hard wait, capture terminal
   evidence, stop 8911 immediately, and obtain a same-session Codex/Luna
   read-only review.

Do not retry/reuse/salvage v4-v8. Do not run MY009 or any other real project.
Do not start another topic. Do not make a candidate decision. Do not modify the
parallel medical-writing lane.

## Records

- Task context:
  `context/monitoring_p10_v9_runtime_preflight_20260801_context.md`
- Codex review:
  `reviews/codex_monitoring_p10_v9_runtime_preflight_20260801_review.md`
- Metrics:
  `metrics/monitoring_p10_v9_runtime_preflight_20260801_metrics.md`
- Luna report:
  `runs/conference/monitoring_p10_v9_runtime_preflight_20260801/general_codex_luna.md`

## Stop State

- 8911: stopped
- 5174: stopped
- No task-owned service, worker, provider, browser, runner or long job remains.
- The task-created `/tmp/monitoring-v9-preflight-20260801` directory is absent.
- PID 43191 / 18911 remains intentionally untouched.
