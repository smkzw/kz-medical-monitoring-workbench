# CMS Document-Level Planning And Chapter Translation Round 7

Implement the P1 architecture gate that remains after the focused Round 6
translation-revision convergence. Do not begin until Codex has confirmed Round
6 source/tests are accepted. Read current source after Round 6; line numbers in
older reports are evidence only.

## Read these files only as the initial context

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- project `AGENTS.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TASK_RECORD.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/ACCEPTANCE_CONTRACT.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/CROSS_INDICATION_E2E_MATRIX.md`
- `runs/execution/mw_cross_indication_reference_release_gate_20260718/grok_document_planning_chunking_manager.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference.py`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/main.py`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- `frontend/src/features/writing-reference/progressJourneyLogic.mjs`
- related writing-reference/chapter-translation tests

Additional adjacent reads are allowed when necessary to preserve actual API,
repository, frontend and test conventions.

## Confirmed defect

The batch creates one item per source span and calls
`translate_chapter()` for each item. `translate_chapter()` runs Flash planning,
Hy-MT2 and Flash QC for every span. A 119-200 page Protocol therefore repeats
document/TOC planning hundreds of times, sends fragmented sentences to Hy-MT2,
and performs fragment QC rather than chapter integration. This violates the
approved workflow:

`one document plan -> ordered chapter chunks -> Hy-MT2 by chunk -> chapter and
chunk-boundary Flash QC -> medical review -> corpus admission`.

## Architecture decisions

1. Keep the current PyMuPDF extraction and GLM-OCR-bf16 dual-channel lineage.
   Do not install Docling or replace parsing/OCR. Adopt only the mature
   hierarchy-aware/token-bounded ideas:
   - preserve heading/section hierarchy;
   - split only oversized units;
   - merge undersized adjacent peers under the same chapter;
   - repeat a detected table header when a table must span chunks;
   - never mix different chapters.
2. Default chunk contract:
   - target up to 6000 source characters;
   - 600 characters of adjacent read-only context for continuity;
   - split on paragraph/list/table-row boundaries first;
   - an indivisible over-limit row/paragraph is retained intact and marked;
   - deterministic IDs/hashes and stable source ordering.
   The context is prompt context only and must not be duplicated in translated
   output.
3. Structure/TOC plans appear in the existing `结构与译文审核` reference
   workflow, not as permanent cards in the writing editor.
4. Existing extraction medical approval remains the human structure gate.
   Flash produces the document role/TOC/chapter plan once after approved
   extraction. Ambiguities are surfaced in the plan and may block translation;
   no second mandatory approval click is added for a clean plan.
5. Legacy span-keyed composite items are explicitly non-current under the new
   document-plan/chunk contract and are regenerated on the next batch. Do not
   silently project them as current or mutate old immutable records.

## Required domain and persistence contract

Add the minimum additive immutable records needed to prove:

- one `DocumentStructurePlan` per artifact, extraction revision and planner
  contract fingerprint;
- ordered plan chapters with document role, title/heading path, M11 anchor,
  ordered source span IDs, source locators, source hashes, ambiguity codes,
  planner model/prompt/input/output hashes;
- deterministic `TranslationChunk` records with chapter ID, order,
  source-span IDs, source/adjacent-context hashes, table-header prefix when
  present, chunk fingerprint, Hy-MT2 model/prompt and translated text/hash;
- `ChapterIntegrationResult` with ordered chunk IDs/hashes, final integrated
  Chinese, Flash model/prompt/input/output hashes, deterministic fidelity
  result and failure codes;
- immutable record tables, auditable current-state projection or deterministic
  latest selection, no-update/no-delete triggers, idempotency and retry.

Use additive fields and migration-safe defaults. Do not invalidate existing
SQLite files or rewrite immutable rows.

## Required service behavior

1. Flash planning runs exactly once for a current document plan, not once per
   source span or chunk. A retry reuses the immutable accepted plan.
2. Plan validation fails closed if:
   - document role or chapters are absent;
   - a source span is missing, duplicated across chapters without an explicit
     allowed shared-context marker, or reordered inconsistently;
   - chapter IDs/titles/order are empty or duplicated;
   - planner output references a different artifact/extraction/hash.
3. Build deterministic chunks from the plan and current source spans.
   Preserve source locators and OCR page lineage for every chunk.
4. Hy-MT2 runs once per pending chunk. Retrying a partially completed document
   reuses completed chunks with matching fingerprints and runs only failed or
   missing chunks.
5. Flash integration QC runs once per ordinary chapter over ordered chunk
   outputs plus source facts. If a chapter exceeds the provider context
   contract, use deterministic ordered integration windows and a final chapter
   envelope check; expose that lineage honestly.
6. Deterministic numeric/unit/comparator/range/negation/time-window/
   abbreviation fidelity runs on the final integrated chapter candidate.
7. Persist a real `WritingReferenceTranslationRevision` for each integrated
   chapter candidate. It may retain a primary `span_id` for backward foreign-key
   compatibility but must carry all source span/chunk lineage additively.
8. Medical review, revision, admission and chapter mapping operate on the
   integrated chapter candidate. Do not create one separately approvable
   translation per arbitrary source span under the new contract.
9. One authoritative product pipeline/service instance remains in `main.py`.
   No legacy Flash-only fallback.

## Real progress contract

Expose product state, not log text:

- document count/current document;
- chapter count/current chapter;
- chunk count/completed/running/failed;
- active stage (`toc_planning`, `translating_hy_mt2`,
  `integration_qc`, `fidelity_blocked`, `candidate_ready`);
- reuse count on retry;
- current human-readable chapter title;
- retryable vs terminal blocker.

Update `ReferenceTranslationBatchPanel` and pure progress logic so desktop users
can see the current document, chapter and chunk progress in the existing
reference workflow. Do not add developer IDs, hashes, model names or log panels
to the primary UI; keep them available in API/audit evidence.

## Tests and structural performance gates

Add focused deterministic tests for:

1. planner call count = 1 per artifact/extraction/planner contract;
2. no chapter mixing, no source omission/duplication, deterministic ordering;
3. chunk count < source span count for mergeable realistic spans;
4. oversized paragraph/list/table handling and repeated table headers;
5. Hy-MT2 call count = chunk count, not span count;
6. ordinary Flash integration call count = chapter count, not chunk count;
7. retry reuses completed plan/chunks and reruns only failed chunks;
8. final integrated chapter becomes one real translation revision with complete
   source span/chunk/OCR lineage;
9. deterministic fidelity can block a Flash-passed chapter;
10. old span-keyed contract is not counted as current after migration;
11. API progress and frontend display real document/chapter/chunk counts and
    terminal/busy state;
12. malformed/missing planner and integration output fail closed.

Run:

- all new focused tests;
- all tests matching `writing_reference|chapter_translation`;
- affected frontend pure logic and component tests;
- broader backend suite if shared contracts/models change.

Report exact counts. Do not substitute mocked assertions that merely search for
strings.

## Hard boundaries

- Do not touch stable runtime databases, real project rows, credentials or real
  source documents.
- Do not start the three-indication external E2E in this worker.
- Do not install paid/commercial dependencies.
- Do not replace GLM-OCR-bf16, Hy-MT2 or DeepSeek Flash/Pro.
- Do not add a second permanent writing-editor information panel.
- Do not claim browser, clinical/regulatory quality or release acceptance.

Write exactly one output file:
`runs/execution/mw_cross_indication_reference_release_gate_20260718/cms_w1_document_planning_chunking_round7.md`

List exact changed files, migrations, commands/results, remaining risks and a
compact action/observation/evaluation/decision trace. Source/tests are the
deliverable; Codex performs final acceptance.
