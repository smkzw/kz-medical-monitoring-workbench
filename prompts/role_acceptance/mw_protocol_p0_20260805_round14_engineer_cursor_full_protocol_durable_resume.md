# Protocol P0 — r14 engineer full Protocol E2E after durable-resume repair

## Purpose

Re-run the complete Protocol workflow in a fresh isolated runtime after the
r13 post-admission orchestration repair. This pass must prove that a visible
preparation-stage admission creates one durable continuation, returns a
truthful UI state, resumes only pending items, and can reach a substantive
Word protocol. A runner completion is not acceptance: inspect every stage and
diagnose the first broken contract.

## Hard boundaries

- Use only `/private/tmp/mw-p0-engineer-r14.GoQYbK`, API
  `http://127.0.0.1:8946`, and Vite `http://127.0.0.1:5227`. Do not touch
  stable r42/v36 data or r9–r13 runtimes/evidence. Do not edit source or
  fixtures.
- Create exactly one project through the visible UI: `QZ-PN04`, indication
  `帕金森病`, phase `II期`. Never create or advance anything via API,
  SQLite, browser console, hidden endpoint, or direct DOM dispatch.
- Use real visible/headful Playwright for all user actions. Read-only API or
  SQLite inspection is allowed only after a visible action for evidence.
- Verify and record the fixed model receipts: independent and translation
  support DeepSeek provider `deepseek-v4-flash`, thinking enabled, `max`;
  OCR official PaddleOCR `PaddleOCR-VL-1.6`; body translation oMLX
  `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`. Stop and diagnose if a receipt differs.
- Preserve any harness-created extra project and mark NOT_CLEAN; never delete
  records or re-run completed downloads/OCR/translation to make a pass look
  clean.

## Required visible workflow and repair proof

1. Verify API/Web build and client-contract gates and all four AI receipts.
   Create the one project and record project/journey IDs and revisions.
2. Let automatic prefill, ClinicalTrials.gov search, and DeepSeek triage run
   once. Record query terms, source counts, snapshot/run/chunk lineages,
   deterministic/AI chunks, reservations, and terminal statuses. If results
   are empty or implausible, inspect query ontology, HTTP/source health,
   pagination, and retention before accepting it. Record the China registry
   reachability/lineage truthfully; do not claim data that the source did not
   provide.
3. Review triage evidence in the UI, retain/confirm only with the legitimate
   visible control, and adopt at most one exact deterministic title with
   complete current-project-fact bindings. Keep unsupported design/PICOS,
   population, dose, endpoint, timing, visit, and sample-size proposals
   manual-only.
4. Use visible preparation/download controls. When the UI shows the first
   `准入下一阶段原文`, click it once and wait for the HTTP response and the
   natural terminal state. Prove read-only that exactly one durable
   `research_pipeline` continuation job was created/reused, its payload is
   bound to the same preparation batch and idempotency key, and the parent
   changes from `preparing` to either the next real stage or
   `awaiting_preparation_admission` with an enabled CTA. A completed durable
   job plus `preparing` and no CTA is P0. Repeat visible stage admission only
   while the UI exposes it; never call `/resume` yourself or shepherd via a
   direct script.
5. Continue through real visible OCR, translation, translation-support/QC,
   corpus admission, deep evidence/PICOS/design analysis, and full Protocol
   writing. Use the configured PaddleOCR-VL-1.6, Hy-MT2, and DeepSeek roles;
   inspect representative source/page/chunk lineage, clinical terminology,
   units, negation, tables, and failed/uncertain statuses. Do not fabricate
   evidence or accept blanket `不适用`.
6. Generate the complete regulatory Chinese Protocol with substantive content
   in every applicable section, not headings/placeholders/`待确定`/logs/AI
   traces. Read it end-to-end for factual consistency and provenance.
7. Export Word through the visible UI and read the whole DOCX/OOXML and useful
   rendered pages. Verify populated paragraphs, heading/style hierarchy,
   numbering, TOC, references and hyperlinks/bookmarks, tables,
   headers/footers, page breaks, and absence of placeholders, logs, or broken
   cross-references. If any downstream stage is blocked, stop honestly at the
   first root cause and do not manufacture a document.
8. Reconcile read-only evidence: one project, one lineage per stage, no
   duplicate model calls/worker/restarts, no upstream retries, explainable
   state/version/source/idempotency/audit events, and P0–P4 classification.

## First-principles diagnosis

For every unexpected result separate connectivity, query/ontology, filtering,
source-document, OCR/translation, provenance, orchestration, rendering, and
harness causes. A clickable flow or HTTP 200 is not evidence of a healthy
clinical workflow. Preserve uncertainty and negative evidence.

## Files to read only

Read these files only:

- `AGENTS.md`
- `context/mw_protocol_p0_max_clean_rounds_20260805_context.md`
- `runs/mw_protocol_p0_max_clean_rounds_20260805.md`
- `reviews/mw_protocol_p0_max_clean_rounds_20260805.md`
- `metrics/mw_protocol_p0_max_clean_rounds_20260805.md`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/writing_reference_preparation_batch.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- `services/api/app/medical_writing_competitor_triage.py`
- `services/api/app/medical_writing_full_draft.py`
- `services/api/app/medical_writing_document_exporter.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.jsx`

Also follow the loaded global contract in
`/Users/smkzw/.codex/AGENTS.md` and all applicable system instructions; do not
edit that file.

## Evidence and handoff

Write exactly one output file:
`runs/role_acceptance/mw_protocol_p0_20260805_round14_engineer_cursor_full_protocol_durable_resume.md`.
Write screenshots, DOM probes, downloaded DOCX, rendered pages, and compact
JSON only under `/private/tmp/mw-p0-engineer-r14.GoQYbK/evidence/`. Include
build/role receipts, every visible action, stage/job/batch lineage, durable
resume proof, source diagnostics, first root cause for each deviation,
full-draft/Word review, idempotency/isolation, P0–P4 findings, clean status,
uncertainty, and the next safe action. Never claim full Protocol/Word
acceptance if any substantive stage or content is missing.
