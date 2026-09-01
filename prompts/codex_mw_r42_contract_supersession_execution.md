# Execution contract: v2-to-v3 planner contract supersession

## Objective

Implement the additive, fail-closed v2-to-v3 transition selected by
`runs/codex_mw_r42_contract_bump_retry_migration_review.md` so the mixed
persisted batch can continue without ordinary cross-prompt retry, stale plan
reuse, unnecessary replanning of three accepted plans, or fabricated provider
calls.

## Required behavior

### Accepted v2 plans

- Revalidate each immutable v2 plan against the exact current artifact,
  extraction revision, document hash, ordered source spans, complete contiguous
  coverage, document role, titles, anchors, order, and unchanged downstream
  translation contract.
- Deterministically derive v3 server IDs using the accepted
  `server_canonical_chapter_id_v1` algorithm.
- Save one new immutable migration plan whose namespace explicitly states
  `server_contract_migration_v1`; persist source plan ID, source/target
  fingerprints, source/target prompt versions, transition version, and bounded
  hashes.
- Preserve all v2 rows byte-for-byte. Do not call a planner.
- For this bounded implementation, do not migrate/reuse old-plan chunks or
  integrations. Leave all downstream work pending under the new plan identity;
  this is safer than copying stale chunk state and matches the current r42
  state, where Hy-MT2 failed before an accepted translation.

### Artifact with no accepted plan

- Create one fresh v3 root Flash run with ordinary retry-parent fields empty.
- Persist a distinct contract-supersession edge to the failed generation-2 v2
  Flash source. Validate the exact allowlisted transition plus owner/item,
  batch, artifact, extraction, input hash, deployment profile, source model,
  failed parentless status, and increasing generation.
- Bind supersession identity into semantic payload, fingerprint, persisted run,
  replay verification, and bounded audit.
- The derived sibling creates no planner run and truthfully inherits the
  canonical source outcome.

### Atomicity and compatibility

- Ordinary retry-parent checks remain strict and same-contract.
- Reject simultaneous ordinary retry and contract-supersession lineage.
- Validate migration/supersession intent before durable-job creation or
  business-state mutation. Invalid or ambiguous lineage changes no batch
  attempt, item, idempotency, migration/audit record, or provider count.
- Only the allowlisted transition
  `flash_toc_planning_v0_2_segment_ranges` to
  `flash_toc_planning_v0_3_server_canonical_ids` is accepted.
- Use existing payload JSON and immutable audit/plan/stage records where
  possible; keep repository schema version 8 and avoid a table migration.
- Old payloads parse with empty/default supersession/migration fields.
- Persist only identifiers, versions, hashes, counts, statuses, timestamps,
  and stable codes; no source/prompt/provider/translated text or credentials.

## Read these files only

Read these files only:
- `runs/codex_mw_r42_contract_bump_retry_migration_review.md`
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_upper_layer_execution.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_writing_reference_upper_layer_execution.py`
- `tests/test_writing_reference_upper_layer_contracts.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_document_pipeline_round8.py`

Allowed product/test writes are limited to those same contract, service, and
test files.

## Required mixed persisted-path regression

Use temporary repositories and deterministic fakes; do not access r42 runtime.
Seed batch attempt 2 with:

- one two-item artifact, no plan, failed generation-2 v2 Flash source;
- three one-item artifacts with accepted v2 plans followed by Hy-MT2 failure;
- retained generation-2 metadata on all five items.

Prove:

1. one accepted retry creates attempt 3 atomically;
2. the no-plan artifact creates exactly one v3 Flash root plus one distinct
   supersession edge and no sibling planner call;
3. three deterministic migration plans/records are created with zero planner
   calls and byte-identical v2 sources;
4. no v2 chunk/integration/translation is returned under v3; only pending v3
   downstream work executes;
5. duplicate retry and duplicate worker execution create no extra plan,
   stage, migration, provider, or translation call;
6. reconstructed repository/services after restart reuse the same v3
   migration/supersession identities;
7. an ordinary v2-parent/v3-child request still fails closed;
8. invalid/ambiguous transition makes no durable job or business mutation.

## Hard boundaries

- Do not access or modify original/clone r42 runtime.
- Do not start services, invoke providers, acquire oMLX leases, run
  OCR/translation, or retry items.
- Do not weaken title/range/coverage/source-span/Protocol/OCR/fidelity/anchor,
  ownership, cancellation, or privacy gates.
- Do not edit outside the allowed list except the report below.

## Verification

Run focused transition tests, the six-module planner/translation gate, and any
direct contract/repository tests required by the patch. Report exact outcomes.

## Output

Write exactly one output file:
`runs/codex_mw_r42_contract_supersession_execution.md`

Report design, files, persisted identities, exact tests/outcomes, failed paths,
boundary compliance, uncertainty, and next action. End with
`EXECUTION_COMPLETE`.
