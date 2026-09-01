# Protocol P0 — engineer role, fresh live project-fact adoption proof

## Purpose

Run one bounded, fresh, headful UI acceptance pass after the narrow backend
repair in `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`.
The only question in this pass is whether a confirmed project identity fact can
be adopted through the real user path while competitor or incomplete clinical
observations remain fail-closed. This is not a full Protocol/Word round and
must not be reported as clean.

## Hard boundaries

- Fresh isolated clone/runtime: `/private/tmp/mw-p0-engineer-r10.1RQ2UD`.
- API: `http://127.0.0.1:8942`; Vite UI: `http://127.0.0.1:5223`.
- The API and Vite are already running. Do not restart, reconfigure, or stop
  either service. Do not touch the prior r9 clone `/private/tmp/mw-p0-engineer-r9.vZbWIw`.
- The fresh runtime began with an empty project store. Create exactly one new
  project through the visible UI, using product `QZ-ASTHMA02`, indication
  `中重度哮喘`, and `III期`. Do not create projects by API or SQLite.
- Use real headful/visible Playwright for every user action. Read-only API or
  SQLite inspection is allowed only after a visible action to verify the
  persisted receipt and idempotency state.
- Do not run or re-run search, registry triage, downloads, preparation, OCR,
  translation, corpus analysis, PICOS, full drafting, freeze, Word export, or
  medical-monitoring work in this pass. Do not enter unsupported design,
  population, intervention, dose, endpoint, timing, visit, or sample-size
  facts. Do not use “skip all” to fabricate framing completion.
- Use the existing configured AI receipt; do not change model routing. Confirm
  visibly that independent AI and translation-support are DeepSeek
  `deepseek-v4-flash` with thinking/max, OCR is official PaddleOCR-VL-1.6,
  and body translation is oMLX
  `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`. If the UI cannot show the receipt,
  record that as an observability finding rather than changing it.

Read these files only:

- `AGENTS.md`
- `context/mw_protocol_p0_max_clean_rounds_20260805_context.md`
- `runs/mw_protocol_p0_max_clean_rounds_20260805.md`
- `reviews/mw_protocol_p0_max_clean_rounds_20260805.md`
- `metrics/mw_protocol_p0_max_clean_rounds_20260805.md`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.jsx`

## Bounded visible actions

1. Start from the empty dashboard and create the one project above through the
   UI. Record the project and journey identifiers shown by the UI.
2. Open the medical-writing authoring journey and enter only the creation
   minimum. Use the visible `更新建议`/prefill action exactly once. Wait for
   the one request to finish naturally; do not fixed-interval poll,
   redispatch, force retry, or click a second time. If the product correctly
   keeps AI enrichment blocked because the research corpus is not ready, treat
   that as a gate observation and inspect the deterministic project-fact cards;
   do not bypass the gate.
3. Inspect the actual candidate cards, evidence/source text, adoption mode,
   and disabled/enabled controls. Find the title candidate constructed only
   from the current product/indication/phase facts. If it is `supported` and
   `batch_allowed`, click its visible single-candidate `采用` action exactly
   once and capture the returned audit receipt. Do not adopt a composite
   design package.
4. Locate at least one competitor/corpus/partial/pending candidate if one is
   surfaced. Verify it remains `manual_only` (or equivalent fail-closed UI),
   and do not adopt it. If no such candidate is available because the fresh
   project has no corpus, record that absence explicitly and explain why the
   missing evidence is expected; never invent a competitor row.
5. Stop after the single safe project-fact adoption probe. Do not advance to
   PICOS or draft generation. Read back the journey and reservation/event
   rows only to prove one adoption event at most, no duplicate model call,
   and no cross-project contamination.

## First-principles diagnosis

For every unexpected result, identify the first broken contract and classify it
as harness/runtime, frontend, backend policy, provider, or evidence-source
limitation. In particular distinguish:

- a truthful `corpus_not_ready`/pending scaffold from an AI/provider failure;
- a supported current-project fact from an unbound or competitor observation;
- a disabled UI control caused by stale frontend rendering from a backend
  `manual_only`/422 policy; and
- a duplicate or replayed request from the one expected visible request.

The repaired predicate is intentionally narrow: a non-package field candidate
may be `batch_allowed` only when status is `supported`, every binding resolves
to `current_project_fact`, the recommendation role is not pending, and there
are no evidence gaps. Competitor, corpus, mixed, partial, pending, and every
composite package must remain manual-only. Treat any deviation as a product
defect and stop at that contract.

## Evidence and handoff

Write exactly one output file: `runs/role_acceptance/mw_protocol_p0_20260805_round10_engineer_cursor_agent_project_fact_live.md`.
Write screenshots/DOM probes and a compact JSON summary under
`/private/tmp/mw-p0-engineer-r10.1RQ2UD/evidence/`. The runner owns the report
at the output path above;
do not edit that report through tools. Return a concise handoff containing:

- visible actions, project/journey IDs, and UI/API build receipts;
- configured role/model receipt;
- prefill request/reservation/event lineage and physical attempt count;
- candidate adoption mode, evidence bindings, visible control result, and
  audit receipt (or the exact reason no safe adoption was possible);
- whether a competitor fail-closed candidate was observable;
- unchanged prior clone/reservation statement;
- P0–P4 findings with root cause and uncertainty; and
- the next bounded action. Never claim a clean round, substantive Protocol,
  or Word acceptance from this pass.
