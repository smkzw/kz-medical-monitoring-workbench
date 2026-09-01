You are continuing the same Hermes/aishuo/cms-model Worker 03 execution session
before the user-mandated 2026-07-24 01:00 Asia/Shanghai route switch. Read and
comply with `/Users/smkzw/.codex/AGENTS.md`,
`/Users/smkzw/.hermes/SOUL.md`, and the closest project `AGENTS.md`.

Codex rejected acceptance_07 after direct import-graph and source review. This
is one final, sharply bounded integration pass. Do not add another parallel
test-only abstraction or report aggregate counts from obsolete suites.

Read these files only:
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_followup_acceptance_07.md`
- `frontend/tests/final_release_12lane_behavior_helpers.mjs`
- `frontend/tests/final_release_12lane_behavior_acceptance_07.mjs`
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

Read additional W3 contract/service files only when required and record them.

Hard boundaries:

- Allowed writes remain W3 harness files above plus W3-only executable tests
  named `final_release_12lane_behavior_*`.
- Preserve W1 authority semantics and exactly 80 tests. Do not edit W2,
  product/stable runtime, fixtures, source protocols, credentials, or reports.
- Runner-managed report path: `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_followup_acceptance_08.md`.
  The runner owns it. Return the report in final text and never write it.

Decisive residuals:

1. `final_release_12lane_behavior_helpers.mjs` claims its functions are used by
   the child, but the import graph shows only acceptance_07 and the payload
   emitter import it. Neither `child.mjs` nor `pipeline.mjs` imports
   `verifySourceLineage`, `verifyExportCompletion`,
   `verifyCandidateStageComplete`, `verifyAtomicAdoption`, or
   `commitEvidenceTransaction`. Integrate one production harness helper module
   into the real child path, then make tests invoke those exact imports. Remove
   duplicated inline implementations from the child.
2. `PAYLOAD_BUILDERS` is test-only. The pipeline still constructs request
   bodies inline. Move canonical builders to the pipeline or a shared contract
   module; every actual POST in the W3 pipeline must call them. The Node emitter
   must import those exact builders, not a look-alike fixture builder.
3. The claimed eight crash points are not the required eight orchestration
   boundaries. Acceptance_07 tests project duplicate POST, checkpoint reload,
   cross-lane, cross-project, immediate result, retry, failed locator and
   clearLocator. Implement a resumable stage-transition driver used by the
   child and fault-inject exactly after: project; search; preparation;
   translation; candidate terminal result; pre-adoption; post-adoption before
   evidence; post-verified-evidence before locator deletion. Run the same lane
   workflow to the injected crash, construct a fresh driver/client/checkpoint,
   resume, and prove authoritative GET rehydration, no duplicate completed POST,
   no ID-only fallback, no half-green stage and exact locator retention/deletion.
4. `verifyAtomicAdoption` only compares hand-built objects. It never issues the
   same `accept-and-apply` call twice with the same idempotency key, never
   captures the original exact suggestion set, and never proves no second
   revision/content/state mutation. Add one mock HTTP integration test that
   invokes the actual pipeline adoption function twice with one key and then
   invokes the same verifier used by child against authoritative working-copy
   and thread rereads. Require at least three original suggestions, exact
   selected ID, every non-selected sibling unchanged, and exact replay equality.
5. `commitEvidenceTransaction` is not used by child and does not clear locators
   itself after verification. Integrate it as the only final evidence commit
   path in full and dry modes. The transaction/driver must retain reconciled
   locators for every injected failure before verified manifest; after a
   verified manifest and only then, clear the exact reconciled locators. Tests
   must invoke this path rather than manually tampering then manually comparing.
6. `verifyExportCompletion` accepts a caller-provided boolean
   `header_sha256_matches`; it does not independently compare the header hash to
   the local bytes/hash, and child does not call it. Make the shared verifier
   independently require nonempty bytes/file, nonempty server header hash,
   recomputed local SHA-256 equality, manifest inclusion, and only then stage
   completion.
7. Pydantic says it validates exact payloads, but the builders are not actual
   pipeline builders. Also comments around extra-field mutation say Pydantic may
   ignore extras. The required contract is fail-closed: use endpoint models or
   actual parsers that reject a true extra field. If a current endpoint model
   does not forbid extras, report and fix the harness contract/parser boundary;
   do not mark that mutation passed because the extra was ignored.
8. Remove obsolete false-evidence suites from the accepted command/count list:
   acceptance_06, old behavior_tests source-string cases, and old
   payload_validation simulation cases cannot contribute any pass count. They
   may remain as historical files only if the accepted suite never runs or
   counts them. The new suite must enumerate only awaited executable cases.
9. The async red sentinel is only asserted in prose. Provide a separate
   executable sentinel mode/command that exits nonzero and emits one failed test,
   then run normal green mode separately. Do not edit the source between the red
   and green commands.
10. Require source lineage, candidate exact coverage and adoption verification
    in actual child stage completion. A helper that is only unit-tested cannot
    gate the harness.

Acceptance:

- Show import/call evidence that child/pipeline invoke every shared verifier and
  every canonical builder used by tests.
- Syntax-check all changed files, rerun W1 exactly 80/0, run the separate red
  sentinel and require nonzero, then run only the new accepted W3 suites.
- Run the actual eight-boundary crash/resume workflow and same-key adoption
  replay; report POST counts, rehydrated artifacts, stage/checkpoint/locator
  state and manifest status for each case.
- Run exact pipeline-builder JSON through current endpoint Pydantic/parser
  boundaries with missing/extra/wrong-type rejection.
- Report exact commands, exit codes, one-to-one counts, changed files and
  residual uncertainty. No product AI, CT.gov, OCR, translation, browser,
  DOCX visual, Word or release claim.
- End exactly:
  `WORKER_03_E3_ACCEPTANCE_REMEDIATION_08_COMPLETE`
