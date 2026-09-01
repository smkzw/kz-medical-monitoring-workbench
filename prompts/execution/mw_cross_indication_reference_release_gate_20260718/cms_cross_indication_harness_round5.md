# Cross-Indication Product E2E Harness Round 5

You are the Hermes / aishuo / cms-model first-line execution worker for one
bounded harness implementation. Read these files only as initial context;
additional adjacent reads are allowed when required to follow actual API and
frontend contracts:

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- project `AGENTS.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TASK_RECORD.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/ACCEPTANCE_CONTRACT.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/CROSS_INDICATION_E2E_MATRIX.md`
- `frontend/tests/cross_indication_e2e_config.mjs`
- `frontend/tests/cross_indication_e2e_parent.mjs`
- `frontend/tests/cross_indication_e2e_child.mjs`
- `frontend/tests/cross_indication_e2e_harness_structure_qc.mjs`
- `frontend/tests/cross_indication_source_contracts.json`
- relevant API decorators and request/response models in
  `services/api/app/main.py` and
  `packages/contracts/workbench_contracts/models.py`
- relevant existing backend/frontend tests for the same routes

Codex remains final authority. Do not claim a full live lane or release.

## Objective

Complete the isolated full-mode harness so it cannot pass unless the product
has actually performed, with observed immutable receipts:

`fresh project through UI -> framing -> fresh ClinicalTrials.gov search ->
official product download -> content validation -> extraction and structure
review -> document-level translation batch -> medical review -> corpus
admission -> evidence-to-chapter mapping -> 3-5 real AI chapter/paragraph
candidates -> working-copy invariance proof`.

Dry-run must still stop before external search/download/production AI.

## Current defects

Codex's source audit found two intentionally red structural gates:

1. `captureSourceReceipt()` fabricates
   `validation_revision: artifact.state_revision || 1` and
   `extraction_revision: "pending"`.
2. The full harness ends after ingest/workspace polling. Translation, medical
   review, admission, chapter mapping and revision-thread candidates are only
   comments, so a lane can appear to finish before the required product
   workflow.

Do not remove the assertions that expose these defects. Implement the missing
behavior until they pass honestly.

## Required behavior

1. Read current multiline FastAPI decorators and Pydantic models with AST or
   another multiline-safe parser. Never infer a request body from comments.
2. After ingest, poll the real product workspace/state until content validation
   and extraction have real immutable records. Capture the actual validation
   ID/revision/status and extraction revision from product responses or a real
   endpoint. Missing data blocks the lane; never substitute artifact revision,
   `1`, `"pending"`, empty strings or fixed placeholders.
3. Follow the existing extraction-review contract with its real
   `expected_revision`, review decision and structure fields. Do not override a
   failing content check just to make the harness pass.
4. Create/execute the real translation-batch preview/create/status workflow.
   Poll terminal state. Require integrated chapter-level candidates with
   nonblank immutable plan/chunk/integration/run lineage. A fidelity-blocked or
   failed item blocks downstream review.
5. For every candidate selected for corpus admission:
   - use its exact translation ID and revision;
   - POST medical review with the actual expected review revision;
   - capture the returned real `review_id`;
   - POST admission with that review ID and exact translation revision;
   - capture the returned evidence brief ID and chapter/M11 anchor.
   Do not approve every document blindly. Limit the formal lane to the
   representative chapters in `REPRESENTATIVE_CHAPTERS` and record why each
   span/chapter was selected.
6. Create real chapter/paragraph revision threads using the currently declared
   `MedicalWritingRevisionRequest`. Use admitted evidence brief IDs and real
   section IDs from the project protocol/working-copy state. Candidate
   generation must return 3-5 suggestions. Record exact suggestion IDs, text,
   rationale, uncertainty and evidence IDs.
7. Before each revision-thread request, read the actual target working copy and
   persist its revision plus a canonical content hash. After candidate
   generation, read it again. The lane passes invariance only when both real
   hashes and revisions exist and are identical. Do not apply/accept any
   candidate in this harness.
8. Candidate/chapter evidence must include:
   indication, phase, NCT ID, source artifact/document, chapter/section,
   source/evidence brief IDs, translation/integration lineage, AI run,
   provider/model/prompt/schema/contract metadata exactly as observed.
9. `quality_scorecard.json` remains `pending_blind_review`; scores and average
   stay null. If any upstream requirement is absent it becomes
   `blocked_before_review`. Never self-score.
10. Fail fast and stop downstream stages after a gate failure. A missing
    response field is `not_observed`, never pass.
11. Keep source payloads bounded. Do not write complete protocol text to run
    logs. Candidate text and the limited source snippets needed for blind
    review are allowed.
12. Preserve the real dry-run behavior already proven: random ports, isolated
    runtime, exactly one UI-created disposable project, SQLite integrity,
    stable runtime byte-for-byte unchanged, cleanup.

## Structural tests

Extend `cross_indication_e2e_harness_structure_qc.mjs` to prove:

- forbidden fixed/fallback validation and extraction revisions are absent;
- full mode calls actual validation/extraction review/translation batch/medical
  review/admission/revision-thread routes;
- route request fields match current Pydantic contracts;
- no downstream candidate status can pass when an upstream receipt is missing;
- 3-5 candidates are captured only from real thread suggestions;
- working-copy invariance requires real before/after hashes and revisions;
- no candidate action/apply route is invoked;
- scorecard cannot become reviewed or receive scores in the harness.

Run:

```bash
node --check frontend/tests/cross_indication_e2e_config.mjs
node --check frontend/tests/cross_indication_e2e_parent.mjs
node --check frontend/tests/cross_indication_e2e_child.mjs
node --check frontend/tests/cross_indication_e2e_harness_structure_qc.mjs
node frontend/tests/cross_indication_e2e_harness_structure_qc.mjs
node frontend/tests/cross_indication_e2e_parent.mjs --dry-run
```

Record exact counts and the dry-run disposable project/ports/runtime cleanup,
SQLite integrity and stable-runtime hash result.

## Hard boundaries

- Modify only the four harness modules, their source-contract JSON, and a
  narrowly required frontend stable selector if no accessible selector exists.
- Do not modify backend translation architecture; a parallel Round 8 worker is
  repairing it.
- Do not touch stable ports 5174/8911, stable runtime, credentials, real project
  rows or real protocol files.
- Do not start the full AD/PNH/obesity/SLE lanes.
- Do not expose environment values or secrets.
- Do not fabricate receipts, hashes, revisions, scores, AI runs or completion.

Write exactly one output file:

`runs/execution/mw_cross_indication_reference_release_gate_20260718/cms_cross_indication_harness_round5.md`

List exact changed files, commands/results, dry-run evidence, unresolved API
dependencies and a compact action/observation/evaluation/decision trace.
