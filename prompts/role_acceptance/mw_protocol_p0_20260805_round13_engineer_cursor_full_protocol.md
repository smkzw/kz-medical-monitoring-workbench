# Protocol P0 — r13 engineer full visible Protocol E2E

## Purpose

Perform the first fresh, engineer-perspective, end-to-end Protocol workflow
after the deterministic evidence-binding and revision-only stale-triage
repairs. The acceptance target is a real, substantive, Word-exportable
research protocol, not a page of headings. Treat every unexpected result as a
diagnostic signal: identify the first broken contract and its root cause before
deciding whether the workflow can continue.

## Hard boundaries and isolation

- Use only the fresh r13 runtime `/private/tmp/mw-p0-engineer-r13.GoQYbK`:
  API `http://127.0.0.1:8945`, Vite `http://127.0.0.1:5226`. Do not restart,
  reconfigure, or write to another runtime. Do not touch stable r42/v36 data
  or the r9, r10, r11, or r12 evidence/runtimes.
- Start exactly one new project through the visible UI: `QZ-AD03`, indication
  `特应性皮炎`, phase `III期`. Use the UI as a real senior engineer would;
  never create, mutate, click, or advance anything through an API, SQLite, a
  browser console, direct DOM dispatch, or a hidden endpoint.
- All user actions must be real visible/headful Playwright interactions: one
  button, menu, field, confirmation, or download control at a time. Read-only
  API/SQLite inspection is permitted only after the corresponding visible
  action, for evidence and root-cause diagnosis. Do not edit product source,
  test fixtures, or runtime configuration.
- The fixed independent-AI configuration must be observed and recorded, not
  silently substituted: LLM and OCR/translation-support = DeepSeek provider
  `deepseek-v4-flash` with thinking enabled and `max`; OCR = official
  PaddleOCR `PaddleOCR-VL-1.6`; translation = oMLX
  `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`. If the UI receipt differs, stop at the
  first discrepancy, capture it, and diagnose the configuration path.
- Do not delete projects or evidence to make the runtime look clean. If a UI
  retry or a harness mistake creates an extra project, preserve it, mark the
  run NOT_CLEAN, and continue only with the first intended project if that is
  safe. Never retry an upstream completed item merely to improve a score.

## Required visible workflow

1. Verify the API/Vite build gate, the client-contract gate, and the four
   model-role receipts at 8945/5226. Create the single project above in the
   visible UI and record its project/journey IDs, revision, and initial state.
2. Let the product's normal automatic prefill/search/triage behavior run once.
   Observe the UI and capture ClinicalTrials.gov and Chinese registry result
   counts, snapshot/run/chunk IDs, deterministic versus DeepSeek chunks,
   provider reservations, and terminal statuses. If a source returns zero
   results, a network-looking error, a generic `no data` message, or an
   implausible candidate set, do not accept it: inspect the actual query,
   encoded indication/phase terms, HTTP/provider response, source health,
   pagination, and filtering/retention logic, then document the first causal
   boundary. A successful HTTP status or a visible skeleton is not evidence of
   valid clinical retrieval.
3. Review triage decisions and evidence in the UI. Use only legitimate visible
   actions to retain/confirm appropriate evidence. Do not blindly accept all,
   skip all, or insert unsupported facts. For title/framing suggestions,
   accept at most the one exact deterministic title whose product, indication,
   phase bindings are all current-project facts, supported, gap-free, and
   batch-allowed; keep design/PICOS/population/intervention/dose/endpoint/
   timing/visit/sample-size candidates manual-only when the evidence contract
   says they are not supported.
4. Continue through the visible preparation/download admission workflow. Use
   the actual supported public protocol sources; do not fabricate a source or
   bypass admission. Observe idempotency, reservation, progress, and failure
   reasons. Diagnose connection, search, authorization, or source-document
   failures at their first observable boundary. Do not re-run completed
   downloads or attempts.
