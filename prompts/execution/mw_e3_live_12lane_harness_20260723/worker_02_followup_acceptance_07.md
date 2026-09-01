You are continuing the same Hermes/aishuo/cms-model Worker 02 execution session
before the user-mandated 2026-07-24 01:00 Asia/Shanghai route switch. Read and
comply with `/Users/smkzw/.codex/AGENTS.md`,
`/Users/smkzw/.hermes/SOUL.md`, and the closest project `AGENTS.md`.

Codex independently reran acceptance_06 (13/0, 14/0, 7/0) and rejected it
because direct source review proves the key security and resume cases are not
actually tested or correct. Fix only the four root causes below.

Read these files only:
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02_followup_acceptance_06.md`
- `frontend/tests/final_release_12lane_parent.mjs`
- `frontend/tests/final_release_12lane_process_ownership.mjs`
- `frontend/tests/final_release_12lane_runtime_isolation.mjs`
- `frontend/tests/final_release_12lane_isolation_qc.mjs`
- `frontend/tests/final_release_12lane_isolation_adversarial.mjs`
- `frontend/tests/final_release_12lane_isolation_parent_smoke.mjs`

The initial list is a starting set, not a tool prohibition. Read additional
W2-only files when required and record them.

Hard boundaries:

- Allowed writes remain the W2 files above plus W2-only executable tests named
  `final_release_12lane_isolation_*`.
- Do not edit W1, W3, product/stable runtime, fixtures, protocols, credentials,
  source inputs, or reports.
- Runner-managed report path: `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02_followup_acceptance_07.md`.
  The runner owns it. Return the report in final text and never write it.

Rejected residuals:

1. The claimed private allocator authority is public. Lines 319 of
   `process_ownership.mjs` export `_initAllocation`,
   `_allocatorCreateDir`, and `_allocatorResumeDir`. Every ESM importer can
   call them. Worse, the marker is forgeable JSON containing only caller-known
   lane/taskRoot/createdAt, so an importer can create an arbitrary existing
   child directory, write `.mw_e3_alloc`, call `_initAllocation` and
   `_allocatorResumeDir`, then make cleanup delete it. Comments saying
   "internal" do not create an authority boundary. Put allocation and owned-dir
   cleanup behind one cohesive module/API that never exports registration,
   resume-adoption, marker creation, token minting, or owned-dir mutation.
   Public cleanup must operate only on immutable allocation handles created by
   that same closure/module, or use another unforgeable design. Show actual
   exported keys and an adversarial importer that cannot register/delete a
   pre-existing directory even after forging marker/manifest JSON.
2. Resume identity is still inconsistent. `allocateLane()` creates a fresh
   per-process `attemptId` on every call, but `runLane()` passes that fresh ID to
   `checkResume()`, which compares it against the old locator's attempt ID.
   A real locator-bearing resume therefore rejects. Persist one immutable
   allocation/attempt identity used by manifests, locators, checkpoint lineage
   and child env. If a fresh process-run ID is useful, give it a different name
   and never use it for durable resume equality. `QC_ATTEMPT_ID` and
   `QC_ALLOCATION_ATTEMPT` must carry the exact durable identities expected by
   W3.
3. PS-05 is false evidence. Despite its name and comment, lines 246-266 run only
   the first parent invocation and inspect a manifest/marker; there is no second
   invocation, no locator-bearing recovery, no assertion of `resume=true`, no
   child env lineage check and no no-duplicate-work proof. Run parent twice on
   the same task. The first run must leave at least one valid completed locator
   and preserved runtime. The second must pass locator validation, report
   `resume=true`, reuse exact durable identities/runtime/project, pass positive
   allocation attempt to the child, skip duplicate completed work, finish
   green, and leave zero processes/listeners. Add a malformed/mismatched variant
   that blocks before service/child spawn.
4. PS-02 is not the deterministic readiness failure it claims. Its comment says
   `QC_FORCE_SERVICES_FAIL`, but the test sets only
   `VITE_API_PROXY_TARGET=127.0.0.1:1`; that does not itself make Vite readiness
   fail and the observed nonzero result can depend on unrelated local startup.
   Add a dry-test-only, narrowly scoped readiness fault injection in the real
   readiness path. Assert exact `service-startup-failed`, `servicesReady=false`,
   no child spawn, parent nonzero/report false, runtime/evidence preserved,
   stable roots unchanged and zero wrapper/descendant/listener leaks. Keep child
   timeout as a separate test.

Also tighten manifest validation already touched in acceptance_06:

- `evidenceDir` must be present and equal the canonical lane evidence dir, not
  only validated when truthy.
- Runtime and Chrome profile must be exact children of the current task root,
  non-symlink, and bound to the same immutable allocation identity.
- Lane/project/attempt/allocation identities must be non-empty exact matches.
- Missing realpath targets return a stable invalid result.
- A successful resumed lane must follow the documented cleanup/preservation
  policy rather than remaining forever solely because `laneReport.resume` is
  true.

Acceptance:

- Syntax-check every changed file and run every W2 suite.
- Run task-scoped exact green parent, deterministic readiness failure, child
  timeout, malformed locator, and genuine two-invocation resume with completed
  locator.
- Show parent exit/report agreement, child-spawn count, durable identity values,
  runtime/evidence disposition, and zero assigned-port/process-group leaks.
- Show the actual exported keys and a marker+manifest forgery adversary that
  cannot cause deletion.
- No source-string assertion or single-run "resume" test may count.
- Report exact commands, exit codes, counts, changed files, and residual
  uncertainty. No W3/product AI/browser/DOCX/Word claim.
- End exactly:
  `WORKER_02_E3_ACCEPTANCE_REMEDIATION_07_COMPLETE`
