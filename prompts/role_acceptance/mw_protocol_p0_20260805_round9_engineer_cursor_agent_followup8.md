# Protocol P0 engineer round 9 — visible candidate/adoption contract diagnosis

## Purpose

Continue the same isolated engineer pass after follow-up7. This is not another
prefill-generation retry. The timeout repair already passed once in the real
UI; the next question is whether a senior medical manager can safely review and
adopt the returned candidates without typing unsupported protocol facts.

## Hard boundaries

- Runner-managed output file: `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup8.md`; return a compact handoff only.
- Use the same isolated clone `/private/tmp/mw-p0-engineer-r9.vZbWIw`, project
  `proj_user_0e7ac527231c`, pipeline `mwpipe_a28fe3b181b0b20d1927`, the existing
  API on `127.0.0.1:8941`, and the existing Vite UI on `127.0.0.1:5222`.
- The API is already running with `WORKBENCH_AI_PREFILL_TIMEOUT_SECONDS=900`.
  Do not restart or reconfigure it. If Vite has stopped, start only Vite in the
  clone with a detached/session-preserving process; never restart the API.
- Use a real visible/headful Playwright browser. Do not use direct API calls as
  a substitute for user clicks; read-only API/SQLite inspection is allowed to
  verify evidence after the visible action.
- Do not rerun search, triage, download, preparation, OCR, translation, corpus
  analysis, or any completed/failed item. Do not click `更新建议` or any other
  prefill-generation control. Do not clear or rewrite the two immutable unknown
  reservations or completed evidence.

## Current source-of-truth checkpoint

- Authoring journey revision **9**, stage `framing`, package status `partial`,
  package revision 1, pre-PICOS gate 4/5; no substantive Protocol or Word.
- Completed prefill reservation/event: `mwprefillcall_d4b093096491417690b618f0`
  / `mwjourney_event_e64837b8f3c973b4634a44bf`, one transport attempt, DeepSeek
  `deepseek-v4-flash`, prompt v7, 702-entry evidence catalog.
- Immutable unknown reservations: revision-6
  `mwprefillcall_45363c651fdf467d8c7844ca` and revision-7
  `mwprefillcall_f120b44838ff448c99a0ffb7`; they must remain unchanged.
- Candidate facts already observed: `framing.design_pattern` is an unbound,
  insufficient deterministic suggestion; `framing.intrinsic_objectives` has
  no candidate; bound `picos.design_archetype` and population/intervention
  suggestions are competitor observations with `manual_only` and
  partially-supported/insufficient/pending status. The only directly supported
  project-fact example is a document-title candidate, but it is still rendered
  `manual_only` by the current contract.

Read these files only:

- `AGENTS.md`
- `context/mw_protocol_p0_max_clean_rounds_20260805_context.md`
- `runs/mw_protocol_p0_max_clean_rounds_20260805.md`
- `reviews/mw_protocol_p0_max_clean_rounds_20260805.md`
- `metrics/mw_protocol_p0_max_clean_rounds_20260805.md`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.jsx`
- `prompts/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup7_new_session.md`

Runner report path: `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup8.md`.

## Single bounded action

1. Reopen the authoring screen visibly and inspect the actual candidate cards,
   `高级微调`, the composite package panel, and the stage controls. Confirm
   whether a user can:
   - distinguish project facts from competitor observations;
   - see the source quote and limitation before adoption;
   - provide an explicit audited per-path override or skip for a composite
     candidate; and
   - adopt a supported project-fact candidate without inventing a design,
     objective, dose, endpoint, sample size, timing, or visit window.
2. If a genuine composite `module/design_package` candidate is present, select
   it visibly and inspect the per-path override/skip UI. You may submit at most
   one adoption only when every applied value is either directly bound to the
   authoritative catalog or an explicit user override/skip is recorded in the
   returned receipt. Do not treat a competitor observation as a current project
   fact. If no such candidate is present, do not fabricate one and do not submit
   a forced adoption.
3. If the only route to complete framing is free-text entry, do not enter new
   clinical facts on behalf of the project. Record that the clean test fixture
   supplied only product/indication/phase and that the system’s AI-first path
   cannot safely complete required framing under its own evidence contract.
4. Do not advance to PICOS or full-draft generation unless framing is genuinely
   complete through an auditable user-confirmed action. Headings-only or blank
   output never counts as a substantive result.

## Root-cause review requirements

For every unexpected UI result, identify the first broken contract and classify
it as harness/runtime, frontend, backend policy, provider, or evidence-source
limitation. Specifically check whether the UI’s disabled state and message
match the backend 422 policy for `manual_only`, `pending_decision`,
`insufficient`, and unsupported gaps. Do not call a truthful fail-closed block a
provider failure, but do record the product usability gap if a safe project-fact
candidate is impossible to adopt without retyping it.

## Output

Return a compact handoff with visible actions, screenshots/DOM evidence, the
candidate/adoption state, any single receipt or proof that no safe receipt was
possible, unchanged reservation IDs, P0–P4 findings and root causes, uncertainty,
and the next bounded product/test action. Do not claim a clean round: no clean
round is possible without substantive full Protocol Word plus structural,
reference-link, and visual checks.
