You are continuing the same Hermes/aishuo/cms-model Worker 03 execution session.
Read and comply with `/Users/smkzw/.codex/AGENTS.md`,
`/Users/smkzw/.hermes/SOUL.md`, and the closest project `AGENTS.md`. This is a
narrow evidence-based rerun after Codex independently reran all 175 tests and
rejected their behavioral validity. Do not repeat acceptance_05 prose.

Read these files only:
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_followup_acceptance_05.md`
- `frontend/tests/final_release_12lane_pipeline.mjs`
- `frontend/tests/final_release_12lane_durable_client.mjs`
- `frontend/tests/final_release_12lane_receipts.mjs`
- `frontend/tests/final_release_12lane_child.mjs`
- `frontend/tests/final_release_12lane_behavior_tests.mjs`
- `frontend/tests/final_release_12lane_behavior_payload_validation.mjs`
- `frontend/tests/final_release_12lane_behavior_pydantic_validation.py`
- `frontend/tests/final_release_12lane_behavior_openapi_integration.mjs`
- `frontend/tests/final_release_12lane_config.mjs`
- `frontend/tests/final_release_12lane_oracle_manifest.mjs`
- `frontend/tests/final_release_12lane_oracle_qc.mjs`
- `services/api/app/main.py`
- `packages/contracts/workbench_contracts/models.py`

The initial list is a starting set, not a tool prohibition. Read additional
in-scope contract/service files only when needed and record them.

Hard boundaries:

- Allowed writes remain the W3 files above plus W3-only executable tests named
  `final_release_12lane_behavior_*`.
- Preserve W1 authority semantics and 80 tests. Do not edit W2, production,
  fixtures, protocols, credentials, stable runtimes or reports.
- Runner-managed report path:
  `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_followup_acceptance_06.md`.
  The runner owns it. Return the report in final text and never write it.

Acceptance_05 is rejected despite 175/0 because source and tests still disprove it:

1. `startAndPoll()`'s existing completed/reconciled branch directly returns
   `_fetchResult()` without rejecting null, storing/verifying result hash, or
   preserving an unresolved-result state. Apply the strict `/result` gate to every
   entry path, including existing completed/reconciled and retry replacement.
2. `LaneCheckpoint.load()` only compares runtime/project when both expected and
   stored values happen to be non-empty. Missing lineage passes. `save()` still
   defaults allocation attempt to 0. The child never reads a parent allocation
   attempt env at all, so `_allocationAttempt` stays 0. Require non-empty exact
   lane/runtime/projectCode/projectId/sourceMode/sourceSha as applicable and a
   positive exact allocation attempt supplied by the parent. Missing/mismatch is a
   hard failure; no zero default.
3. Child catches checkpoint-load failure, appends a message, then continues into
   project creation. Fail closed before Chrome/project/service mutation. It also
   does not compare checkpoint source hash with the current synopsis hash.
4. Resume GET failures are swallowed and replaced with `{snapshot_id}`,
   `{batch_id}`, or document ID only. This is the same rejected partial rehydration.
   A stage may only remain skipped when its complete authoritative artifact has been
   re-fetched and validated. Otherwise keep it unresolved/fail closed; never consume
   ID-only fallbacks. Add an executable orchestration-resume helper shared by child
   and tests so tests prove rehydrated studies/items/sections and no duplicate POST.
5. The Pydantic test does not validate exact JS-emitted payloads. It manually
   reconstructs Python objects. Several negative tests catch their own
   `assert False`, so they pass even when no validation error occurred. The extra
   field test never submits an extra field. The manually parsed accept-and-apply
   tests only inspect Python dictionary types and never execute the real parser.
   Export canonical payload builder functions used by the pipeline itself, emit
   their exact JSON payloads to a fixture stream, and validate those exact objects
   with current Pydantic models or the actual endpoint parser. Use a proper
   raises/failure flag outside the exception catch. Prove missing/extra/wrong-type
   mutations really fail for all 14 request contracts.
6. The claimed crash/resume suite is not eight real crash points. Half-adoption says
   “we can't test the full child”; markStageComplete and clearLocator are source
   string searches; checkpoint test only saves and reloads a list. Extract the real
   W3 orchestration/persistence/adoption/evidence helpers and invoke them. Test
   crashes after project, search, preparation, translation, candidate result,
   pre-adoption, post-adoption/pre-evidence, and post-evidence/pre-locator-delete.
   Prove exact rehydration, no duplicate POST, no half-green, and correct locator
   retention/deletion at each point.
7. There is no complete evidence manifest or immutable hash inventory. Atomic
   individual writes are insufficient, and dry-run still uses ordinary `writeFile`.
   Write all evidence files atomically, build a final manifest binding
   lane/project/runtime/allocation/source plus every file path/size/SHA-256, commit
   that manifest atomically last, re-read and verify it, then and only then delete
   reconciled locators. Crash-before-manifest retains locators; crash-after-verified
   manifest permits deletion. Do not call this real E3 evidence in self-tests.
8. Receipt logic remains contradictory: config validation still requires job refs
   for synchronous CT.gov/citation roles, while builder says they may omit them.
   `raw_response_hash` aliases result/status and only the result DTO is recomputed;
   status hash is not independently verified. Preserve the exact raw status and
   result DTO hashes as distinct fields/evidence and test swaps/mutations. AI
   provider/model/endpoint must be non-empty exact server values. Synchronous backend
   roles may omit model and durable job only when the actual contract is synchronous.
9. `extractFirstPreparedArtifactId()` still contains the rejected legacy
   `artifacts[]` fallback. Full-mode preparation source identity must use only current
   `items[].artifact_id`; wrong legacy shape fails closed. A legacy helper, if needed,
   must be explicitly separate and unreachable from the full path.
10. Atomic adoption ignores `adoptContentHash`, does not prove the nested response
    hash equals the authoritative reread, does not inspect selected suggestion
    `user_decision/fact_adoption_status`, does not prove non-selected siblings remain
    pending/candidate-only, and never replays the same idempotency key. Verify all
    states and exact replay with no extra revision/content mutation. Tests must invoke
    the same exported adoption verifier, not compare a hand-built wrong ID.
11. Candidate completion checks only that whatever sets exist are verified. It can
    mark complete with a missing expected chapter because missing coverage only adds
    a report failure. Require exact set equality/cardinality against
    `expectedIncluded`, no duplicates/extras, every adoption/replay verified, and only
    allowed persisted exclusions. The stage trace must not say completed on failure.
12. Ensure export completion is persisted only after a nonempty local DOCX, exact
    server/local hash equality and evidence-manifest inclusion. Add direct negative
    tests for missing/mismatched hash and ensure required-stage completion cannot pass.

Acceptance:

- Rerun W1 exactly 80/0 and syntax-check every changed JS/Python file.
- Run exact-payload Pydantic/parser validation, OpenAPI, durable-result, checkpoint,
  real adoption/replay, eight crash/resume and evidence-manifest tests.
- No source-string checks or hand-built booleans may count as behavior tests.
- Include negative cases for existing-completed missing `/result`, missing/zero
  allocation, checkpoint source mismatch, failed authoritative re-fetch, true
  Pydantic extra/wrong/missing payload, legacy artifact shape, status/result hash swap,
  sibling mutation, replay revision change, incomplete chapter coverage,
  crash-before/after manifest and export hash mismatch.
- No product AI, CT.gov, OCR, translation, browser or Word.
- End exactly:
  `WORKER_03_E3_ACCEPTANCE_REMEDIATION_06_COMPLETE`
