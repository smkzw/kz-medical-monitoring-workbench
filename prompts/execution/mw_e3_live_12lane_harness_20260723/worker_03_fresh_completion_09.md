You are a fresh Hermes/aishuo/cms-model execution worker. The prior W3 session
was honestly stopped after exhausting its accumulated context and made no
acceptance_08 changes. Complete the bounded W3 integration now. Read and comply
with `/Users/smkzw/.codex/AGENTS.md`, `/Users/smkzw/.hermes/SOUL.md`, and the
closest project `AGENTS.md`.

Read first:
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_followup_acceptance_08.md`
- `prompts/execution/mw_e3_live_12lane_harness_20260723/worker_03_followup_acceptance_08.md`
- `frontend/tests/final_release_12lane_child.mjs`
- `frontend/tests/final_release_12lane_pipeline.mjs`
- `frontend/tests/final_release_12lane_durable_client.mjs`
- `frontend/tests/final_release_12lane_behavior_helpers.mjs`
- `frontend/tests/final_release_12lane_behavior_acceptance_07.mjs`
- backend request models/routes actually called by those pipeline methods

The initial list is a starting context, not a tool prohibition. Do not repeat
broad exploration already summarized in the acceptance_08 report.

Hard boundaries:

Allowed writes:
- W3 files named `frontend/tests/final_release_12lane_{child,pipeline,durable_client,
  behavior_helpers,behavior_acceptance_09}*.mjs`;
- the exact backend request-model configuration needed to fail closed on extra
  payload fields, plus its focused tests.
Do not modify W1/W2/W4, fixtures, protocols, credentials, production content,
stable runtime state, or runner reports.

Runner-managed report path: `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_fresh_completion_09.md`.
Return the report in final text; never write that file.

Implement, do not merely recommend:

1. `child.mjs` must import and invoke shared executable helpers for source
   lineage, candidate completeness, adoption verification, export completion
   and evidence commit. Delete or delegate the duplicated inline logic. The
   import graph and runtime call graph must prove the child uses them.
2. Move all request payload builders into `pipeline.mjs`; every actual pipeline
   POST must use exactly one exported builder. Tests and Python/Pydantic probes
   must consume those exact emitted builder objects, not reconstructed fixtures.
3. Make export verification independently stat/read/hash the produced file and
   compare the expected hash. Never accept a caller-supplied
   `header_sha256_matches` boolean as proof.
4. Make `commitEvidenceTransaction` the sole child evidence finalization path:
   write staging, independently re-read/hash/validate required receipts and
   lineage, atomically promote, then and only then mark/clear the durable
   locator. Failure before promotion must retain the locator and prior evidence.
5. Make atomic adoption issue a real HTTP request twice with the same
   idempotency key against the actual mock/API route. Assert one logical commit,
   unchanged non-selected siblings, identical replay response/receipt, and
   atomic rollback on an injected apply failure.
6. Add one resumable stage driver used by the child and by acceptance tests.
   Inject crashes at exactly: project creation, competitor search, preparation,
   translation, candidate generation, pre-adoption, post-adoption and
   post-evidence. For each boundary, restart from persisted state, prove no
   completed POST refires, exact stage continues, lineage remains exact and the
   final transaction commits once.
7. Endpoint parsing must reject extra fields and missing/type-invalid required
   fields. Feed exact JS-builder JSON into the actual Python parser/model and
   endpoint route. Do not let Pydantic's default extra-ignore behavior count as
   validation.
8. Create `final_release_12lane_behavior_acceptance_09.mjs` as the only W3
   acceptance suite. It must use a stable `EXPECT_RED=1` mode or equivalent
   runtime fault mode to prove at least one behavioral sentinel fails before
   integration and passes after integration without editing source between
   red/green. Await every async test. Count each test exactly once.
9. Do not include acceptance_06, acceptance_07, source-string tests, hand-built
   boolean/file simulations, or payload-validation fixtures disconnected from
   actual builders in the accepted count.

Run:
- `node --check` for every changed JS/MJS file;
- the new acceptance_09 suite in red and green modes;
- focused Python parser/route tests using exact emitted builder JSON;
- any existing focused suite needed to prove no regression.

Report exact changed files, import/call graph evidence, commands, exit codes,
one-to-one test names/counts, eight crash-boundary outcomes, adoption POST/commit
counts, evidence transaction/hash/locator outcomes, Pydantic rejection matrix
and residual uncertainty. Do not claim product AI, browser, DOCX, Word or
release acceptance.

End exactly:
`WORKER_03_E3_FRESH_COMPLETION_09_COMPLETE`
