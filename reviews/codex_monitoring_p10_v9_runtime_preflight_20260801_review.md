# Codex Review: monitoring_p10_v9_runtime_preflight_20260801

Date: 2026-08-01
Independent review:
`runs/conference/monitoring_p10_v9_runtime_preflight_20260801/general_codex_luna.md`

## Verdict

**CONDITIONAL PASS for preparing a later, separately controlled one-topic v9
canary. The canary itself remains blocked.**

The offline cutover, source startup order and isolated real-snapshot migration
replay are internally consistent. The task does not authorize a live start,
POST, provider call, retry, reuse, salvage, candidate decision or real project.

## Boundary Check

- Codex performed only read-only queries against the authoritative runtime and
  one writable replay on a task-created `/tmp` SQLite backup.
- No product source, tests, medical-writing files or runtime database were
  modified.
- 8911/5174 were never started. PID 43191 on 18911 was observed but not
  contacted, stopped or exercised.
- The native Luna reviewer read only the declared files, changed nothing and
  did not query runtime.
- The `/tmp` replay files were precisely unlinked and their task directory
  removed after evidence persistence.

## Codex Verification

- Path authority: `main.py` resolves the default runtime at the project root;
  the workbench-local monitoring SQLite is a zero-byte stub.
- Frozen source inventory:
  - v4 `8/8/8`;
  - v5 `1/1/0`;
  - v6 `1/1/0`;
  - v7 `1/1/0`;
  - v8 `1/1/0`;
  - v9 `0/0/0`.
- Exact v4-v8 job status reconciliation:
  `2 completed + 7 failed invalid_ai_output + 3 stale_input
  superseded_job_contract = 12`; queued/running are zero.
- Source database:
  - integrity `ok`, WAL mode, pre-marker schema;
  - DB SHA-256
    `5cb250891b0437e9cffc1121e6956136802f5557a66a0285f723822421db4ba3`;
  - WAL SHA-256
    `a69b489d09a45a05e87a38cfa2399ca1d72eb2c757f3158760aacced97c48ead`.
- Isolated snapshot replay:
  - current initialization created all three marker columns;
  - all 12 rows were marked as `3 superseded_job_contract +
    9 superseded_prompt_contract`;
  - status, attempts, provider failure evidence and all eight proposed
    candidates remained unchanged;
  - old unmarked retry surface, queued and running were zero.
- Source DB/WAL hashes, sizes and mtimes were identical before and after the
  replay. The disposable copy was removed.
- Governed offline-cutover hashes remained frozen:
  - contracts `ec63cc67...c8196`;
  - repository `9141cf51...1443`;
  - repository test `a9787efb...5692`;
  - protocol test `9bd1daa3...8b17`;
  - API test `3704acd9...44f0`.
- Final ports: 8911 and 5174 have no listeners; 18911 remains the unrelated
  pre-existing full app.
- Tests, services and browser checks were intentionally not run because this
  was a read-only runtime preflight after an already accepted offline suite.

## Independent Review

Luna independently confirmed the path resolution, initialization-before-claim
order, retry fail-closed behavior and isolated replay sufficiency. It identified
two mandatory conditional gates:

1. the startup hook swallows prompt-retirement exceptions, so readiness alone
   cannot establish migration success;
2. the old full app on 18911 shares the authoritative runtime and becomes a
   material concurrent surface once a fresh queue row exists.

Its initial P3 status-accounting concern was closed by exact read-only
reconciliation. No unsupported runtime/canary/release claim was accepted.
Hermes and other external-provider routes were not used; the independent pass
reused the existing App-native Codex/Luna child session as required by the
current route contract.

## Residual Risk

- A future process can be redirected by `WORKBENCH_RUNTIME_DIR`; its resolved
  path must be proved before startup.
- A later canary requires a single controlled monitoring execution surface.
  Passive reliance on 18911 remaining unused is insufficient.
- Immediately after a no-submit startup, the live database must prove integrity,
  marker columns, `3 job + 9 prompt`, exact historical preservation, zero
  unmarked retry surface, zero queued/running and zero v9. Any mismatch is
  fail-closed before POST.
- Provider-only stable identity versus SQLite uniqueness remains a separate P2
  before provider-only rotation.
- Eight historical proposed candidates remain untouched and unauthorized for
  decision or reuse.
- No provider execution, canary, real project or release condition was tested.
