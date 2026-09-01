# Medical Writing Document Pipeline Round 8 Remediation

You are the Grok Build / grok-4.5 execution manager for one bounded production-code remediation. Read `/Users/smkzw/.codex/AGENTS.md` and the closest project `AGENTS.md` before acting. Codex remains the final acceptance authority.

## Objective

Repair and prove the document-level protocol translation pipeline so it implements this real product contract:

`one immutable document plan -> deterministic chapter chunks -> Hy-MT2 once per pending chunk -> Flash integration/QC once per ordinary chapter or explicit ordered windows -> deterministic final fidelity -> exactly one immutable WritingReferenceTranslationRevision per integrated chapter -> medical review/admission/chapter mapping`

Do not start any ClinicalTrials.gov external E2E in this pass.

## Current source of truth

Read these files only as the initial context. Additional adjacent reads are
allowed only when needed to preserve the actual pipeline contract:

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- project `AGENTS.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TASK_RECORD.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/ACCEPTANCE_CONTRACT.md`
- `runs/execution/mw_cross_indication_reference_release_gate_20260718/grok_document_planning_chunking_manager.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/writing_reference.py`
- `services/api/app/main.py`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- `frontend/src/features/writing-reference/progressJourneyLogic.mjs`
- `tests/_composite_pipeline_fixture.py`
- all related `writing_reference|chapter_translation` tests

## Observed defects to reproduce before editing

Codex reran:

```bash
python3 -m pytest -q \
  tests/test_chapter_translation_pipeline.py \
  tests/test_writing_reference_translation_batch.py \
  tests/test_writing_reference_translation_service.py \
  tests/test_writing_reference_extraction.py \
  tests/test_mw_round3_backend_remediation.py \
  tests/test_mw_round5_backend_contract.py
```

Current result: 10 failures. The deterministic planner fixture does not return source-span assignments required by the new fail-closed plan validator, so many existing batch cases end in `failed_retryable`. Fix tests/fakes only when they model the real contract; do not weaken production validation.

Source audit also found:

1. `_process_with_composite_pipeline()` is still invoked per span item. The first item creates a chapter integration, but later items call `_link_item_to_chapter_revision()` and create a new span-keyed translation ID. The code comment saying spans share one revision is false. There must be exactly one translation revision per plan/chapter/contract, and every item in that chapter must reference that exact revision ID/revision.
2. New composite revisions persist `ai_run_id=""`. This is not acceptable provenance. Persist immutable plan/chunk/integration run records or a deterministic auditable composite run ledger that has real stage model, prompt, input/output hashes and is queryable by ID. Do not fabricate a provider run.
3. `adjacent_context` is prepended to `source_text` and sent as one body to Hy-MT2. The translator cannot distinguish read-only context from text to translate, so context may be duplicated in output. Use an explicit prompt envelope or a translator request contract separating `read_only_context` from `source_text`; output must correspond only to source text.
4. `integration_windowed=chunk_count > 1` is only a label. Implement deterministic ordered integration windows only when the chapter exceeds a declared provider input limit, persist each window's ordered chunk IDs/input/output hashes, then run a final chapter envelope check. A normal multi-chunk chapter must still have one ordinary integration call and `integration_windowed=False`.
5. `_resolve_chapter_for_span()` silently falls back to the first chapter. Remove that fallback and fail closed.
6. Progress lacks required document count/current document, chapter count/current chapter, running chunk count, and retryable-vs-terminal blocker. Persist observable product state, not log text. Do not show hashes, model names, internal IDs, or logs in the primary UI.
7. The new Round 7 code has no focused deterministic tests proving planner count, chunk count/calls, chapter revision uniqueness, retry reuse, context non-duplication, true integration windows, immutable lineage and fail-closed behavior.
8. The legacy method/docstring says a Flash-only fallback remains even though production now fails closed. Remove dead contradictory code if it is not invoked; otherwise make the boundary explicit and test that production cannot silently use it.

## Required design and implementation

### Identity and idempotency

