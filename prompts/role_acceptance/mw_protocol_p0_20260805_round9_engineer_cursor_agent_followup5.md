# Protocol P0 engineer round 9 — stale-prefill race repair continuation

## Hard boundaries

- Runner-managed output file: `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup5.md`; return only a compact handoff and do not write that report path.
- Continue the same isolated engineer session, project, clone, and visible headful browser. Do not create a new project or role.
- Clone: `/private/tmp/mw-p0-engineer-r9.vZbWIw`; project: `proj_user_0e7ac527231c`; pipeline: `mwpipe_a28fe3b181b0b20d1927`; API `http://127.0.0.1:8941`; frontend `http://127.0.0.1:5222`.

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
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `tests/test_frontend_medical_writing_contract.py`
- `prompts/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup4.md`

The fixed receipt remains DeepSeek `deepseek-v4-flash` thinking/max for independent and translation-support, official PaddleOCR-VL-1.6 for OCR, and oMLX `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX` for body translation. Do not rerun search, triage, download, preparation, OCR, translation, corpus analysis, or completed/failed items.

## Race evidence and repair boundary

The previous visible pass proved the gate repair: revision 6→7, discovery retained 87, candidate triage/protocol/Chinese translation/medical admission covered, and `corpus_triage` intentionally pending until PICOS. Its one `更新建议` request started a prefill reservation at expected revision 6 while the delayed gate recalculate advanced the journey to revision 7; one transport attempt later became `unknown_outcome` and the request returned 409. Keep that old logical call/row unchanged.

The front-end now performs an authoritative journey GET immediately before the single external prefill request and passes the fresh revision. This pass may use exactly one explicit force retry for the incomplete prefill route, only through the visible `更新建议` control. Never interrupt an in-flight call and never click again after a terminal error.

## Visible acceptance assignment

Use real headful/visible Playwright or equivalent for user actions. API reads are read-only cross-checks; do not replace the visible action with a POST or SQLite write.

1. Reopen the authoring screen. Verify the intended pre-PICOS state (4/5 covered, only PICOS alignment missing), 16 approved briefs, the prior unknown reservation, and the fixed route receipt.
2. Click visible `更新建议` exactly once. Verify network/UI and reservation lineage: current revision 7 (not stale 6), at most one new logical call, and no duplicate prior call. If a valid bulk schema arrives, inspect evidence-bound candidates and adopt only clear targets with citations. If the unbound single-candidate shape, 409, timeout, or model mismatch recurs, stop; do not coerce, retry, or invent.
3. If evidence-bound framing candidates appear, continue visible framing and PICOS only with substantive source-bound content. Never invent dose, sample size, endpoint timing, thresholds, visit windows, or product facts; keep `corpus_triage=pending` until PICOS is complete.
4. Only if normal gates pass, proceed through full Protocol drafting, formal Word export, and whole-document review (no empty/heading-only body, blanket `不适用`, `待……决策/确定后……`, AI/log residue, or unresolved placeholders; verify TOC/numbering/references/cross-links/styles/rendering).

At every unexpected result, trace the first broken contract (fresh revision, reservation, one transport attempt, provider envelope, persisted event, UI state, or export). Keep immutable rows, 16 approved briefs, 4 candidate-ready/15 excluded statuses, corpus-analysis artifact, and route/idempotency lineage unchanged. Do not broaden to the senior-medical-monitor role or provider matrix.

## Output

Return sources/evidence read; visible actions and actual outputs; fresh revision and prefill reservation/call lineage; provider receipt; gate/stage transitions; any framing/PICOS/full-draft/Word locators; P0–P4 findings with root causes; failed paths and uncertainty; next safe action. Do not claim a clean round without complete substantive Word and all gates. Runner report: `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup5.md`.
