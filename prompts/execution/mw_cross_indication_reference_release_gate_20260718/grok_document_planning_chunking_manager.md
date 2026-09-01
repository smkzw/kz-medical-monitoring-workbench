# Grok Execution-Manager Review: Document Planning And Chapter Chunking

Act as the execution manager for a production medical-writing backend
architecture correction. Inspect current source and produce a precise,
implementable remediation plan. Do not edit production code in this pass.

Before acting, reread `/Users/smkzw/.hermes/SOUL.md`,
`/Users/smkzw/.codex/AGENTS.md`, project `AGENTS.md`, the current task record
and acceptance contract. Use first principles and bounded external research of
current authoritative/open-source approaches. Treat model outputs and prior
notes as evidence, not authority.

## Read these files only as the initial context

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TASK_RECORD.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/ACCEPTANCE_CONTRACT.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/CROSS_INDICATION_E2E_MATRIX.md`
- `services/api/app/writing_reference.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/main.py`
- `packages/contracts/workbench_contracts/models.py`
- `frontend/src/features/writing-reference/WritingReferenceProgressJourney.jsx`
- `frontend/src/features/writing-reference/progressJourneyLogic.mjs`
- relevant tests discovered under `tests/`

## Observed production problem

The current batch creates one translation item per extracted source span.
`_process_with_composite_pipeline()` calls
`ChapterTranslationPipeline.translate_chapter()` for each item, and that method
calls Flash planning every time. The practical chain is therefore:

`span -> Flash plan -> Hy-MT2 -> Flash QC`, repeated for every span.

This violates the approved workflow:

`document -> one persisted role/TOC/chapter plan -> medical structure review ->
ordered chapter chunks -> Hy-MT2 per chunk -> chapter integration/QC -> medical
review/admission`.

For 119-200 page Protocol/SAP files, per-span planning will cause duplicated
provider calls, fragmented context, poor chapter joins, misleading progress and
unacceptable runtime/cost.

## Required manager output

Produce a concrete implementation plan covering:

1. Domain objects and persistence:
   - immutable artifact/extraction revision;
   - one structure plan per artifact/extraction/planner contract;
   - document role, ordered TOC, chapter boundaries, source span IDs/pages;
   - medical structure-review revision and returned/approved states;
   - deterministic ordered chunk records with hashes and lineage;
   - chapter integration result and admission lineage.
2. Idempotency, revision, retry and restart behavior. A failed chunk retry must
   not rerun completed chunks or duplicate translations.
3. Chunking algorithm:
   - use current audited spans and approved chapter plan;
   - preserve paragraph/list/table boundaries;
   - keep heading path and source locators;
   - token/character cap appropriate for Hy-MT2 output budget;
   - deterministic overlap only where needed for sentence/section continuity;
   - repeated table headers for split tables;
   - no cross-chapter or cross-project mixing.
4. AI contracts:
   - Flash plans once per immutable document revision;
   - Hy-MT2 remains the body translator;
   - actual rendered glossary terms and medical-review instructions;
   - Flash integrates ordered chunks with adjacent context and returns a complete
     final Chinese chapter;
   - deterministic numbers/comparators/units/negation/timing checks after final
     integration.
5. Progress API/UI:
   - document, chapter and chunk counters;
   - current file/chapter/chunk;
   - persisted failure and retry-only-failed;
   - honest terminal/blocked states and `aria-busy`.
6. Backward compatibility and migration of current span-level rows. Prefer a
   bounded compatibility reader or explicit invalidation over silent reuse.
7. Exact source files/classes/functions to change, sequence of edits and
   acceptance tests.
8. Performance gates for the three real protocols:
   - AD NCT05923099, 200 pages;
   - PNH NCT04654468, 119 pages;
   - obesity NCT04707313, 135 pages.
   Define measurable limits for planner calls, chunk count, active model calls,
   restart reuse and lineage completeness. Do not invent throughput until
   measured.
9. Compare the smallest custom solution on current spans with at least one
   mature permissively licensed open-source option such as Docling's
   hierarchical/hybrid chunking. Check current license and integration costs.
   Recommend adoption only if evidence supports it; the required GLM OCR path
   and dual-channel lineage cannot be replaced.
10. Identify any decisions that truly require user judgment. Routine schema and
    implementation details should be resolved by the manager.

## Hard boundaries

- Read-only planning pass: do not edit production, tests, frontend, runtime,
  credentials or clinical files.
- Do not propose Flash as the body translator.
- Do not replace GLM-OCR-bf16/Hy-MT2/DeepSeek Flash.
- Do not introduce paid or proprietary runtime dependencies.
- Do not claim release acceptance.

Write exactly one output file:
`runs/execution/mw_cross_indication_reference_release_gate_20260718/grok_document_planning_chunking_manager.md`

Include sources read, external sources and licenses checked, recommended design,
rejected alternatives, file-by-file work breakdown, tests, risks, uncertainties
and a compact loop trace for Codex.
