# Protocol P0 — r12 live stale-revision repair probe

## Purpose

Prove the minimal stale-triage repair in a fresh isolated runtime. A title
adoption derived only from immutable product/indication/phase facts may advance
the authoring CAS revision, but it must not invalidate the same search/triage
run. Real relevance-driving fact changes must remain fail-closed. This is a
focused engineer contract pass, not full Protocol/Word acceptance.

## Hard boundaries

- Use only the fresh r12 runtime `/private/tmp/mw-p0-engineer-r12.GoQYbK`.
  API `http://127.0.0.1:8944` and Vite `http://127.0.0.1:5225` are already
  running repaired source; do not restart or reconfigure either service.
- The r12 project store is empty. Create exactly one project through the
  visible UI: `QZ-UC04` / `溃疡性结肠炎` / `I期`. Never create it by API or
  SQLite. Do not touch r9, r10, or r11.
- Use real visible/headful Playwright for all user actions. Read-only API or
  SQLite inspection is allowed only after visible actions to verify receipts,
  triage identity, stale status, and idempotency.
- The product may automatically start initial prefill, public search, and
  deterministic/AI triage after visible creation. Observe that automatic
  behavior once. Do not click search, triage, retry, download, preparation,
  OCR, translation, corpus, PICOS, full drafting, freeze, or Word controls.
  Do not trigger a second prefill update. If the automatic pipeline invokes a
  provider, let its one natural run finish or record the exact terminal
  boundary; never retry or redispatch it.
- Do not enter or adopt any unsupported design, population, intervention,
  dose, endpoint, timing, visit, or sample-size fact. Adopt only one exact
  deterministic title candidate whose three bindings are all
  `current_project_fact`, supported, and gap-free.

Read these files only:

- `AGENTS.md`
- `context/mw_protocol_p0_max_clean_rounds_20260805_context.md`
- `runs/mw_protocol_p0_max_clean_rounds_20260805.md`
- `reviews/mw_protocol_p0_max_clean_rounds_20260805.md`
- `metrics/mw_protocol_p0_max_clean_rounds_20260805.md`
- `services/api/app/medical_writing_competitor_triage.py`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.jsx`

## Bounded visible sequence

1. Verify the live build gate and role receipt at 8944/5225. Create the one
   project above in the visible UI. Record project/journey IDs and the four
   configured roles: DeepSeek V4 Flash thinking/max for independent and
   translation support, PaddleOCR-VL-1.6, and oMLX Hy-MT2.
2. Let automatic prefill, search snapshot attachment, and its one natural
   triage run settle. Record the snapshot/run IDs, deterministic versus AI
   chunks, terminal run status, and any provider reservation. Do not manually
   retry a stale/failed run.
3. Once the snapshot is visibly attached and authoring is ready, click
   visible `更新建议` exactly once. Inspect the exact deterministic
   `framing.document_title` candidates. Click `采用推荐` for exactly one
   supported, batch-allowed title once; do not use free text or composite
   skip-all.
4. After that single adoption, read the journey and triage status once after
   the natural UI transition. The unchanged snapshot/run must not be marked
   `stale` merely because the journey revision advanced. If the run is still
   genuinely running, record that and do not poll on a fixed interval; if it
   is terminal, capture `status`, `stale_reason`, run/journey revisions,
   material-facts hashes, and event counts. A true relevance fact change must
   still be demonstrated as stale only by offline evidence, not by editing
   this project.
5. Stop. Prove at most one automatic prefill, one search attachment, one
   visible update, and one title adoption; no duplicate model call, no retry,
   no cross-project data, and no r9/r10/r11 mutation. No downstream stage.

## First-principles diagnosis

If an unexpected `stale` appears, compare the run's captured journey revision
and material-facts hash with the post-adoption values and identify whether a
relevance-driving field actually changed. Distinguish a real provider/triage
failure from the prior revision-hash bug; do not accept HTTP 200, a skeleton,
or a pending status as proof of a healthy triage run.

## Evidence and handoff

Write exactly one output file:
`runs/role_acceptance/mw_protocol_p0_20260805_round12_engineer_cursor_stale_revision_live.md`.
Write screenshots/DOM probes and compact JSON only under
`/private/tmp/mw-p0-engineer-r12.GoQYbK/evidence/`. Return a compact handoff
with builds, role receipt, IDs, visible actions, prefill/search/triage lineages,
title bindings/adoption audit, post-adoption stale check, reservations,
isolation, P0–P4 findings, uncertainty, and the next safe action. Never claim
full Protocol or Word acceptance from this focused pass.
