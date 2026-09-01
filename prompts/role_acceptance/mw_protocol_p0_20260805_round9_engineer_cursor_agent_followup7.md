# Protocol P0 engineer round 9 — one visible prefill retry after timeout-budget repair

## Hard boundaries

- Runner-managed output file: `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup7.md`; return a compact handoff only.
- Continue the same engineer session, project `proj_user_0e7ac527231c`, clone `/private/tmp/mw-p0-engineer-r9.vZbWIw`, pipeline `mwpipe_a28fe3b181b0b20d1927`, visible browser, API 8941 and Vite 5222. Do not create a new project or role.
- The clone API has been restarted with `WORKBENCH_AI_PREFILL_TIMEOUT_SECONDS=900`; do not restart it, change the route, or use a backend/API shortcut for the user action.

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
- `prompts/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup6.md`

Fixed receipt: DeepSeek `deepseek-v4-flash` thinking/max for independent and translation-support, official PaddleOCR-VL-1.6 OCR, oMLX `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX` body translation. Do not rerun search, triage, download, preparation, OCR, translation, corpus analysis, or completed/failed items.

## Known state and one allowed action

Follow-up6 proved the authoritative-revision repair: the visible request used revision 7 and persisted revision 8. The old revision-6 unknown reservation `mwprefillcall_45363c651fdf467d8c7844ca` and the new revision-7 unknown reservation `mwprefillcall_f120b44838ff448c99a0ffb7` are immutable; each has one physical attempt and must not be replayed. The latter hit the old 300 s provider plus 15 s local wait boundary without a provider response.

The product-side repair is now built and tested: `DeepSeekPrefillAdapter` resolves a dedicated bounded prefill timeout, defaults to 900 s for max reasoning, honors `WORKBENCH_AI_PREFILL_TIMEOUT_SECONDS`, and synchronizes the provider transport with the local wait boundary. The fixed model/effort, one-attempt reservation, evidence gates, and fail-closed unknown-outcome semantics are unchanged. Focused timeout/reservation tests passed and the full prefill/corpus/evidence-binding set passed (`272 passed`).

Use real headful/visible Playwright for the user action. Reopen the authoring screen, verify authoritative revision **8**, the pre-PICOS gate (4/5; only PICOS alignment missing), and both old unknown reservations. Then click visible `更新建议` exactly once with the force option if the UI exposes it. This is the single explicit retry after the timeout repair. Do not click again, manually clear a lease, mutate SQLite, or trigger any other workflow stage.

Allow the provider enough time to complete under the 900 s budget; do not fixed-interval poll or redispatch. If the call returns, verify one new logical call/one transport attempt, actual provider/model identity, structured-schema validity, catalog hash, and evidence-bound candidates. Adopt only clearly bound candidates and never invent design pattern, population, objectives, dose, sample size, endpoints, timing, or visit windows. If the response is malformed/unbound, 409, timeout, or identity-mismatched, stop at that exact contract and preserve evidence. Only if framing/PICOS genuinely complete may you proceed to full substantive Protocol and Word review; headings-only or placeholder output never counts.

At every unexpected result, trace the first broken contract and distinguish UI/harness from product/provider. Keep the 16 approved briefs, candidate-ready/excluded statuses, corpus-analysis artifact, both unknown reservations, route receipt, and all idempotency lineage unchanged.

## Output

Report visible actions and outputs, authoritative revision, request/reservation/model lineage, timeout/wait evidence, gate/stage transitions, any substantive framing/PICOS/full-draft/Word evidence, P0–P4 findings with root causes, uncertainty, and next safe action. Do not claim a clean round without complete substantive Word and all gates. Runner report path: `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup7.md`.
