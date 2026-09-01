# Protocol P0 — r11 same-session build-gate recovery

## Purpose

Continue the terminal r11 engineer pass after the isolated Vite/API build
contract gate blocked the authoring page. The API was not restarted. A frozen
test-only Vite snapshot is now serving the same r11 UI with its expected
backend build explicitly aligned to the already-running API receipt. Prove
the repaired deterministic identity policy in the existing project, and stop
before any upstream re-run or substantive drafting.

## Hard boundaries

- Use the existing r11 clone/runtime `/private/tmp/mw-p0-engineer-r11.GoQYbK`.
- API `http://127.0.0.1:8943` remains running and must not be restarted,
  reconfigured, or stopped. Vite is served from the test-only frozen snapshot
  `/private/tmp/mw-p0-engineer-r11.GoQYbK/vite-snapshot/frontend` at
  `http://127.0.0.1:5224`; do not edit the product source or the snapshot.
- Resume the existing Cursor session; do not create another session or a new
  project. The existing project is
  `proj_user_d0192cbe211f`, journey
  `mwjourney_37e2da88b6d05246109e`, code `MW-II-59116C98`, and uses
  QZ-CRSNP03 / 慢性鼻窦炎伴鼻息肉 / II期.
- Use real visible/headful Playwright for every user action. Read-only API or
  SQLite inspection is allowed only after the visible actions to verify the
  receipt and idempotency.
- Do not create a project by API or SQLite. Do not run or manually trigger a
  second search, triage, download, preparation, OCR, translation, corpus
  analysis, PICOS, full drafting, freeze, Word export, or medical-monitoring
  operation. The product may automatically resume its initial prefill/search
  after the writing page mounts; observe that automatic behavior once.
- Do not enter or adopt unsupported design, population, intervention, dose,
  endpoint, timing, visit, or sample-size facts. Do not use composite skip-all
  or free text to fabricate framing completion.

Read these files only:

- `AGENTS.md`
- `context/mw_protocol_p0_max_clean_rounds_20260805_context.md`
- `runs/mw_protocol_p0_max_clean_rounds_20260805.md`
- `reviews/mw_protocol_p0_max_clean_rounds_20260805.md`
- `metrics/mw_protocol_p0_max_clean_rounds_20260805.md`
- `runs/role_acceptance/mw_protocol_p0_20260805_round11_engineer_cursor_agent_project_fact_live.md`
- `services/api/app/runtime_readiness.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.jsx`

## Bounded visible sequence

1. Open the existing r11 project through the visible UI at `http://127.0.0.1:5224`
   and navigate to its writing journey; do not create anything. Confirm the
   build gate now reports matching frontend/API receipts. Record the role
   receipt (DeepSeek V4 Flash thinking/max for independent and translation
   support, PaddleOCR-VL-1.6, and oMLX Hy-MT2).
2. Let the automatic creation-time prefill and registry-search continuation
   settle to a terminal visible state. Do not fixed-interval poll, force retry,
   redispatch, or click a duplicate search. Record whether the existing
   project receives its first automatic package and whether a registry
   snapshot is attached.
3. Once the search snapshot is visibly attached and the authoring page is no
   longer in its initial search state, click visible `更新建议` exactly once.
   Wait naturally for that single request. Inspect the single-field
   `framing.document_title` candidates. The three exact deterministic title
   variants must be `supported` and `batch_allowed`, each bound to the same
   immutable `current_project_fact` entries for product, indication, and
   phase, with one catalog ID/SHA and an enabled unedited `采用` control.
4. Click `采用` for exactly one such title candidate, once. Do not use
   `修改后采用` unless the unedited control is genuinely unavailable; if so,
   record the exact UI/backend reason and stop without typing a replacement.
   Capture the HTTP response, package/journey revision, evidence-verification
   receipt, and audit event.
5. Verify the deterministic `framing.design_pattern` candidate is
   `pending_decision`/`manual_only`, has no claim bindings, and has no enabled
   single-adopt control. A missing competitor/corpus candidate is expected if
   no corpus analysis has run; if one appears, it must remain manual-only and
   must not be adopted.
6. Stop. Read back only the journey, candidate, reservation, and audit/event
   records needed to prove at most one manual prefill update and one title
   adoption, no duplicate model call/record, no stale cross-project identity,
   and no changes to r9/r10. Do not advance to PICOS or full draft.

## First-principles diagnosis

For every unexpected result, locate the first broken contract and classify it
as harness/runtime, frontend, backend policy, provider, or evidence-source
limitation. Explicitly distinguish the prior build-gate race from any real
prefill/adoption failure, automatic ordering from duplicate user action,
current-fact bindings from phase heuristics, and truthful `corpus_not_ready`
from an AI/provider failure. The safe predicate remains narrow: only exact
title templates with complete, gap-free current-fact bindings may be
`batch_allowed`; design, competitor, corpus, mixed, partial, pending, and
composite candidates must stay fail-closed.

## Evidence and handoff

Write exactly one output file:
`runs/role_acceptance/mw_protocol_p0_20260805_round11_engineer_cursor_agent_build_align_followup.md`.
Write screenshots/DOM probes and compact JSON only under
`/private/tmp/mw-p0-engineer-r11.GoQYbK/evidence/`. Return a compact handoff
with visible actions, IDs/builds, role receipt, automatic/manual prefill
lineages, title bindings and adoption receipt, design/competitor fail-closed
state, unchanged prior clones, P0–P4 findings, uncertainty, and the next
recommended action. Never claim clean substantive Protocol or Word acceptance
from this focused pass.
