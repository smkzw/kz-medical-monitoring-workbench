# Protocol P0 — engineer role, repaired deterministic identity adoption

## Purpose

Verify the second bounded repair in a fresh real user flow. The repair binds
only the exact creation-minimum document-title templates to the immutable
product/indication/phase catalog facts and makes phase-only design prose
pending/manual-only. This remains a focused contract pass, not a full
Protocol/Word acceptance round.

## Hard boundaries

- Fresh isolated clone/runtime: `/private/tmp/mw-p0-engineer-r11.GoQYbK`.
- API `http://127.0.0.1:8943` and Vite `http://127.0.0.1:5224` are already
  running the repaired source. Do not restart, reconfigure, or stop them. Do
  not touch r9 `/private/tmp/mw-p0-engineer-r9.vZbWIw` or r10
  `/private/tmp/mw-p0-engineer-r10.1RQ2UD`.
- The r11 project store is empty. Create exactly one project through the
  visible UI, using product `QZ-CRSNP03`, indication `慢性鼻窦炎伴鼻息肉`, and
  `II期`. Never create a project by API or SQLite.
- Use real headful/visible Playwright for all user actions. Read-only API or
  SQLite inspection is allowed only after visible actions to verify receipts,
  catalog identity, and idempotency.
- Do not run or manually click search, triage, downloads, preparation, OCR,
  translation, corpus analysis, PICOS, full drafting, freeze, Word export, or
  medical-monitoring work. The product may automatically start its initial
  search/prefill sequence after visible project creation; observe that
  automatic behavior, do not trigger a duplicate search.
- Do not enter or adopt any unsupported design, population, intervention,
  dose, endpoint, timing, visit, or sample-size fact. Do not use composite
  skip-all or free text to fabricate framing completion. Stop after the single
  title adoption probe.

Read these files only:

- `AGENTS.md`
- `context/mw_protocol_p0_max_clean_rounds_20260805_context.md`
- `runs/mw_protocol_p0_max_clean_rounds_20260805.md`
- `reviews/mw_protocol_p0_max_clean_rounds_20260805.md`
- `metrics/mw_protocol_p0_max_clean_rounds_20260805.md`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_prefill_evidence.py`
- `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.jsx`

## Bounded visible sequence

1. Start from the empty dashboard and create the one project above through the
   UI. Record project/journey IDs and the four role/model settings. Let the
   product's automatic creation-time prefill and automatic registry search
   settle to a terminal visible state; record any unexpected timing or
   snapshot behavior. The first create-time prefill is expected to be
   deterministic and may precede search attachment.
2. After the search snapshot is visibly attached and the authoring page is no
   longer in its initial “正在启动公开研究检索” state, click visible
   `更新建议` exactly once. This is the only manually triggered prefill update
   in this pass. Wait naturally for the single request to finish; do not
   fixed-interval poll, force retry, redispatch, or click it again. If the
   research gate correctly leaves design/PICOS scaffolds pending, record it;
   do not bypass it.
3. Open the visible single-field evidence drawer and inspect the
   `framing.document_title` candidates. The three deterministic title variants
   must show:
   - `supported` evidence status;
   - `batch_allowed` adoption mode;
   - three bindings to product, indication, and phase `current_project_fact`
     entries with one catalog ID/SHA; and
   - an enabled single-candidate `采用` control.
   Click `采用` for exactly one title candidate, once. Capture the HTTP result,
   journey/package revision, candidate state, evidence-verification receipt,
   and audit event. Do not use `修改后采用` unless the unedited button is
   genuinely unavailable; if unavailable, record the exact frontend/backend
   reason and do not type a replacement.
4. Verify that deterministic `framing.design_pattern` is now
   `pending_decision`/`manual_only` with no claim bindings and no enabled
   single-adopt control. If a competitor/corpus candidate is surfaced, verify
   it is `manual_only` and do not adopt it. If none is surfaced because the
   fresh project has no corpus analysis, record that absence as expected
   evidence scope, not as a competitor search failure.
5. Stop. Read back the journey and reservation/event tables only to prove at
   most one manual prefill update and one title adoption, no duplicate model
   call, no duplicate audit event, and no cross-project data. Do not advance to
   PICOS or full draft.

## First-principles diagnosis

For every unexpected result, locate the first broken contract and classify it
as harness/runtime, frontend, backend policy, provider, or evidence-source
limitation. Specifically distinguish:

- automatic create/search ordering from a duplicate user action;
- a stale package/catalog revision after snapshot attachment from a bad
  binding or provider response;
- a supported identity fact from an unbound phase heuristic; and
- a truthful `corpus_not_ready`/pending scaffold from an AI failure.

The safe predicate is intentionally narrow: only the exact title templates with
complete, gap-free `current_project_fact` bindings may be `batch_allowed`;
competitor, corpus, mixed, partial, pending, design, PICOS, and composite
candidates must remain fail-closed. Existing live catalog hash verification,
CAS, one-attempt reservations, and idempotency keys must be preserved.

## Evidence and handoff

Write exactly one output file:
`runs/role_acceptance/mw_protocol_p0_20260805_round11_engineer_cursor_agent_project_fact_live.md`.
Write screenshots/DOM probes and compact JSON under
`/private/tmp/mw-p0-engineer-r11.GoQYbK/evidence/`; do not write other files in
the workbench. Return a compact handoff with visible actions, IDs/builds,
role receipt, both prefill lineages, title bindings and adoption audit receipt,
design/competitor fail-closed state, unchanged prior clones, P0–P4 findings,
uncertainty, and next action. Never claim clean, substantive Protocol, or Word
acceptance from this focused pass.
