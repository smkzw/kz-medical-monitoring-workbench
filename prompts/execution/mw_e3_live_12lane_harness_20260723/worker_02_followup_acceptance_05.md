You are continuing the same Hermes/aishuo/cms-model Worker 02 execution session.
Read and comply with `/Users/smkzw/.codex/AGENTS.md`,
`/Users/smkzw/.hermes/SOUL.md`, and the closest project `AGENTS.md`. This is a
narrow evidence-based rerun after Codex rejected acceptance_04. Do not repeat its
prose or treat test count as acceptance.

Read these files only:
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02_followup_acceptance_04.md`
- `frontend/tests/final_release_12lane_parent.mjs`
- `frontend/tests/final_release_12lane_process_ownership.mjs`
- `frontend/tests/final_release_12lane_runtime_isolation.mjs`
- `frontend/tests/final_release_12lane_isolation_qc.mjs`
- `frontend/tests/final_release_12lane_isolation_adversarial.mjs`
- `frontend/tests/final_release_12lane_isolation_parent_smoke.mjs`

The initial list is a starting set, not a tool prohibition. Read additional
in-scope W2 files when required and record them.

Hard boundaries:

- Allowed writes remain exactly the W2 files authorized in acceptance_04 plus
  W2-only executable tests named `final_release_12lane_isolation_*`.
- Do not edit W1, W3, production source, stable runtimes, authoritative inputs,
  credentials, or any runner report.
- Runner-managed report path:
  `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02_followup_acceptance_05.md`.
  The runner owns this path.
  Return the report in final text and never write that path.

Acceptance_04 is rejected by its own report and source:

1. Its claimed “successful real parent” actually timed out the child, produced
   `exitCode:null`, preserved runtime, and was non-green. PS-01 accepts any parent
   exit and any report. It never requires `report.passed===true`, lane exit 0,
   services ready, runtime removed, or parent exit 0.
2. PS-02 through PS-08 are source-string assertions, not behavior. The assignment
   explicitly prohibited this. The foreign-listener, listener-inspection-unavailable,
   startup failure, invalid manifest, process-group cleanup and atomic-write cases
   must invoke actual exported functions or the real parent process.
3. `main()` writes `report.passed` but never sets `process.exitCode=1` when the
   report is non-green. A failed suite can therefore exit 0. Exit code and report
   status must agree.
4. `checkResume()` returns `rejected:true` for malformed/mismatched locators, but
   `runLane()` ignores it and starts fresh. Reject before any service or child spawn,
   preserve runtime/evidence, emit a stable failure, and perform no duplicate POST.
5. `_issueAllocationToken()` is publicly exported and not lane/path/root bound. The
   adversarial test itself proves any caller can mint a token, register any temp
   directory and delete it. This is forgeable authority, not allocator-issued
   authority. Make directory deletion capability private to the allocator contract,
   bind it to exact lane + canonical task root + exact allocated path, consume or
   revoke it appropriately, and expose only a bounded allocator registration API.
   Tests may use a dedicated non-production test harness export only if it cannot
   authorize an arbitrary external path.
6. Resume allocation trusts an existing manifest's `runtimeDir` if it merely exists.
   `loadAllocationManifest()` does not receive/validate the current canonical
   `taskRuntimeRoot` or `evidenceRoot`; a crafted manifest can point to an unrelated
   existing directory, which is then registered and later deleted. Require exact
   canonical containment, expected per-lane allocation naming/identity, evidence
   path, lane, project, attempt lineage and non-symlink status. A malicious manifest
   pointing outside the current task root must fail closed and leave the target.
7. Job-locator save is non-atomic and omits immutable project/attempt lineage.
   `loadJobLocators()` permits a missing project code and `countUnresolvedLocators()`
   returns zero for a malformed/missing wrapper. Align with the accepted versioned
   W3 wrapper: atomic write + fsync/rename/dir-fsync, required lane/project/attempt/
   schema, strict malformed handling, and explicit resolved semantics. Missing or
   malformed records are not silent success when a locator file exists.
8. A successful lane must prove all registered process identities are gone after
   cleanup. The current PS-01 catches `process.kill` errors but never fails if the
   PID is alive. Fail on any surviving owned PID, PGID descendant, or listener.
9. The created stub-child helper in the smoke test is never used. Add a narrowly
   scoped test-only child injection to the harness, fail closed outside dry/test
   mode, and run the real parent with the real API/Vite service lifecycle plus the
   injected deterministic successful child. This is W2 orchestration evidence only,
   not W3/product-AI evidence.
10. Run a real deliberate startup/readiness failure through the parent, not a
    nonexistent-stable-root shortcut. Prove parent exit nonzero, `report.passed=false`,
    exact failure code, runtime/evidence preserved, and zero owned process/listener
    leaks.
11. Remove any task-created `_debug_*`, temporary scripts or ad hoc files after their
    evidence is captured. Do not leave unlisted write artifacts.

Acceptance:

- `node --check` every changed `.mjs`.
- Execute all W2 QC/adversarial/real-parent tests.
- Run a real one-lane dry parent success in a fresh isolated root with
  `PRESERVE_QC_RUNTIME=0` and deterministic test child. Require:
  parent exit 0, `report.passed=true`, exact one-lane cardinality, servicesReady,
  child exit 0, zero failures, stable roots unchanged, runtime and Chrome profile
  removed, evidence retained, and no surviving process/listener.
- Run a real service-readiness failure. Require:
  parent exit nonzero, `report.passed=false`, runtime preserved, evidence retained,
  and no surviving process/listener.
- Run negative tests for foreign listener, unavailable/inconclusive listener
  inspection, malicious allocation manifest outside root, malformed/mismatched
  locator, forged cleanup authority, stale PID identity, and non-green exit-code
  agreement.
- Show exact commands and counts. Do not claim W3, product AI, browser, DOCX, Word,
  or release acceptance.
- End exactly:
  `WORKER_02_E3_ACCEPTANCE_REMEDIATION_05_COMPLETE`