5. Continue through OCR, translation, and translation-support/QC using the
   configured independent AIs. Exercise the real visible controls for upload,
   OCR, chunking, translation, merge/QC, and corpus admission. Inspect at
   least one representative page/chunk end-to-end for source alignment,
   page/chunk lineage, terminology, clinical abbreviations, units, negation,
   tables, and failed/uncertain OCR or translation. Distinguish a true model
   or data failure from a UI status/rendering problem. Do not substitute a
   local shortcut or run any frozen r42 item.
6. Build/admit the evidence corpus and run the visible deep analysis/PICOS and
   study-design recommendations. Check that each material assertion has
   provenance and that unsupported details stay explicitly unresolved rather
   than being invented. If the corpus is empty, partial, or all `不适用`, trace
   the chain from source acquisition through OCR/translation/chunk QC to
   admission and record the root cause.
7. Use the visible writing controls to generate the complete Protocol draft
   with DeepSeek. Read every generated section, not just the outline. Require
   substantive, internally consistent regulatory Chinese for all applicable
   sections (objectives/endpoints, design, population, eligibility,
   treatment/dosing, procedures/visits, safety, statistics, ethics, data
   handling, quality, references and appendices as applicable). Headings alone,
   placeholders, repeated boilerplate, blanket `不适用`, `待确定`/`待决策`,
   analysis logs, provider traces, or AI self-references are failures. Follow
   citations and cross-references back to evidence; do not silently fill a
   missing material fact.
8. Export the final Word document through the visible UI. Save the downloaded
   artifact under the runtime evidence directory only. Read the whole DOCX
   (OOXML/text plus rendered pages where useful) and verify: non-empty
   paragraphs in every required section, consistent terminology and facts,
   styles/heading hierarchy, page breaks and numbering, a usable TOC, reference
   numbering and in-document hyperlinks/bookmarks, tables, headers/footers,
   no placeholder or log/AI residue, and no broken or missing cross-references.
   If export or rendering is blocked, diagnose the first failing contract and
   stop honestly; do not manufacture a passing document.
9. After visible completion, perform read-only evidence reconciliation: one
   project only (or explicitly NOT_CLEAN), one lineage per stage, no duplicate
   provider call/worker/restart record, no unexpected retries, every state,
   version, source, idempotency key, and audit event explainable. Compare
   observable results with the acceptance criteria and assign P0–P4 severity.

## First-principles review lens

For every deviation, ask what a real medical monitor would expect at that
boundary, what contract would have to be true for the observed result, and
which earliest state transition or provider response violated it. Separate
connectivity, query/ontology, filtering, model, provenance, orchestration,
rendering, and harness errors. A flow that merely has clickable buttons is not
accepted. Preserve negative findings and uncertainty; do not turn a partial
run into a success claim.

## Files to read before acting

Read these files only:

- `AGENTS.md`
- `context/mw_protocol_p0_max_clean_rounds_20260805_context.md`
- `runs/mw_protocol_p0_max_clean_rounds_20260805.md`
- `reviews/mw_protocol_p0_max_clean_rounds_20260805.md`
- `metrics/mw_protocol_p0_max_clean_rounds_20260805.md`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- `services/api/app/medical_writing_competitor_triage.py`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/medical_writing_full_draft.py`
- `services/api/app/medical_writing_document_exporter.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.jsx`

These are the source-of-truth materials; read directly referenced files only
when needed to inspect a demonstrated failure.
Also follow the already-loaded global contract in
`/Users/smkzw/.codex/AGENTS.md` and all applicable system instructions; that
path is not a workspace output or an artifact to edit.

## Evidence and handoff

Write exactly one output file:
`runs/role_acceptance/mw_protocol_p0_20260805_round13_engineer_cursor_full_protocol.md`.
Write screenshots, DOM probes, downloaded DOCX, rendered pages, and compact
JSON only under `/private/tmp/mw-p0-engineer-r13.GoQYbK/evidence/`. The report
must contain: build/role receipts; project and journey identity; every visible
action and terminal state; search/source diagnostics; triage and provenance;
download/prep/OCR/translation/corpus/PICOS/full-draft/Word evidence; the first
root cause for every unexpected result; idempotency/isolation/restart checks;
P0–P4 findings; clean/NOT_CLEAN status; uncertainty; and the next safe action.
Never claim full Protocol or Word acceptance when the document is incomplete.
