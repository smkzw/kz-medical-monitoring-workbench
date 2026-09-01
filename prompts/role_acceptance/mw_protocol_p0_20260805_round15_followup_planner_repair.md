# Protocol P0 Round 15 same-session continuation — failed document-plan repair

You are the same engineer role that completed Round 15. This is an approved,
bounded continuation at an actionable step boundary, not a new project and not
a new broad test round. Continue the existing isolated runtime and project
only after reading `/Users/smkzw/.codex/AGENTS.md`, the current workbench
`AGENTS.md`, and the current P0 context/run/review/metrics records. The
filesystem is the source of truth; do not claim restoration of a deleted
conversation.

## Runtime and immutable boundary

- Existing isolated runtime: `/private/tmp/mw-p0-engineer-r15.FWUf2T`.
- API is expected at `http://127.0.0.1:8947`; Vite/headful browser at
  `http://127.0.0.1:5228`.
- Continue the one existing project `proj_user_2a9462823af5` (`MW-II-84674160`,
  QZ-SLE05, systemic lupus erythematosus, II期) and its existing journey and
  batches. Do not create another project.
- Do not rerun any already successful search, triage, candidate lock,
  download, preparation, OCR, Hy-MT2 translation, or integration. Do not
  touch the 18 `candidate_ready`/one excluded translation items. Only the one
  visible failed item `wref_translation_item_907ea10c473d85fa2cdd8591`
  (`NCT02349061`, `Prot_000.pdf`, `document_plan_failed`) may be retried.
- No API/HTTP/SQLite action may stand in for a user action. All user actions
  and all buttons must be performed through a real headful Playwright browser.
  Read-only evidence queries are allowed after a UI action settles.
- Do not edit product source, test files, runtime databases, or frontend
  sources from this role. The product-side repair is already present in the
  workbench source: the deterministic anchor-grouped planner fallback now
  canonicalizes heading titles case-insensitively before appending a suffix.

## Hard boundaries

- Do not create a second project or mutate any completed item. No direct API,
  SQLite, browser-console, DOM-dispatch, or hidden-endpoint user action.
- Do not edit source or tests from this role. Do not retry anything except the
  one named failed translation item, and do not claim acceptance without a
  substantive Word document opened and read.

## Files to read only

Read these files only:

- `AGENTS.md`
- `context/mw_protocol_p0_max_clean_rounds_20260805_context.md`
- `runs/mw_protocol_p0_max_clean_rounds_20260805.md`
- `reviews/mw_protocol_p0_max_clean_rounds_20260805.md`
- `metrics/mw_protocol_p0_max_clean_rounds_20260805.md`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/medical_writing_full_draft.py`
- `services/api/app/medical_writing_document_exporter.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.jsx`

## Exact continuation objective

1. Reopen the current project and inspect the actual visible state. Find the
   failed-document retry action and retry only that single failed document.
   Record the clicked label, request identity/idempotency key if visible,
   worker status, and final item counts. If the CTA retries more than the one
   failed item, stop and diagnose rather than accepting it.
2. Verify the repaired planner path from real UI behavior: the document must
   no longer fail with `chapter_176_duplicate_title`/
   `planner_duplicate_chapter_identity`; the persisted plan must have unique
   normalized titles and complete ordered source-span coverage. Do not accept
   a superficial success with no plan, empty text, or a hidden new provider
   failure. Retrying this one failed document must not issue duplicate calls
   for completed items.
3. Continue from the visible corpus/PICOS admission gate. Use the AI-first
   recommendations and evidence actually shown by the product. Admit or
   reject only when the source-grounded UI gives enough evidence; never invent
   product, dose, randomization, comparator, endpoints, or population facts.
   If the UI says a medical admission or PICOS conflict is unresolved, inspect
   the evidence and root cause instead of clicking through blindly.
4. Continue all remaining visible Protocol stages to a substantive, complete
   Word export. A framework with headings, placeholders, “待确定/待决策”,
   “不适用” everywhere, logs, JSON, AI traces, or blank sections is failure.
   Read the complete draft from start to finish, check internal consistency,
   Chinese regulatory wording, source traceability, TOC/page/reference links,
   and open the real exported `.docx` to verify it is not empty or a skeleton.
5. If any unexpected result occurs (zero content, missing evidence, stuck
   stage, API/worker mismatch, retry scope drift, or failed Word output), apply
   first-principles diagnosis: identify the exact UI action and backend state,
   distinguish connectivity from query/contract/data causes, capture evidence,
   and stop at the smallest safe boundary. Do not hide or work around a defect.

## Evidence and handoff

Keep all new screenshots, downloaded artifacts, read-only JSON, and diagnostic
notes under `/private/tmp/mw-p0-engineer-r15.FWUf2T/evidence/` (do not delete
prior evidence).

Write exactly one output file:
`runs/role_acceptance/mw_protocol_p0_20260805_round15_followup_planner_repair.md`.
The report must state: sources read; actual UI actions; project/journey/batch
IDs; before/after item counts; planner failure and repair evidence; AI route
receipts (DeepSeek V4 Flash max for independent/translation-support, PaddleOCR
VL-1.6, Hy-MT2); no-rerun/idempotency proof; corpus/PICOS decisions; full
draft/Word result; P0–P4 findings with evidence locators; failed paths,
uncertainty, and exact next action. Do not claim clean acceptance unless a
complete substantive Word document was actually opened and verified.
