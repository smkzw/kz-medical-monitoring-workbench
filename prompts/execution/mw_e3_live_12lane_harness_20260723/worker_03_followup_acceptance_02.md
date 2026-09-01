You are continuing the same Hermes/aishuo/cms-model Worker 03 execution session.
Read and comply with `/Users/smkzw/.codex/AGENTS.md`, `/Users/smkzw/.hermes/SOUL.md`,
the workspace `AGENTS.md`, and the current files before editing. This is a targeted
same-session remediation, not a new design pass and not a status request.

Read these files only:

- `context/mw_e3_live_12lane_harness_20260723_execution_context.md`
- `plans/codex_execution_mw_e3_live_12lane_harness_20260723.md`
- `records/active_slices/medical_writing_e3_12lane_harness_20260723/PAUSE_CHECKPOINT.md`
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03.md`
- `frontend/tests/final_release_12lane_child.mjs`
- `frontend/tests/final_release_12lane_pipeline.mjs`
- `frontend/tests/final_release_12lane_contract_probe.mjs`
- `frontend/tests/final_release_12lane_durable_client.mjs`
- `frontend/tests/final_release_12lane_receipts.mjs`
- `frontend/tests/final_release_12lane_behavior_tests.mjs`
- `frontend/tests/final_release_12lane_config.mjs`

The initial read list is a starting set, not a tool prohibition. Read additional
in-scope files only when needed to prove a listed defect, and record them.

Hard boundaries:

Allowed writes only:
- `frontend/tests/final_release_12lane_child.mjs`
- `frontend/tests/final_release_12lane_pipeline.mjs`
- `frontend/tests/final_release_12lane_contract_probe.mjs`
- `frontend/tests/final_release_12lane_durable_client.mjs`
- `frontend/tests/final_release_12lane_receipts.mjs`
- `frontend/tests/final_release_12lane_behavior_tests.mjs`
- `frontend/tests/final_release_12lane_config.mjs`, only for ServiceReceipt
  validation and related gate constants/tests; do not change lane/source/oracle data
- optional new W3-only direct test under `frontend/tests/` whose name starts
  `final_release_12lane_behavior_`

Do not edit W2 parent/isolation/stable-hash/process files, production source, stable
runtimes, credentials, authoritative inputs, or report paths. Do not call product AI,
CT.gov, OCR, translation, browser acceptance or Word.
- Runner-managed report path:
  `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_followup_acceptance_02.md`.
  Never invoke write/edit tools to create or update this report. Return the complete
  report in the final response; the runner persists it. Do not create sibling reports.

Codex reproduced the following acceptance failures. Fix all and add deterministic
mock/adversarial tests that fail against the current code:

1. Candidate generation is started twice. The child calls
   `submitCandidateDurable(...)` and then `DurableMwClient.startAndPoll(...)`, which
   POSTs the same route again; the first response is unused. There must be exactly one
   product start per logical step. Remove the duplicate path and prove a mock server
   observes one POST.
2. Idempotency is unstable and split. `buildCandidateRequest` and accept/apply use
   `Date.now()`. Synopsis import constructs two separately timed keys, one inside
   FormData and one passed to the client. Derive one stable key per lane/project/section/
   action/source-context, persist it before start, send that exact key in every relevant
   location, and reuse it after a crash. Never use a new timestamp to recover the same
   logical operation.
3. Locator persistence is non-atomic. `writeFile` can leave truncated JSON, and
   `loadLocators` silently converts malformed content into `{}`, causing duplicate
   product starts. Use atomic temp-write+fsync/rename (or equivalent) and fail closed on
   malformed/mismatched schema/project/lane data. Include schema, project, lane and
   stable step identity. A corrupted locator must block, not restart.
4. Failed/cancelled existing locators currently fall into the start-new-job branch
   instead of an explicit product retry/replacement path. Timeout and synopsis timeout
   state are not consistently persisted. Retry must persist the replacement ID before
   polling, update terminal state, and never re-fire via the original start route.
5. Resume is incomplete across the child journey. Persist a lane checkpoint with
   project_id/source_mode/journey revision and completed stage artifact identities.
   When W2 exposes a resumed runtime, the child must select/reopen that exact existing
   project and continue from durable locators/checkpoint instead of creating another
   project. Fail closed if the project/runtime/locator identity disagrees. Do not use
   request-memory objects as the recovery source.
6. ServiceReceipt validation only checks field presence. Codex proved a
   reasoning-generation receipt with `provider:null`, `model:null`, invented job ID,
   null endpoint/policy/timestamps/hashes currently validates. Require non-empty,
   server-derived identity appropriate to the service role, expected provider/model/
   endpoint match where the policy is fixed, terminal completed status, timestamps,
   policy/prompt identity for AI steps, artifact IDs and redacted input/output hashes.
   Validate product job/run/task IDs against the exact polled result; do not infer
   `source=response_header` merely because a Headers object exists.
7. Receipt provenance currently trusts any object the harness passes. Couple each
   receipt to an immutable raw product response hash plus exact request/locator/result
   identity and reject mismatched IDs. Test forged provider/model, wrong job result,
   missing hashes and cross-step artifact reuse.
8. All-chapter coverage is fail-open. Missing target sections are appended to
   `excludedChapters` and partial completion can still pass; the only gate fires when
   zero candidate sets exist. Produce a deterministic expected included/excluded matrix
   from the product document/study definition, require an explicit design-grounded
   exclusion reason, and fail when any included chapter lacks 3-5 candidates, exact
   evidence, adoption and required rewrite. No first-N sampling.
9. Atomic adoption is only asserted by calling one route. Verify returned thread,
   suggestion, section, revision and content hash; re-read both suggestion/thread state
   and working copy and prove both committed to the same operation. Unchanged/mismatched
   hashes, half-state, stale revision and replay mismatch must fail. Use a stable
   idempotency key and test server-side rollback/fault responses.
10. Durable candidate locator is cleared immediately after adoption even if receipt,
    rewrite, chapter coverage or persisted reconciliation is incomplete. Clear only
    after exact domain reconciliation is durably written. A `/result` 200 alone or a
    later failure must retain enough state for safe resume.
11. `contract_probe` records `full_mode_deferred` as `pass`. Dry/full-deferred work must
    be `skipped`/`not_run`, never pass. Parent/child summaries must distinguish
    deterministic harness readiness from product-stage acceptance.
12. The rewrite start is not driven through the durable client, so it is not polled,
    reconciled or receipted. Route it through the same durable lifecycle and require at
    least one completed rewrite with a valid product receipt in full mode.
13. Chrome ignores the parent-provided `CHROME_PROFILE_DIR` and creates a different
    `/tmp` profile. `startChrome` must use the exact lane-owned profile path supplied by
    W2, expose the real Chrome PID/start identity in child evidence, and never create an
    untracked profile. Cleanup remains exact-path only.
14. The W2 and W3 locator schemas are currently incompatible: W2 expects a wrapper with
    `laneKey/locators`, while the durable client writes a bare step map. Define one
    versioned schema and ensure the parent can detect the exact file the child writes.

Acceptance:
- Existing behavior tests stay green after legitimate expectation updates.
- Add tests for one-start-only, stable idempotency across restart, corrupt locator
  fail-closed, explicit replacement retry, project checkpoint resume, strict/forged
  receipt rejection, cross-result mismatch, partial chapter failure, atomic half-state
  rejection, locator retention and deferred/not-run semantics.
- Run `node --check` on every changed `.mjs` and all W3 tests.
- Return a compact loop trace and exact changed files/tests. Do not claim product-AI,
  browser, DOCX, Word or release acceptance.
- Final response must end with:
  `WORKER_03_E3_ACCEPTANCE_REMEDIATION_COMPLETE`
