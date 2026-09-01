You are continuing the same Hermes/aishuo/cms-model Worker 02 execution session.
Read and comply with `/Users/smkzw/.codex/AGENTS.md`, `/Users/smkzw/.hermes/SOUL.md`,
the workspace `AGENTS.md`, and current files before editing. This is a consolidated
Codex acceptance rerun after a real parent-process reproduction. Do not merely explain.

Read these files only:
- `context/mw_e3_live_12lane_harness_20260723_execution_context.md`
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02_followup_acceptance_03.md`
- all current `frontend/tests/final_release_12lane_{parent,runtime_isolation,stable_hash,process_ownership,isolation_qc,isolation_adversarial,isolation_parent_smoke}.mjs`
- `records/active_slices/medical_writing_e3_12lane_harness_20260723/evidence/w2_real_parent_failure/twelve_lane_parent_report.json`
- `records/active_slices/medical_writing_e3_12lane_harness_20260723/evidence/w2_real_parent_failure/process_ownership.json`

The initial read list is a starting set, not a tool prohibition. Read additional
in-scope W2 files when needed and record them.

Hard boundaries:

Allowed writes remain exactly the W2 files authorized previously, plus W2-only direct
tests named `final_release_12lane_isolation_*`. Do not edit W1, W3, production source,
stable runtimes, credentials, authoritative inputs, or runner reports.
- Runner-managed report path:
  `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02_followup_acceptance_04.md`.
The runner owns that report path;
Return the complete report in final text and never write that path.

Codex ran the real parent command with one lane:

`QC_OUTPUT_DIR=/tmp/mw-w2-realparent-0kcQkb/out
 QC_TASK_RUNTIME_ROOT=/tmp/mw-w2-realparent-0kcQkb/runtimes
 STABLE_RUNTIME_ROOTS=a:/tmp/mw-w2-realparent-0kcQkb/stable_a,b:/tmp/mw-w2-realparent-0kcQkb/stable_b
 QC_MAX_CONCURRENCY=1 PRESERVE_QC_RUNTIME=1
 node frontend/tests/final_release_12lane_parent.mjs --dry-run --lanes=RA_I_SCRATCH`

The report was non-green:
`service-startup-failed:timeout waiting for http://127.0.0.1:59724/ (pid=78566)`.
The expected PID was the `npm` parent, but the actual listener was its node/Vite child,
PID 78603. The Vite root correctly returned HTML, while `waitForServiceReady` required
JSON for every service. The parent did not clean up its process tree: shell, parent,
npm and Vite remained alive until Codex terminated only task-owned PGID 78555. This is
decisive proof that the current parent smoke is a simulation and acceptance_03 failed.

Repair all of the following as one coherent change:

1. Make readiness service-specific. API must validate the real `/api/health` response
   and owned-listener ancestry. Vite must validate an expected HTML/app marker (or a
   deterministic dedicated test marker) and owned-listener ancestry. Do not require
   Vite JSON. Resolve and verify the listener as the spawned process or a proven
   descendant; never compare only to the `npm` wrapper PID.
2. If listener inspection is unavailable or inconclusive, fail closed. Do not accept
   arbitrary valid JSON/HTTP 200 as a fallback.
3. Register and clean the process group/descendant tree. Consume child stdout/stderr
   continuously or redirect to bounded logs so pipes cannot deadlock. Handle spawn
   errors before assuming a PID exists. Every exit path must terminate only confirmed
   task-owned descendants and write the suite report.
4. Replace the current parent smoke simulations with a test that actually spawns the
   parent module/process. It must prove a successful one-lane dry parent exits, writes
   a cardinality-correct green report, leaves no listeners/process descendants, and
   performs cleanup/preservation according to the outcome. Its foreign-listener and
   startup-failure cases must invoke the real parent/readiness/cleanup path rather than
   manually setting booleans or searching source strings.
5. `loadAllocationManifest()` may annotate invalid data, but `allocateLane()` must
   fail closed on malformed/schema/lane/runtime/path mismatch instead of treating it
   as a fresh run. `checkResume()` must also block malformed or mismatched locator
   state rather than silently starting over.
6. Align unresolved-locator counting with the final documented W2/W3 versioned wrapper
   and status field. Failed/cancelled/interrupted entries are unresolved until explicit
   terminal reconciliation says no recoverable work remains; do not infer resolution
   from a different field name.
7. Directory deletion authority must be allocator-issued, not granted merely because
   arbitrary caller code invokes `registerOwnedDir` on an existing temp path. Use an
   unforgeable allocation record/token or an equivalent exact allocator-owned root
   contract, canonical containment and symlink rejection. Add an adversarial test that
   registering an unrelated temp directory cannot make it deletable.
8. Implement bounded bind/reallocation retry, or a deterministic fail-closed path that
   writes evidence and cleans all processes. Manifest/report updates must be atomic.
   Make `input_manifest.json` atomic too.
9. Preserve the runtime on any startup/readiness/child/hash/artifact/reconciliation
   failure. Remove it only after an explicit successful lane result, zero unresolved
   locators and successful integrity checks.

Acceptance:
- `node --check` every changed `.mjs`.
- Run all W2 tests.
- Run the real one-lane dry parent command in a new isolated task temp root with
  `PRESERVE_QC_RUNTIME=0`; show the report, process/listener post-check and exact cleanup.
- Run one deliberate startup/readiness failure and prove non-green report, runtime
  preservation and no process/listener leak.
- Do not claim W3, product AI, browser, DOCX, Word or release acceptance.
- End exactly with:
  `WORKER_02_E3_ACCEPTANCE_REMEDIATION_04_COMPLETE`
