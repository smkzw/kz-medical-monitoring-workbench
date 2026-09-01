# Protocol P0 engineer round 9 — same-session prefill retry after UI typo fix

## Hard boundaries

- Runner-managed output file: `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup6.md`; return a compact handoff only.
- Continue the same engineer session, project `proj_user_0e7ac527231c`, clone `/private/tmp/mw-p0-engineer-r9.vZbWIw`, pipeline `mwpipe_a28fe3b181b0b20d1927`, visible browser, API 8941 and Vite 5222. Do not create a new project or role.

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
- `prompts/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup5.md`

Fixed receipt: DeepSeek `deepseek-v4-flash` thinking/max for independent and translation-support, official PaddleOCR-VL-1.6 OCR, oMLX `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX` body translation. Do not rerun search, triage, download, preparation, OCR, translation, corpus analysis, or completed/failed items.

## Known state and one allowed action

Follow-up4 proved the pre-PICOS gate: revision 7, discovery retained 87, 4/5 requirements covered, only PICOS alignment missing, 16 approved briefs, final `corpus_triage` pending. The first stale prefill call at revision 6 remains immutable: logical call `mwprefillcall_45363c651fdf467d8c7844ca`, one transport attempt, `unknown_outcome`. Follow-up5 found and repaired a front-end typo (`onJourneyChange` versus the actual `onJourneyChanged`) before any second POST; no new reservation was created.

The fresh-revision GET repair and prop-name fix are now built and locally tested. Use real headful/visible Playwright for the user action. Reopen the authoring screen, verify revision 7 and the old reservation, then click visible `更新建议` exactly once. The click is the one explicit force retry for the incomplete prefill path. Verify the request uses current revision 7 and creates at most one new logical call; do not click again, manually clear a lease, or mutate SQLite.

If the provider returns a valid bulk schema, inspect evidence-bound field paths and citations; adopt only clearly bound candidates. If the response is malformed/unbound, 409, timeout, or identity-mismatched, stop at that exact contract and preserve evidence. Never invent design pattern, population, objectives, dose, sample size, endpoints, timing, or visit windows. Only if framing/PICOS genuinely complete may you proceed to full substantive Protocol and Word review; headings-only or placeholder output never counts.

At every unexpected result, trace the first broken contract and distinguish UI/harness from product/provider. Keep the 16 approved briefs, 4 candidate-ready/15 excluded statuses, corpus-analysis artifact, old reservation, route receipt, and all idempotency lineage unchanged.

## Output

Report visible actions and outputs, fresh revision, request/reservation/model lineage, gate/stage transitions, any substantive framing/PICOS/full-draft/Word evidence, P0–P4 findings with root causes, uncertainty, and next safe action. Do not claim a clean round without complete substantive Word and all gates. Runner report path: `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup6.md`.
