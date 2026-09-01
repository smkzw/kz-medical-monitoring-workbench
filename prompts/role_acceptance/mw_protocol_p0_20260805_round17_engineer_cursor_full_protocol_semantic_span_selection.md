# Protocol P0 Round 17 — fresh engineer route with semantic research-span selection

You are continuing the same engineer session after Round 16, but this is a
new clean isolated runtime and a new visible project. Read the current
`/Users/smkzw/.codex/AGENTS.md`, workbench `AGENTS.md`, and the current P0
context/run/review/metrics records before acting. The filesystem is the source
of truth; do not claim recovery of a deleted conversation.

## Hard boundaries

- Fresh isolated runtime: `/private/tmp/mw-p0-engineer-r18.fWUe1r`.
- API: `http://127.0.0.1:8950`; Vite/headful browser:
  `http://127.0.0.1:5230`.
- Use real headful Playwright for every user action and button. Do not create,
  advance, approve, retry, or admit anything through API, SQLite, browser
  console, DOM dispatch, or hidden endpoints. Read-only API/SQLite inspection
  is allowed only after the corresponding visible action settles.
- Create exactly one new project: `QZ-AST04`, indication `哮喘`, `II期`,
  randomized double-blind placebo-controlled parallel-group. Do not create a
  second project. Preserve any accidental extra project and mark NOT_CLEAN;
  never delete it.
- Do not touch r42/v36, medical-monitoring files, r9–r16 clones, or any
  immutable rows. Do not reuse r16 evidence as runtime data.
- Fixed AI roles must be visible/read-only verified: independent and
  translation-support DeepSeek `deepseek-v4-flash`, thinking enabled, `max`;
  official PaddleOCR `PaddleOCR-VL-1.6`; body translation oMLX
  `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`.
- Do not edit product source or tests from this role. The current source
  contains bounded repairs for case-insensitive fallback-title dedupe,
  fail-closed substantive evidence/PICOS admission, longest-source ranking,
  and now semantic research-span ranking: explicit anchor headings first,
  references/TOC and generic cross-references down-ranked, oversized HTML
  tables avoided when a complete paragraph/criterion is available. Passing
  fidelity and medical gates remain authoritative.

## Required visible route

1. Verify API/Web build identity, clean project count, and all four AI receipts.
   Create the one project and record project/journey IDs and revisions.
2. Let initial AI-first prefill/search run once. Use the visible UI to inspect
   ClinicalTrials.gov query terms, result counts, public-document lineage, and
   any China registry reachability. If results are empty or implausible,
   investigate connectivity versus ontology/filter/pagination before moving on.
3. Review and confirm the triage through visible controls only. Retain only
   source-grounded direct competitors/indirect references and adopt no
   unsupported design, dose, population, endpoint, or PICOS fact.
4. Run visible document preparation and all exposed stage admissions. Prove
   durable continuation/idempotency and no duplicate worker/model calls.
5. In the translation preview/creation UI, inspect the selected capped spans
   by anchor. Confirm eligibility is a complete inclusion/exclusion criterion,
   objectives is an actual objective/endpoint/estimand passage, safety is a
   safety/adverse-event passage, and schedule is a usable visit/assessment
   passage. Reject headings, references, TOC pages, generic cross-references,
   punctuation, `CCI`, `无`, `包含：`, or fragments. Record source/translation
   lengths and exact exclusion or fidelity reasons.
6. Complete only source-grounded medical admission. The medical gate must
   remain closed for thin/placeholder briefs; exercise the visible UI and
   record the precise message if it blocks. Once all four critical anchors
   have substantive regulatory Chinese evidence, complete PICOS conflict
   disposition from shown evidence. Never invent missing facts.
7. Continue the visible independent-AI design/PICOS analysis, full Protocol
   writing, and Word export only after the deterministic corpus gate is ready.
   Every applicable section must contain substantive regulatory Chinese text;
   headings-only, `待确定/待决策`, `不适用` everywhere, logs/JSON/AI traces, or
   empty tables are failures. Read the complete draft end-to-end for factual
   consistency, provenance, Chinese regulatory semantics, and unresolved
   placeholders.
8. Open the actual `.docx` and inspect populated paragraphs, styles, numbering,
   TOC, references/hyperlinks/bookmarks, tables, headers/footers, page breaks,
   and absence of skeleton or log artifacts. If any gate remains blocked, stop
   at the first root cause and report it honestly rather than manufacturing a
   Word file.

## First-principles diagnosis and evidence

For every unexpected result distinguish connectivity, search ontology,
filtering, source-document quality, OCR, translation, span selection,
medical-admission contract, PICOS, orchestration, rendering, and harness
causes. A clickable flow or HTTP 200 is not health evidence. Preserve all
screenshots, DOM/network notes, read-only JSON, downloaded files, and DOCX
renders under `/private/tmp/mw-p0-engineer-r18.fWUe1r/evidence/` without
deleting prior files.

## Read these files only

Read these files only:

- `AGENTS.md`
- `context/mw_protocol_p0_max_clean_rounds_20260805_context.md`
- `runs/mw_protocol_p0_max_clean_rounds_20260805.md`
- `reviews/mw_protocol_p0_max_clean_rounds_20260805.md`
- `metrics/mw_protocol_p0_max_clean_rounds_20260805.md`
- `services/api/app/medical_writing_corpus_readiness.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_full_draft.py`
- `services/api/app/medical_writing_document_exporter.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.jsx`

Write exactly one output file:
`runs/role_acceptance/mw_protocol_p0_20260805_round17_engineer_cursor_full_protocol_semantic_span_selection.md`.
The report must include sources read, every visible action, project/journey/
batch IDs, build and AI receipts, search/triage/source counts, selected span
quality and exclusion proof, medical/PICOS gate status, complete draft/Word
evidence or the first honest blocker, no-rerun/idempotency proof, P0–P4
findings, uncertainty, and exact next safe action. Do not claim a clean round
without a substantive Word document actually opened and verified.
