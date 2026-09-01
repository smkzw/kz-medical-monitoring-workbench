You are continuing the same Hermes/aishuo/cms-model Worker 03 execution session.
Read and comply with `/Users/smkzw/.codex/AGENTS.md`,
`/Users/smkzw/.hermes/SOUL.md`, and the closest project `AGENTS.md`. This is a
narrow evidence-based rerun after Codex executed source review. Do not repeat
acceptance_04 prose.

Read these files only:
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_followup_acceptance_04.md`
- `frontend/tests/final_release_12lane_pipeline.mjs`
- `frontend/tests/final_release_12lane_durable_client.mjs`
- `frontend/tests/final_release_12lane_receipts.mjs`
- `frontend/tests/final_release_12lane_child.mjs`
- `frontend/tests/final_release_12lane_behavior_tests.mjs`
- `frontend/tests/final_release_12lane_behavior_payload_validation.mjs`
- `frontend/tests/final_release_12lane_behavior_openapi_integration.mjs`
- `frontend/tests/final_release_12lane_config.mjs`
- `frontend/tests/final_release_12lane_oracle_manifest.mjs`
- `frontend/tests/final_release_12lane_oracle_qc.mjs`
- `services/api/app/main.py`
- `packages/contracts/workbench_contracts/models.py`

The initial list is a starting set, not a tool prohibition. Read additional in-scope
contract/service files only when needed and record them.

Hard boundaries:

Allowed writes remain the W3 files above plus W3-only executable behavior tests named
`final_release_12lane_behavior_*` (including one Python Pydantic test if useful).
Preserve the accepted W1 authority semantics and 80 tests. Do not edit W2, production,
fixtures, protocols, credentials or stable runtimes.
- Runner-managed report path:
  `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_followup_acceptance_05.md`.
The runner owns the report; return it in final text and never write that path.

Acceptance_04 is rejected because its own executable source disproves the report:

1. `startAndPoll` lines 155-168 returns `resultDto || body`, and the polled path returns
   `statusResult` when `/result` is missing. Status/embedded start result must never
   satisfy the artifact gate. Throw/persist a distinct unresolved-result failure.
   `retry()` still returns `pollResult`, not the fetched authoritative result. Return
   the real result DTO and retain replacement job identity.
2. `markStageComplete()` fires `_checkpointRef.save(...).catch(()=>{})` without await
   and drops errors. Make it async and await every stage transition. Pass/preserve
   allocation attempt from a parent-provided env/manifest, plus project/lane/runtime/
   source identities. Fsync the checkpoint directory after rename.
3. Resume remains nonfunctional: it rehydrates search as only `{snapshot_id}` with no
   studies, preparation/translation as only batch IDs, and document as only ID with no
   sections. Skipped stages then consume null/partial state. Persist the exact required
   stage artifact payloads or re-fetch them from authoritative GET endpoints before
   downstream use. Add executable resume tests that run the same orchestration helper,
   not source-string assertions.
4. The new “Pydantic payload validation” never validates against a Pydantic model or
   even the fetched OpenAPI schema. It only checks values are not undefined, and its
   forbidden-field test merely confirms the clean object lacks the manually injected
   field. Add a real Python/Pydantic validator (or equivalent actual schema evaluator)
   importing the current request models. Validate the exact payloads emitted by
   pipeline builders and prove missing/extra/wrong-type mutations raise validation
   errors. Test all 14 contracts, including the manually parsed accept-and-apply body.
5. D12 half-adoption and mark-stage tests are simulations/source-string checks. Execute
   the real exported verification/persistence functions. Eight crash points must prove
   stage rehydration, no duplicate POST and no half-green result.
6. The child declares global `let durableClient=null` but creates a shadowing
   `const durableClient` inside main. Post-evidence locator deletion therefore never
   executes. Remove shadowing. Conversely, do not delete any locator when lane/report
   is non-green or its step has a gate/failure.
7. Evidence “durable commit” uses ordinary `writeFile` for lane artifacts and report.
   Implement same-directory temp + file fsync + rename + directory fsync. Only after
   the complete evidence manifest and hashes are committed may reconciled locators be
   removed. Simulate crash before and after commit.
8. Candidate receipt hashing currently chooses `statusHash || resultHash`, then
   recomputes against the result DTO. A valid result therefore fails whenever the
   status hash differs. Store and verify status and result hashes separately; never let
   one substitute for the other. Bind lane/project/job/artifact. Synchronous CT.gov or
   citation responses must not be forced to invent a durable job ID, while genuinely
   durable roles must have one.
9. Source receipt still reads `report.preparationBatch?.artifacts?.[0]` after the new
   real `items[].artifact_id` helper. Use the same proven artifact identity everywhere;
   remove the legacy fallback from the full-mode path so wrong shapes fail closed.
10. Atomic adoption checks allow missing IDs/revisions to pass using `!value || equal`.
    Require non-empty exact nested working-copy ID/revision/section/hash, exact thread
    and suggestion, selected suggestion state, non-selected sibling states, and
    idempotent replay. Missing fields fail.
11. Candidate stage is marked completed even with missing/unverified sets. Mark it only
    after exact required-chapter coverage and all adoptions pass. Export is never marked
    complete at all, so every real lane fails required-stage verification. Mark export
    only after a non-empty hash-matched DOCX result.
12. Checkpoint load does not validate projectCode or allocation attempt itself, and
    save defaults allocation to zero on every per-stage call. Make both immutable
    required lineage values and reject mismatch/missing values.

Acceptance:
- Run the accepted W1 oracle QC and require exactly 80/0.
- Syntax-check all changed JS/Python.
- Run explicit W3 behavior, OpenAPI, real Pydantic payload and real crash/resume tests.
- Tests must invoke exported production-harness functions; source-string/manual boolean
  simulations do not count.
- Add negative cases for missing `/result`, retry result, async checkpoint failure,
  partial resume, evidence crash, shadowed client, status/result hash swap, wrong
  prepared artifact, missing nested adoption fields, failed candidates and export.
- No product AI, CT.gov, OCR, translation, browser or Word.
- End exactly:
  `WORKER_03_E3_ACCEPTANCE_REMEDIATION_05_COMPLETE`