- Document plan identity: artifact ID + extraction revision + document hash + planner contract fingerprint.
- Chunk identity/fingerprint must include plan/chapter/order/source-span IDs/source hash/read-only-context hash/table-header prefix/glossary/model/prompt contract.
- Chapter integration identity must include ordered chunk IDs/hashes + integration contract.
- Chapter translation ID must be deterministic from project + plan + chapter + translation contract, not batch item/span/attempt.
- Retry reuses completed immutable plan/chunks/integration/revision when every fingerprint matches. Failed or missing chunks alone rerun.
- Existing legacy span-keyed composite candidates lacking document plan/chunk/integration lineage are non-current under the new fingerprint and are regenerated without mutating old immutable records.

### Planning and chunking

- Flash planning runs once per current document plan.
- Fail closed for missing/duplicated/reordered spans, empty or duplicate chapters, wrong artifact/extraction/hash, or missing chapter membership.
- Keep <=6000 source characters by default and 600 adjacent read-only context characters. Split on paragraph/list/table-row boundaries. Repeat table headers when needed. Never mix chapters.
- An indivisible over-limit unit remains intact with an explicit persisted marker.

### Translation and integration

- Hy-MT2 sees source text and read-only continuity context as separately labelled fields. It must be instructed to translate only the source block.
- Hy-MT2 call count equals pending chunk count.
- Ordinary Flash integration call count equals chapter count, not chunk count.
- Define a deterministic integration input limit and window algorithm. Persist immutable window lineage additively. Do not claim windowing merely because a chapter has multiple chunks.
- Both Flash QC and deterministic numeric/unit/comparator/range/negation/time-window/abbreviation fidelity must pass for `candidate_ready`.
- Malformed planner, Hy-MT2 or integration output fails closed.

### Progress

Expose and persist:

- document total and current document filename/title;
- chapter total/current index/current chapter title;
- chunk total/completed/running/failed/reused;
- active stage;
- retryable versus terminal blocker and a concise medical-user-facing message.

Update the existing `结构与译文审核` panel and pure progress logic only. Do not add a permanent editor card or developer log panel.

## Required tests

Add focused tests that prove behavior, not string presence:

1. planner call count = 1 for multiple spans/chapters in one artifact and for retry;
2. no span omission/duplication/reordering/chapter fallback;
3. mergeable realistic spans yield fewer chunks than spans;
4. oversized paragraph/list/table behavior and repeated table header;
5. explicit read-only context is not included in translated output;
6. Hy-MT2 call count = pending chunks; partial retry reruns only failed/missing chunks;
7. ordinary Flash integration call count = chapters and does not set windowed;
8. oversized chapter invokes deterministic windows plus one final envelope check and persists window lineage;
9. all span items in one chapter reference the same single translation ID/revision;
10. translation revision has complete plan/chunk/OCR/integration/composite-run lineage and no blank required run ID;
11. deterministic fidelity can block a Flash-passed result;
12. legacy span-keyed current-looking candidates are not reused;
13. API and frontend progress show real document/chapter/chunk counts and blocker state;
14. malformed/missing planner, translator and integration payloads fail closed;
15. immutable plan/chunk/window/integration/run rows reject UPDATE and DELETE.

Run the focused tests first, then:

```bash
python3 -m pytest -q \
  tests/test_chapter_translation_pipeline.py \
  tests/test_writing_reference_translation_batch.py \
  tests/test_writing_reference_translation_service.py \
  tests/test_writing_reference_extraction.py \
  tests/test_mw_round3_backend_remediation.py \
  tests/test_mw_round5_backend_contract.py
```

Then run all backend tests whose node IDs match `writing_reference|chapter_translation`, affected frontend pure/component tests, and broader contract/repository tests if models or schema changed. Report exact counts.

## Hard boundaries

- Do not touch stable runtime databases, credentials, real project rows, real protocol files, ports 5174/8911, or production AI.
- Do not weaken fail-closed checks to satisfy old tests.
- Do not install a paid/commercial dependency or replace GLM-OCR, Hy-MT2, DeepSeek Flash or DeepSeek Pro.
- Do not start external study search/download/translation.
- Do not claim visual, clinical, regulatory, DOCX or release acceptance.
- Keep edits limited to the document translation pipeline, its contracts/repository/progress UI, and directly related tests.

Write exactly one output file:

`runs/execution/mw_cross_indication_reference_release_gate_20260718/grok_document_pipeline_round8_remediation.md`

The report must list exact changed files, schema additions, commands/results, unresolved risks, and a compact action/observation/evaluation/decision trace. Source and tests are the deliverable; Codex will inspect and rerun them.
