# Protocol P0 engineer round 9 — same-session continuation after approved-brief refresh repair

## Hard boundaries

- Runner-managed output file: `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup3.md`. Return a compact handoff for the runner; do not write this report path directly.
- Continue the same isolated engineer-perspective Protocol P0 acceptance session, the same project and the same visible headful browser. Do not start a new project, new role, or new clone.
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
- `tests/test_frontend_medical_writing_translation_batch_contract.py`
- `prompts/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup2.md`

The fixed product receipt remains DeepSeek `deepseek-v4-flash` with thinking/max for LLM and translation-support, official PaddleOCR-VL-1.6 for OCR, and oMLX `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX` for body translation. The immutable completed corpus-analysis artifact is `mwca_d259c8cc698d41d741fd0fbd`; its exact pipeline/snapshot/route lineage is already bound to the parent. Do not rerun that analysis or any completed search, triage, download, preparation, OCR, translation, or failed retryable item.

## Recovered state and repair boundary

The preceding visible pass confirmed that the one-click medical-review action created 16 current approved evidence briefs and 16 admitted translations, but the adjacent `已准入证据` tab remained at `0 条` because the batch panel refreshed only its own batch and the batch revision marker did not change. A bounded frontend repair now calls `await onBatchSettled()` immediately after the successful `loadBatch(batchId)`, so the parent workspace must be refreshed without repeating the medical-review POST or any model call. The API read-only baseline after repair is journey revision 6, `current_stage=framing`, `status=stage1_in_progress`, `framing_complete=false`, `picos_complete=false`, `corpus_triage=pending`, and `approved_evidence_briefs=16`. The corpus gate remains not-ready with five explicit unsatisfied requirements; do not bypass the PICOS/framing contract.

The prior visible `更新建议` call completed one logical prefill reservation but the provider response failed the bulk envelope contract (`top_level=claim_bindings,clinical_tradeoffs,evidence_gaps,preview,rationale,recommendation_role,structured_value`); the package remains deterministic/partial and no duplicate call was made. Do not coerce this response or invent a target field. If a new visible update is genuinely needed after the gate repair, use at most one user-visible retry, record the new logical idempotency key and actual provider result, and stop at the exact contract boundary if the same shape failure recurs.

## Visible acceptance assignment

Use only real headful/visible Playwright or equivalent browser interaction for user actions. API reads are allowed only to cross-check what the UI visibly reports; do not replace clicks with HTTP POSTs or SQLite writes. Reopen the current research-pipeline/authoring screen and first verify the repaired refresh contract: after the existing confirmed batch is loaded, the visible `已准入证据` tab should show 16 current briefs (or an equivalent nonzero list with the same IDs), while the translation batch remains unchanged. Do not click the one-click medical-review control again; do not rerun analysis, search, triage, downloads, OCR, translation, retries, or any other completed work.

Then continue from the visible authoring surface. Use the deterministic or evidence-bound prefill cards as reviewable suggestions and adopt only candidates with a clear target and evidence; complete the minimum framing fields and click the visible completion control. Complete PICOS using the visible evidence-bound recommendations and medical-review controls. Do not fabricate exact dose, sample size, endpoint timing, thresholds, or visit windows merely to enable a button. If a required field has no evidence-bound candidate, record the precise UI/API contract and stop there rather than typing placeholder prose.

When the normal corpus gate is satisfied through visible triage/admission/PICOS actions, proceed to the complete Protocol draft, all review/consistency/freeze gates, and formal Word export. Read the resulting document end-to-end, not just its headings. Check indication- and phase-specific Chinese content, scientific consistency, no empty bodies, no blanket `不适用`, no `待……决策/确定后……`, no AI/log traces or unresolved placeholders, and verify TOC/TOF, numbering, references/locators, cross-links, styles, headers/footers, and real rendering. If a full Word cannot be reached, stop at the first broken contract and preserve exact evidence.

At every unexpected result, trace the first broken contract (UI control, request, provider envelope, persisted row, generation/lease, parent refresh/projection, or export) and distinguish harness failure from product failure. Keep immutable OCR failures, failed-retryable translation rows, the corpus-analysis artifact, route receipts, model-call counts, and idempotency records unchanged. Do not broaden to the senior-medical-monitor role, other providers, or the multi-provider matrix.

## Output

Return a compact handoff with sources/evidence read; visible actions and actual outputs; exact stage/revision transitions; provider/model calls and duplicate count; approved-brief refresh evidence; prefill response contract evidence; PICOS/corpus/full-draft/Word locators and checks; P0–P4 findings with root causes; failed paths and uncertainty; and the next safe action. Do not claim a clean round unless a complete substantive Word and all required gates are evidenced. The runner-owned report must be written to `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup3.md`.
