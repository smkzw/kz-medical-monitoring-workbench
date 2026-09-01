You are continuing the same Hermes/aishuo/cms-model Worker 02 execution session.
Read and comply with `/Users/smkzw/.codex/AGENTS.md`, `/Users/smkzw/.hermes/SOUL.md`,
the workspace `AGENTS.md`, and the current files before editing. This is a consolidated
Codex acceptance rerun after source review. Do not restart the design or merely explain.

Read these files only:
- `context/mw_e3_live_12lane_harness_20260723_execution_context.md`
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02_followup_acceptance_02.md`
- `frontend/tests/final_release_12lane_parent.mjs`
- `frontend/tests/final_release_12lane_runtime_isolation.mjs`
- `frontend/tests/final_release_12lane_stable_hash.mjs`
- `frontend/tests/final_release_12lane_process_ownership.mjs`
- `frontend/tests/final_release_12lane_isolation_qc.mjs`
- `frontend/tests/final_release_12lane_isolation_adversarial.mjs`

The initial read list is a starting set, not a tool prohibition. Read additional
in-scope files only when necessary to prove a listed defect, and record them.

Hard boundaries:

Allowed writes remain exactly the W2 files authorized in the preceding prompt, plus an
optional W2-only direct test named `final_release_12lane_isolation_*`. Do not edit W1,
W3, production source, stable runtimes, credentials, authoritative inputs or reports.
- Runner-managed report path:
  `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02_followup_acceptance_03.md`.
The runner owns this report;
return the full report in final text and never write that path.

Codex rejected the previous result after reading the actual source. Repair every item
below and add tests that exercise the parent orchestration rather than helper functions
alone:

1. `runLane()` registers a Chrome placeholder with `pid: 0`, but `registerProcess()`
   rejects zero at line 180. Every real lane therefore throws before readiness. Separate
   owned-directory registration from process registration. Register the exact
   `chromeProfileDir` as an owned resource without inventing a process. Register a real
   Chrome PID only after W3 actually starts Chrome and returns trustworthy identity.
2. `runChildAsync()` exposes the PID only after `close`; the parent registers the child
   after it has exited. Add an `onSpawn`/registration callback (or equivalent) invoked
   synchronously after successful spawn and before awaiting completion. Record exit
   state on close. Cleanup must be able to terminate a still-running child and owned
   descendants. Test the registry while the child is alive.
3. `waitForHttpWithNonce()` unconditionally returns true for any HTTP 200 at line 224,
   so the stated nonce guarantee is false. Do not require production-source edits in
   W2. For API readiness, verify the expected spawned PID/start identity is the listener
   for the allocated port and require the real `/api/health` contract. For Vite, verify
   its spawned process/owned descendant is the listener and require expected app content
   or an injected deterministic Vite marker. A foreign 200 listener must fail. Never
   silently downgrade an expected nonce to status-only acceptance.
4. The held-port handoff order is inverted: API/Vite are spawned while the harness still
   owns the listening socket, then the socket is released. The service can race and exit
   with EADDRINUSE. Release immediately before spawn and combine that with bounded
   bind/readiness retry plus listener-identity verification; if retry allocates a
   replacement, update the lane allocation/manifest/report atomically. A remembered
   integer is not sufficient.
5. `saveAllocationManifest()` claims atomic persistence but directly calls `writeFile`.
   Implement temp file in the same directory, fsync file, rename and fsync directory.
   Malformed, wrong-schema, wrong-lane, missing-runtime or escaped-path manifests must
   fail closed, not become a fresh run. Resume may reopen only an existing task-owned
   runtime and the same project identity.
6. `checkResume()` returns `attemptId: locators.attempt_id`, but the persisted locator
   wrapper stores attempt identity outside the inner map. Align this with the one final
   W2/W3 locator schema after W3 completes; for now parse the documented versioned
   wrapper strictly and reject malformed/mismatched lane/project/runtime identity.
7. Preservation logic treats any existing `job_locators.json` as unresolved forever,
   even if all entries are reconciled, and treats readiness failure with
   `exitCode:null` as successful. Derive unresolved state from strict locator terminal/
   reconciliation fields. Any startup, readiness, child, cleanup, integrity, hash or
   artifact failure preserves runtime/evidence. Cleanup is permitted only after an
   explicit successful lane result and zero unresolved locators.
8. `isSafeRemovalPath()` accepts any path below the OS temp root and broad name patterns.
   Replace pattern-based authority with exact canonical paths registered by the
   allocator, verify `realpath`/parent containment and reject symlink escape. Cleanup
   must not delete an arbitrary temp directory merely because a caller registers it.
9. OS identity validation must require both start identity and compatible command/
   executable. A null captured identity must never become signalable. Ensure process
   groups/descendants are registered or verified without process-name matching.
10. `parseConcurrencyEnv()` uses `parseInt`, so values such as `1x` are accepted. Require
    the complete string to encode exactly integer 1 or 2; do not clamp larger values.
11. Parent error handling must convert every `runLane` exception into a lane result and
    continue/fail deterministically rather than rejecting `Promise.all` before the suite
    report and cleanup are written.
12. The current 12+10 tests are insufficient because all passed despite defects 1-4.
    Add a bounded parent smoke fixture that starts real local API/Vite stubs or injectable
    deterministic equivalents and proves: real lane reaches child, zero-PID placeholder
    is absent, child is owned while alive, foreign HTTP 200 is rejected, bind collision
    retries or fails closed, startup failure preserves runtime, and the final result
    cardinality/report is non-green on orchestration failure.

Acceptance:
- Run `node --check` for every changed `.mjs`.
- Run all W2 isolation tests including the new parent smoke.
- Show exact command/output proving the parent orchestration path, not only helper tests.
- Do not claim W3, product AI, browser, DOCX, Word or release acceptance.
- End exactly with:
  `WORKER_02_E3_ACCEPTANCE_REMEDIATION_03_COMPLETE`
