You are continuing the same Hermes/aishuo/cms-model Worker 02 execution session.
Read and comply with `/Users/smkzw/.codex/AGENTS.md`, `/Users/smkzw/.hermes/SOUL.md`,
the workspace `AGENTS.md`, and the current files before editing. This is a targeted
same-session remediation, not a new design pass and not a status request.

Read these files only:

- `context/mw_e3_live_12lane_harness_20260723_execution_context.md`
- `plans/codex_execution_mw_e3_live_12lane_harness_20260723.md`
- `records/active_slices/medical_writing_e3_12lane_harness_20260723/PAUSE_CHECKPOINT.md`
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02.md`
- `frontend/tests/final_release_12lane_parent.mjs`
- `frontend/tests/final_release_12lane_runtime_isolation.mjs`
- `frontend/tests/final_release_12lane_stable_hash.mjs`
- `frontend/tests/final_release_12lane_process_ownership.mjs`
- `frontend/tests/final_release_12lane_isolation_qc.mjs`

The initial read list is a starting set, not a tool prohibition. Read additional
in-scope files only when needed to prove a listed defect, and record them.

Hard boundaries:

Allowed writes only:
- `frontend/tests/final_release_12lane_parent.mjs`
- `frontend/tests/final_release_12lane_runtime_isolation.mjs`
- `frontend/tests/final_release_12lane_stable_hash.mjs`
- `frontend/tests/final_release_12lane_process_ownership.mjs`
- `frontend/tests/final_release_12lane_isolation_qc.mjs`
- optional new W2-only direct test under `frontend/tests/` whose name starts
  `final_release_12lane_isolation_`

Do not edit W1 config/oracle, W3 child/pipeline/durable/receipt/contract files,
production source, stable runtimes, credentials, authoritative inputs, or report paths.
Do not call product AI, CT.gov, OCR, translation, browser acceptance or Word.
- Runner-managed report path:
  `runs/execution/mw_e3_live_12lane_harness_20260723/worker_02_followup_acceptance_02.md`.
  Never invoke write/edit tools to create or update this report. Return the complete
  report in the final response; the runner persists it. Do not create sibling reports.

Codex reproduced the following acceptance failures. Fix all of them and add
deterministic adversarial tests that fail against the current code:

1. Stable inventory is fail-open. `walkDir` skips every dot file and silently treats
   unreadable/racing directories or files as absent. A mutation of `.hidden` currently
   yields `hasChanges:false`. The contract says recursive inventory excludes only an
   explicit allowlist (none by default). Include dot files by default, represent
   symlinks deterministically or fail closed, and carry inventory errors/incompleteness
   into a P0-changing/failing comparison. Never convert an unreadable root into a valid
   empty snapshot.
2. The parent hashes only `…/医学经理工作台/runtime`. The execution context requires the
   stable runtime and stable user-project stores. The currently material roots include
   both `path.resolve(projectRoot, "../..", "runtime")` and
   `path.join(projectRoot, "runtime")`. Implement a deterministic multi-root inventory
   with explicit root labels and aggregate hash; support an env override for an explicit
   root list. Missing/unreadable configured roots fail closed. Before/after/per-lane
   reports must identify every root.
3. `startIdentity` is only registration time. `stopOwnedPid` checks only that a numeric
   PID is in an in-memory registry, so PID reuse can kill an unrelated process. Capture
   an OS-observed process-start identity plus executable/command at registration and
   re-read it immediately before every signal. If identity cannot be proven or changes,
   fail closed and record a mismatch; never signal that PID.
4. The child process is not registered in the ownership registry. Register it at spawn
   time. Ensure timeout/cancellation and parent failure cleanup cover the child and its
   task-owned descendants without process-name matching or broad kill commands.
5. The allocated Chrome profile is never registered in the parent registry, so normal
   cleanup leaks it. Ensure every task-owned runtime/profile directory is in an
   allocation ownership record independently of whether Chrome started. Cleanup must
   remove only exact task-owned paths and must reject path escape, shared paths and
   cross-lane paths.
6. Crash resume is false today: `allocateLane` creates a new runtime/project identity,
   while `checkResume` reads old locators from the reused evidence directory. Persist an
   allocation/runtime manifest atomically. A resumed lane must reopen the same isolated
   runtime and project identity while allocating fresh free ports/profile/attempt ID.
   A fresh successful lane may clean its runtime only after evidence proves there are no
   unresolved locators; a failed/timed-out/interrupted lane must preserve it. Do not
   claim that child-level project selection is fixed here; expose the exact resume state
   to W3 through environment/manifest and test that boundary.
7. Resource startup and lane execution need `try/finally`: a spawn error, readiness
   failure, child exception, stable-hash failure or report-write failure must still stop
   only verified task-owned processes and preserve evidence/runtime as required.
8. Port allocation has a check-then-release race. Either reserve sockets until service
   bind handoff or implement a bounded bind-retry that reassigns the lane port and
   records the replacement. Add a deterministic collision test; a remembered integer
   alone is not a reservation.
9. Reject invalid execution cardinality. `QC_MAX_CONCURRENCY=NaN` currently creates
   zero workers and can pass, and dry-run with an unknown lane can run zero lanes.
   Require a finite integer 1 or 2, reject an empty lane selection in every mode, and
   fail unless completed results exactly equal selected lanes.
10. HTTP readiness cannot accept arbitrary `<500` responses from a process that stole
    the port. Require a product health payload carrying the expected lane/runtime
    identity or another deterministic per-process nonce before declaring readiness.

Acceptance:
- Existing isolation QC stays green after legitimate expectation updates.
- New tests prove hidden-file mutation, incomplete inventory, PID identity mismatch,
  child registration, profile cleanup, cross-lane/path-escape rejection, multi-root
  mutation, interrupted-runtime preservation, same-runtime resume and port collision.
- Run `node --check` on every changed `.mjs` and all W2 tests.
- Return a compact loop trace and exact changed files/tests. Do not claim product-AI,
  browser, DOCX, Word or release acceptance.
- Final response must end with:
  `WORKER_02_E3_ACCEPTANCE_REMEDIATION_COMPLETE`
