You are continuing the same Hermes/aishuo/cms-model Worker 03 execution session
before the user-mandated 2026-07-24 01:00 Asia/Shanghai route switch. Read and
comply with `/Users/smkzw/.codex/AGENTS.md`,
`/Users/smkzw/.hermes/SOUL.md`, and the closest project `AGENTS.md`.

Codex rejected acceptance_06 despite the reported 199/0 because direct source
review proves that many tests are false positives or simulations. This is one
self-contained remediation pass. Do not return another count-only report.

Read these files only:
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_followup_acceptance_06.md`
- `frontend/tests/final_release_12lane_behavior_acceptance_06.mjs`
- `frontend/tests/final_release_12lane_behavior_pydantic_validation.py`
- `frontend/tests/final_release_12lane_pipeline.mjs`
- `frontend/tests/final_release_12lane_durable_client.mjs`
- `frontend/tests/final_release_12lane_receipts.mjs`
- `frontend/tests/final_release_12lane_child.mjs`
- `frontend/tests/final_release_12lane_config.mjs`
- `frontend/tests/final_release_12lane_oracle_manifest.mjs`
- `frontend/tests/final_release_12lane_oracle_qc.mjs`
- `services/api/app/main.py`
- `packages/contracts/workbench_contracts/models.py`

Read additional W3 contract/service files when required and record them.

Hard boundaries:

- Allowed writes remain W3 harness files above plus W3-only executable tests
  named `final_release_12lane_behavior_*`.
- Preserve W1 authority semantics and exactly 80 oracle tests. Do not edit W2,
  product/stable runtime, fixtures, source protocols, credentials, or reports.
- Runner-managed report path: `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_followup_acceptance_07.md`.
  The runner owns it.
  Return the report in final text and never write that path.
- Tests may use mock HTTP services, fault injection, temporary files, and
  exported W3 helpers, but they must invoke the same executable helper used by
  the child. Source-string checks, comments, manually recomputed booleans, or
  direct file fabrication that bypasses the helper do not count.

Exact rejected residuals:

1. `final_release_12lane_behavior_acceptance_06.mjs` uses synchronous `test()`
   for async functions at least at lines 114, 124 and 138. `test()` does not
   await the returned Promise, so these tests increment `passed` immediately
   and rejected promises can escape later. Use one runner that always awaits,
   detects unhandled rejection, counts each enumerated test once, and exits
   nonzero on any failure. Add a sentinel test proving an async rejection is
   observed as a failed test rather than a green count.
2. D1 accepts any `Error`. Require the exact exported
   `UnresolvedResultError`, exact step/job identity, persisted unresolved
   locator state, and no returned body.
3. D3 source mismatch only compares `"hash-AAA"` and `"hash-BBB"` in the test.
   Extract and invoke the real checkpoint/source-lineage verifier used by the
   child. Missing source hash and mismatch must fail before Chrome/project/API
   mutation; exact match must resume.
4. D10 hash-swap only proves two JSON values hash differently. Invoke the real
   receipt collector/verifier with independently captured raw status DTO and
   raw result DTO. Mutate/swap either persisted DTO/hash and require rejection.
   Do not reconstruct a receipt whose fields are assumed correct.
5. D7 crash-before/after-manifest directly writes fake files and manually
   deletes a locator. Implement one exported evidence transaction used by the
   child and tests: atomically commit every evidence file, build the final
   manifest last, bind lane/project/runtime/allocation/source and each
   path/size/SHA-256, re-read every listed file, recompute size/hash, reject
   missing/extra/path-escape/hash-swap, then and only then clear reconciled
   locators. Dry-run must use the same transaction. Fault-inject before each
   commit boundary and prove locator retention before a verified manifest and
   deletion only after verified commit.
6. D11 export hash/empty tests manually restate an `if` expression. Extract the
   real export-completion verifier used before checkpoint stage completion and
   manifest inclusion. Invoke it with nonempty matching bytes/header (positive),
   empty bytes, missing header, and mismatched header (negative). A negative
   case must not mark the export stage complete.
7. Incomplete chapter coverage is hand-built set arithmetic. Extract and invoke
   the real candidate-stage verifier used by the child. Require exact
   cardinality and set equality, no duplicate/extra IDs, every atomic adoption
   and idempotent replay verified, and only persisted allowed exclusions.
   Missing one expected chapter must keep the stage incomplete.
8. The claimed eight crash points still do not invoke the real orchestration.
   Extract a shared resumable stage runner/state transition helper used by the
   child. Fault-inject after project, search, preparation, translation,
   candidate result, pre-adoption, post-adoption/pre-evidence, and
   post-evidence/pre-locator-delete. For each point prove authoritative
   rehydration, no duplicate POST for completed work, no ID-only fallback,
   no half-green stage, and correct locator retention/deletion.
9. Pydantic tests still construct Python dictionaries independently. Export
   canonical JS payload builders for every request contract actually emitted
   by the W3 pipeline; make the pipeline call those builders; emit exact builder
   JSON through a Node fixture command; have Python validate those exact
   objects with current Pydantic models or the actual endpoint parser.
   For each contract mutate the emitted object with one missing required field,
   one true extra field, and one wrong type. Do not catch a locally raised
   assertion as validation success. If an endpoint is manually parsed, invoke
   that real parser/handler boundary instead of a look-alike dictionary check.
10. Atomic adoption still lacks a real same-key replay and complete sibling
    proof. Extract one verifier used by child/tests. Capture the original exact
    suggestion ID set, require selected suggestion state/content hash to match
    the authoritative working-copy reread, require every non-selected sibling
    to remain pending/candidate-only, replay the same idempotency key, and prove
    no additional revision/content/state mutation. Empty sibling sets cannot
    satisfy a multi-candidate test.
11. Checkpoint resume and authoritative rehydration must be shared behavior,
    not inline child-only code. Load must require non-empty exact lane,
    runtimeDir, projectCode, projectId, sourceMode, sourceSha when applicable,
    immutable attempt ID, and positive allocation attempt. Failed GET or
    structurally incomplete GET must fail closed before downstream POST.
12. Delete or exclude any obsolete acceptance test that still counts source
    inspection, hand-built booleans, fabricated state, or unawaited async work
    as behavior. Test names and final counts must correspond one-to-one with
    real awaited cases.

Acceptance evidence:

- Syntax-check every changed JS/Python file.
- Rerun W1 exactly 80/0.
- Run exact JS-builder-to-Python validation and all W3 behavior suites.
- Run a deliberate red sentinel separately and show that the runner exits
  nonzero; do not include the deliberate red in the final green count.
- Show executable positive/negative traces for source lineage, status/result
  receipt hashing, eight crash points, evidence transaction, export completion,
  exact chapter coverage, adoption replay/siblings, and failed authoritative
  rehydration.
- Report exact changed files, commands, exit codes, counts, and residual
  uncertainty. Do not claim product AI, browser, DOCX visual, Word, CT.gov,
  OCR, translation, or release readiness.
- End exactly:
  `WORKER_03_E3_ACCEPTANCE_REMEDIATION_07_COMPLETE`
