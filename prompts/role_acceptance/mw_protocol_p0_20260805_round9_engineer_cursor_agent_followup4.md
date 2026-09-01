# Protocol P0 engineer round 9 — same-session continuation after gate-reconciliation repair

## Hard boundaries

- Runner-managed output file: `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup4.md`. Return a compact handoff for the runner; do not write this report path directly.
- Continue the same isolated engineer-perspective Protocol P0 acceptance session, the same project and the same visible headful browser. Do not start a new project, role, clone, search, or model worker.
- Clone: `/private/tmp/mw-p0-engineer-r9.vZbWIw`
- Project: `proj_user_0e7ac527231c`
- Pipeline: `mwpipe_a28fe3b181b0b20d1927`
- API: `http://127.0.0.1:8941`
- Frontend: `http://127.0.0.1:5222`

Read these files only:

- `AGENTS.md`
- `context/mw_protocol_p0_max_clean_rounds_20260805_context.md`
- `runs/mw_protocol_p0_max_clean_rounds_20260805.md`
- `reviews/mw_protocol_p0_max_clean_rounds_20260805.md`
- `metrics/mw_protocol_p0_max_clean_rounds_20260805.md`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/medical_writing_corpus_readiness.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `tests/test_medical_writing_corpus_readiness.py`
- `tests/test_frontend_medical_writing_translation_batch_contract.py`
- `prompts/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup3.md`

- `services/api/app/medical_writing_corpus_readiness.py`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `tests/test_medical_writing_corpus_readiness.py`
- `tests/test_frontend_medical_writing_translation_batch_contract.py`

The fixed product receipt remains DeepSeek `deepseek-v4-flash` with thinking/max for LLM and translation-support, official PaddleOCR-VL-1.6 for OCR, and oMLX `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX` for body translation. Do not rerun the immutable search, triage, download, preparation, OCR, translation, corpus analysis, or failed items.

## Repair boundary to verify

Two minimal repairs are now present and locally tested:

1. `MedicalWritingCorpusReadinessService.recalculate()` treats a valid confirmed `discovery_basket_projection` as the candidate-triage source before PICOS, while keeping final `corpus_triage` finalization PICOS-gated. It also uses those retained IDs for downstream artifact/brief evaluation and includes the discovery projection in the source hash.
2. The prefill route is pinned to model name `deepseek-v4-flash` and envelope reasoning effort `max`. `WritingReferencePanel` now refreshes the parent workspace **and explicitly POSTs** the corpus-gate recalculation after a settled batch, then reloads the authoritative journey. Local focused tests and frontend build passed; do not treat that as runtime acceptance.

## Visible acceptance assignment

Use only real headful/visible Playwright or equivalent browser interaction for user actions. API reads are allowed only to cross-check visible state; do not replace the required click with a direct HTTP POST or SQLite write.

1. Reopen the current authoring/research-pipeline screen in the same browser. Verify that the existing 16 approved evidence briefs remain visible and that the batch itself is unchanged. Do **not** click medical-review, retry, download, OCR, translation, or any completed action.
2. From the visible authoring surface, click `更新建议` exactly once if the control is enabled and the current package is stale/partial. This is the one allowed prefill retry for this pass. Do not click it repeatedly. Capture the visible response and the resulting logical call/reservation/model identity. If the provider returns the same unbound single-candidate shape, stop at that contract failure; do not coerce it or invent a target.
3. Confirm whether the parent refresh/recalculation repair changes the gate's candidate-triage evidence to the confirmed discovery basket while leaving `corpus_triage` pending until PICOS. Distinguish the intended pre-PICOS state from a genuine stale/false blocker.
4. Continue only through evidence-bound framing/PICOS controls if the UI now exposes them. Never type placeholder prose or invent exact dose, sample size, endpoint timing, thresholds, visit windows, or product facts. If required fields remain without evidence-bound candidates, stop at the first honest blocker and record the exact UI/API contract.
5. Only if all normal gates become valid, proceed to substantive Protocol drafting and formal Word export. Read the whole document, not headings: verify complete non-placeholder Chinese regulatory prose, scientific consistency, no blanket `不适用`, no `待……决策/确定后……`, no AI/log traces, and TOC/numbering/references/cross-links/styles/rendering.

At every unexpected result, trace the first broken contract (UI control, request, provider envelope, persisted projection, generation reservation, or export), and distinguish harness failure from product failure. Keep all immutable rows, the 16 approved briefs, the 4 candidate-ready and 15 excluded statuses, the corpus-analysis artifact, and route/idempotency lineage unchanged. Do not broaden to the senior-medical-monitor role or provider matrix.

## Output

Return a compact handoff with sources/evidence read; visible actions and actual outputs; gate/revision/stage transitions; prefill model/call/result and duplicate count; approved-brief and discovery-projection evidence; any PICOS/full-draft/Word locators; P0–P4 findings with root causes; failed paths and uncertainty; and the next safe action. Do not claim a clean round unless a complete substantive Word and all required gates are evidenced. The runner-owned report must be written to `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup4.md`.
