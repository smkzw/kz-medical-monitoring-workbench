# Protocol P0 engineer round 9 — controlled new Cursor session after Ask-mode resume boundary

## Why this is a new session

The prior Cursor session `095567b4-68c8-446b-a254-c92601765c16` is preserved. Two runner continuations returned without any browser/API action because that session is permanently in Cursor Ask mode; `--force` changes command approval but cannot change the stored session mode. The route runner and the session produced no prefill POST, no click, and no data mutation. This new Cursor Agent session is the bounded recovery for that terminal capability boundary, not a workflow redispatch.

## Hard boundaries

- Runner-managed output file: `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup7_new_session.md`; return a compact handoff only.
- Use the same isolated clone and project, `/private/tmp/mw-p0-engineer-r9.vZbWIw`, project `proj_user_0e7ac527231c`, pipeline `mwpipe_a28fe3b181b0b20d1927`; use a real headful/visible browser and the existing API 8941/Vite 5222. Do not create a project or role.
- The clone API is already running with `WORKBENCH_AI_PREFILL_TIMEOUT_SECONDS=900`; do not restart it, change route/config, or use backend/API shortcuts for the user action.

Read these files only:

- `AGENTS.md`
- `context/mw_protocol_p0_max_clean_rounds_20260805_context.md`
- `runs/mw_protocol_p0_max_clean_rounds_20260805.md`
- `reviews/mw_protocol_p0_max_clean_rounds_20260805.md`
- `metrics/mw_protocol_p0_max_clean_rounds_20260805.md`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_corpus_readiness.py`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `prompts/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup7.md`

Fixed receipt: DeepSeek `deepseek-v4-flash` thinking/max for independent and translation-support, official PaddleOCR-VL-1.6 OCR, oMLX `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX` body translation. Do not rerun search, triage, download, preparation, OCR, translation, corpus analysis, or completed/failed items.

## One allowed action

Read the authoritative journey and SQLite read-only: revision **8**, pre-PICOS gate 4/5 (only PICOS alignment missing), and both immutable unknown reservations `mwprefillcall_45363c651fdf467d8c7844ca` and `mwprefillcall_f120b44838ff448c99a0ffb7`. Then use visible Playwright to reopen the authoring screen and click visible `更新建议` exactly once with force if exposed. This is the one explicit retry after the route-specific timeout repair; the prior Ask-mode session did not click and created no new call.

The prefill adapter now uses a dedicated 900 s budget (explicit override bounded 60–1800 s) synchronized between the provider and local wait; model/effort, evidence binding, one-attempt reservation, and fail-closed unknown-outcome semantics are unchanged. Allow the provider to complete; do not fixed-interval poll, click again, manually clear a lease, mutate SQLite, or trigger any other workflow stage.

If the call returns, verify one new logical call/one transport attempt, actual provider/model identity, structured schema, catalog hash, and evidence-bound candidates. Adopt only directly bound candidates. Never invent design pattern, population, objectives, dose, sample size, endpoints, timing, or visit windows. If malformed/unbound, 409, timeout, or identity-mismatched, stop at that contract. Only if framing/PICOS genuinely complete may you proceed to substantive Protocol/Word review; headings-only output never counts.

At every unexpected result, identify the first broken contract and distinguish UI/harness from product/provider. Preserve all completed evidence, approved briefs, candidate-ready/excluded statuses, corpus-analysis artifact, both unknown reservations, route receipt, and idempotency lineage.

## Output

Report visible actions, prefill lineage and timeout evidence, gate/stage transitions, any substantive framing/PICOS/full-draft/Word evidence, P0–P4 findings with root causes, uncertainty, and next safe action. Do not claim a clean round without complete substantive Word and all gates. Runner report path: `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup7_new_session.md`.
