You are continuing the same Hermes/aishuo/cms-model Worker 02 execution session.
Read and comply with `/Users/smkzw/.codex/AGENTS.md`,
`/Users/smkzw/.hermes/SOUL.md`, and the closest project `AGENTS.md`. Codex
independently reran acceptance_05's 24/15/9 suites and rejected their behavioral
coverage. Fix only the concrete residuals below.

Read these files only:
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02_followup_acceptance_05.md`
- `frontend/tests/final_release_12lane_parent.mjs`
- `frontend/tests/final_release_12lane_process_ownership.mjs`
- `frontend/tests/final_release_12lane_runtime_isolation.mjs`
- `frontend/tests/final_release_12lane_isolation_qc.mjs`
- `frontend/tests/final_release_12lane_isolation_adversarial.mjs`
- `frontend/tests/final_release_12lane_isolation_parent_smoke.mjs`

The initial list is a starting set, not a tool prohibition. Read additional
in-scope W2 files only when required and record them.

Hard boundaries:

- Allowed writes remain the W2 files above plus W2-only executable tests named
  `final_release_12lane_isolation_*`.
- Do not edit W1, W3, production, stable runtimes, credentials, authoritative
  inputs or reports.
- Runner-managed report path:
  `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02_followup_acceptance_06.md`.
  The runner owns it. Return the report in final text and never write it.

Residual defects:

1. PS-01 is not a success assertion. Its comments explicitly allow
   `report.passed=false`, and it only checks exit/report agreement. Require exactly
   parent exit 0, `report.passed===true`, one lane, services ready, child exit 0,
   zero failures, runtime/profile removed, evidence retained, stable roots unchanged,
   and zero listeners/processes.
2. PS-02 does not create a readiness failure. It “just lets it run” and produces a
   child timeout after `servicesReady:true`. Add a narrowly scoped dry-test
   readiness-failure injection that still invokes the real readiness/ancestry and
   cleanup path, then assert an exact service-startup/readiness failure before child
   spawn, parent exit nonzero, report false, runtime preserved and zero leaks. A child
   timeout is a separate failure case and cannot satisfy this test.
3. `_createAllocation` and `_registerAllocatedDir` are called private but are publicly
   exported at line 367. Any importer can create authority for a caller-chosen root
   and register/delete an existing directory. Replace this with a cohesive allocator
   API that never exposes registration/adoption. It may create new owned directories
   itself and resume only an exact prior allocation carrying a durable allocator
   marker/identity inside the runtime. Public callers must not be able to register an
   arbitrary existing directory. Prove the actual exported module surface lacks an
   authority-minting function and an unrelated existing directory survives.
4. IS-20 through IS-24 are still source-string assertions. Replace them with
   executable behavior: real non-green parent exit, malformed locator no-spawn,
   non-dry child-injection rejection, exported-surface cleanup-authority adversary,
   and malicious manifest containment.
5. Resume is internally inconsistent. `allocateLane()` generates a new `attemptId`
   even when loading an existing allocation manifest, then `checkResume()` compares
   the old locator attempt to the new attempt and rejects every genuine resume.
   Persist and reuse immutable allocation identity/positive allocation attempt for
   crash resume. Distinguish any per-process run ID if needed. Pass the positive
   allocation attempt and immutable attempt ID to the child (`QC_ALLOCATION_ATTEMPT`
   plus `QC_ATTEMPT_ID`) for W3 checkpoint lineage.
6. Validate manifest fields exactly, not only containment: evidenceDir must equal the
   canonical lane evidence directory; runtime and Chrome profile must carry matching
   allocator markers and be exact children of the current task root; lane/project/
   attempt/allocation identities must be non-empty and match. Handle missing
   `realpath` targets as stable invalid results, not uncaught exceptions.
7. The rejected-locator branch returns before the normal `finally`, leaving held
   ports/allocation state unreleased until forced process exit. Use one unified
   cleanup/finalization path. Preserve runtime/evidence, but release held sockets and
   leave no listener/event-loop handle.
8. `checkAllPidsDead()` only checks registered wrapper PIDs. Verify assigned API/Vite/
   CDP ports have no listeners and record listener descendants/process-group cleanup.
   Prove no orphan Vite/uvicorn listener survives even when wrapper is gone.
9. PS-08 increments `passed` inside the test and the runner increments it again,
   reporting 9 passes for 8 tests. Count every test exactly once and assert the
   enumerated expected count. Cleanup belongs in suite finalization, not a fake test.
10. Remove all source-string assertions and test-created leftovers. Exact command
    counts must reflect real tests only.

Acceptance:

- Syntax-check all changed files and run every W2 suite.
- Run and retain task-scoped evidence for one exact green parent, one exact readiness
  failure, one child timeout, one malformed locator and one resume success.
- Prove exit/report agreement, runtime cleanup/preservation, immutable allocation
  lineage, child env allocation attempt, evidence retention, and zero wrapper/
  descendant/listener leaks.
- Show the actual exported keys of process-ownership/runtime-isolation and prove no
  caller-facing arbitrary path registration exists.
- No source-string checks may count. No W3/product AI/browser/DOCX/Word claim.
- End exactly:
  `WORKER_02_E3_ACCEPTANCE_REMEDIATION_06_COMPLETE`
