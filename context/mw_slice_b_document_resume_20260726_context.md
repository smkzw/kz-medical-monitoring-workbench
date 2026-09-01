# Task Context: mw_slice_b_document_resume_20260726

Updated: 2026-07-26
Mode: EXECUTION
Risk: critical
Route: Pi / `alibaba-token-plan-cn/qwen3.8-max-preview`, highest supported
reasoning; no model cycling or prewalk.

## Objective

Use the real medical-writing browser product to complete one isolated,
source-grounded document preparation and user-resume path. Prove that the
medical manager can review document-content findings, enter a durable waiting
state, refresh or reopen the project, resume through the visible UI, and
continue without repeating completed search, triage, download or extraction.
Exercise the translation-scope waiting state if the current product workflow
can reach it. Repair only defects reproduced in this path.

## Source Of Truth

- `records/handoffs/codex_retake_20260726/NEXT_LAUNCH_EXECUTION_PLAN_20260726.md`
- `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`
- `records/handoffs/codex_retake_20260726/evidence/slice_a_hermes/`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/main.py`, only the medical-writing journey, preparation,
  validation and resume routes
- `services/api/app/writing_reference_preparation_batch.py`
- `services/api/app/writing_reference.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/AuthoringCompetitorDrawer.jsx`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- directly related tests and styles reached from those files
- live frontend `http://127.0.0.1:5174`
- live API `http://127.0.0.1:8911`

## Scope

In scope:

- create a new isolated project from the real page with minimal user input;
- use the product's independently configured AI, never the executor model, for
  product search, triage, content interpretation or writing;
- select a small retained set with real public Protocol/SAP sources;
- complete real preparation, content validation, waiting-state and resume
  operations;
- refresh, close/reopen and repeat-click to test persistence, idempotency and
  duplicate-work prevention;
- test a content-role or indication warning and the current user's explicit
  override path without treating override as the normal success route;
- repair a reproduced functional, state or browser defect and add focused
  regression checks;
- preserve source URLs, hashes, project/pipeline/batch/item IDs, before/after
  counters and screenshots.

Out of scope:

- broad code, security or dependency audit;
- PNH basket confirmation or changes to the accepted triage rules;
- replacing product AI output with executor output;
- OCR/translation quality or corpus analysis beyond reaching and resuming the
  declared waiting states;
- global visual redesign, DOCX export or unrelated refactoring;
- deleting prior user data.

## Writable Paths

- directly implicated portions of:
  - `services/api/app/medical_writing_research_pipeline.py`
  - `services/api/app/main.py`
  - `services/api/app/writing_reference_preparation_batch.py`
  - `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
  - `frontend/src/features/medical-writing/AuthoringCompetitorDrawer.jsx`
  - `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
  - directly related CSS modules reached from those components
  - focused `tests/test_medical_writing_*`,
    `tests/test_writing_reference_*`, and frontend tests
- task evidence under:
  `runs/execution/mw_slice_b_document_resume_20260726/`

Do not change files outside this list. Do not modify accepted PNH triage or
corpus-analysis code. Preserve unrelated changes.

## Acceptance Checks

1. The page is tested at the live desktop runtime, not a source-only or
   mocked browser surface.
2. The isolated project reaches `awaiting_document_validation` or equivalent
   durable content-review state with real source documents.
3. Refresh and reopen preserve the project, batch and already completed stage
   identifiers.
4. A visible user action resumes the same pipeline; repeated clicks or retry
   use idempotency and do not redownload or re-extract completed documents.
5. If `awaiting_translation_scope` is reachable, the same persistence and
   resume checks pass there; otherwise report the exact upstream blocker.
6. A content mismatch remains a warning with source facts and an explicit
   user override option; normal matching documents do not require a redundant
   second medical approval.
7. Evidence includes browser traces/screenshots, HTTP status and payload
   locators, before/after artifact counts/hashes, and independent-AI route
   identity.
8. Any changed source has focused tests plus browser retest.

## Completion Marker

Write:
`runs/execution/mw_slice_b_document_resume_20260726/DONE.json`

It must state `pass`, `partial`, or `blocked`, changed files, checks, exact
blockers, evidence locators, independent-AI provider/model actually observed,
and the resumable session identifier. A partial result must not claim launch
readiness.

## Loop Log

- The initial guard visual route failed closed before dispatch because it
  generated the obsolete route
  `hermes/mixed/conference:visual-no-chair-pi-k3`.
- A second critical `code_open_audit` initialization selected Codex direct and
  was not dispatched. No source or runtime artifact was changed by either
  initialization.
- This execution uses the current active Pi browser route directly without
  changing the global guard.
