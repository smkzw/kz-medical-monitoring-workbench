You are continuing the same Hermes/aishuo/cms-model Worker 03 execution session.
Read and comply with `/Users/smkzw/.codex/AGENTS.md`, `/Users/smkzw/.hermes/SOUL.md`,
the workspace `AGENTS.md`, and the current files before editing. This is a consolidated
Codex acceptance rerun after source and live OpenAPI review. Do not restart the design
or return an explanation without implementing and testing the repairs.

Read these files only:
- `context/mw_e3_live_12lane_harness_20260723_execution_context.md`
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_followup_acceptance_02.md`
- `services/api/app/main.py`
- `services/api/app/medical_writing_synopsis_import.py`
- `frontend/tests/final_release_12lane_child.mjs`
- `frontend/tests/final_release_12lane_pipeline.mjs`
- `frontend/tests/final_release_12lane_contract_probe.mjs`
- `frontend/tests/final_release_12lane_durable_client.mjs`
- `frontend/tests/final_release_12lane_receipts.mjs`
- `frontend/tests/final_release_12lane_behavior_tests.mjs`
- `frontend/tests/final_release_12lane_config.mjs`
- `frontend/tests/final_release_12lane_oracle_qc.mjs`

The initial read list is a starting set, not a tool prohibition. Read additional
in-scope production API schemas/services only when necessary to prove the current
contract, and record them.

Hard boundaries:

Allowed writes only:
- the seven W3 implementation/test files authorized in acceptance_02;
- `frontend/tests/final_release_12lane_oracle_qc.mjs` only to retain or correct the
  already-made one-line valid-receipt fixture; do not change source/lane/oracle data;
- optional W3 direct tests named `frontend/tests/final_release_12lane_behavior_*`.

Do not edit W2, production source, stable runtimes, credentials, authoritative inputs
or report paths. Do not call product AI, CT.gov, OCR, translation, browser or Word.
- Runner-managed report path:
  `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_followup_acceptance_03.md`.
Never write that report path. Return the complete report in final text.

Codex rejected acceptance_02 because helper tests passed while the real child pipeline
still cannot execute against the current product API. Repair all defects below:

1. Replace every obsolete route/method/body with the exact current FastAPI contract.
   At minimum the current OpenAPI exposes:
   - `POST .../authoring-journey/stages/{stage}/commit`, not `/commit`;
   - `POST .../authoring-journey/competitor-search`, not `/search`;
   - `POST .../references/preparation-batches` plus GET by batch/latest, not `/prepare`
     or `/snapshots/.../preparations`;
   - `POST .../references/translation-batches` plus GET by batch/latest, not
     `/translate` or `/translations/{batch}`;
   - exact document validation/extraction-review routes under
     `/references/documents/{artifact_id}/...`;
   - medical review/admission under
     `/references/translations/{translation_id}/medical-review|admissions`;
   - `POST/GET .../greenfield-document`, not `/documents`;
   - `GET/POST .../working-copies/{section_id}`, not old documents/sections paths and
     not PUT.
   Inspect Pydantic request schemas and supply their real field names/revisions. Remove
   or explicitly skip a stage only when current product design makes it inapplicable;
   never leave a known-dead call in the executable chain.
2. `DurableMwClient._pollJob()` currently returns the status DTO on terminal
   `completed`; `startAndPoll()` then returns it without calling `/result`. On completed,
   require exactly one authoritative `/result` GET and return that result DTO. Persist
   both status-response hash and result-response hash plus artifact locator. A 200
   status object without result must never satisfy artifact/candidate/rewrite gates.
   Failed/cancelled may return terminal status but must not fetch a success artifact.
3. Synopsis public status is `review_ready` (see
   `medical_writing_synopsis_import.py:1941-1967`), not `completed`. Treat
   `review_ready` as the successful result-ready terminal, call `/result`, persist the
   attached journey/result identity, and do not poll until timeout. Preserve
   failed/cancelled semantics.
4. `/result` returns an `artifact` locator. Candidate extraction must support the exact
   current artifact form, including a direct `suggestion_ids` array when present, and
   then fetch the authoritative revision-thread read state when the locator requires
   it. Do not infer 3-5 candidates from status metadata.
5. Fix atomic adoption verification. Re-read the authoritative revision thread/list
   and working copy after `accept-and-apply`; verify project, thread, section,
   suggestion accepted state, exact revision, returned and re-read content hash, and
   idempotent replay equality. Any half-state, stale revision, unchanged hash, missing
   field or replay mismatch fails. Current code checks only two returned IDs and WC.
6. Locator clearing is still unsafe: `candidateSets[]` is only memory and
   `lane_artifacts.json` is written later, yet the locator is cleared immediately.
   Persist an atomic per-step reconciliation record containing request key, exact
   status/result hashes, artifact locator, thread/suggestions, receipt, adopt result,
   re-read state and rewrite state. Only then mark locator `reconciled`; do not delete
   it until the lane evidence bundle is durably committed. A crash at any intermediate
   point must resume without re-starting or losing provenance.
7. Resume checkpoint identity is incomplete. Bind checkpoint and locator wrapper to
   `runtimeDir`, `projectCode`/project ID, lane, source mode, source SHA and allocation
   attempt lineage supplied by W2. All identity fields are required, not conditional.
   Checkpoint save needs same atomic file+directory durability and fail-closed schema/
   path validation. Reopening must verify the project exists in the resumed runtime.
8. The receipt hash is not an exact immutable response hash:
   `JSON.stringify(obj, Object.keys(obj).sort())` drops nested fields. Implement
   recursive canonical JSON and retain the raw status/result hashes in locator and
   reconciliation evidence. `ReceiptCollector` currently only checks hash presence,
   not recomputation. Pass the exact raw response/evidence into verification and
   recompute; bind provider/model/job/artifact to current product fields. Do not invent
   policy/input/output hashes absent from server evidence, and fail the applicable gate
   honestly if the production contract does not expose required provenance.
9. Chapter exclusion remains fail-open: “no matching document section” is not a
   design-grounded exclusion. Build the expected matrix from current product document
   modules plus confirmed study design. Consume each lane's `QC_MIN_CHAPTERS`; every
   required semantic chapter must map to a real section and complete. Optional
   exclusions require a persisted confirmed design feature/reason, never an automatic
   string. No missing mapping may become success.
10. Rewrite retry currently polls but does not collect/persist the retry result receipt
    or fail the lane when rewrite fails; only the first chapter is exercised. Define
    deterministic rewrite applicability, require at least one real completed rewrite
    per full lane, reconcile retry result exactly, and keep failures visible.
11. The contract probe must fetch `/openapi.json` and prove every method/path used by
    the executable pipeline exists. A generic 404/422 cannot prove a route because an
    unknown FastAPI path also returns 404. `dry_run_complete` may pass only the contract
    probe, never G3/G4/product execution. Remove source-string-only assertions for
    behavioral acceptance.
12. Add a no-product-AI integration test using an isolated temporary runtime and the
    real FastAPI app/OpenAPI (TestClient or isolated uvicorn) plus deterministic seeded/
    mock service state as needed. It must fail against the previous old routes and prove
    current request schemas, completed→result, synopsis `review_ready`, exact artifact
    extraction, atomic dual-state/replay checks, locator retention through durable
    reconciliation, and corrupt/cross-runtime resume rejection. Mock regex ordering must
    ensure `/result` is not swallowed by the generic status matcher.
13. Report the acceptance_02 write-boundary violation: it edited
    `final_release_12lane_oracle_qc.mjs` although that file was not authorized. Codex has
    inspected the one-line valid-receipt fixture and permits only that exact correction
    in this pass; make no other W1 change.

Acceptance:
- `node --check` every changed `.mjs`.
- Run oracle, all W3 behavior tests, and the new real-OpenAPI/no-AI integration test.
- Show the exact route manifest and call-order evidence.
- Do not claim W2, product-AI, browser, DOCX, Word or release acceptance.
- End exactly with:
  `WORKER_03_E3_ACCEPTANCE_REMEDIATION_03_COMPLETE`
