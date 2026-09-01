# Protocol P0 engineer round 9 — same-session continuation after orphan-analysis repair

## Hard boundaries

- Runner-managed output file: `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup.md`. Return a compact handoff for the runner; do not write this report path directly.
- You are continuing the same isolated engineer-perspective Protocol P0 acceptance session, not starting a new project or a new role. Work only against the existing clean clone and the visible browser UI:

- clone: `/private/tmp/mw-p0-engineer-r9.vZbWIw`
- project: `proj_user_0e7ac527231c`
- pipeline: `mwpipe_a28fe3b181b0b20d1927`
- API: `http://127.0.0.1:8941`
- frontend: `http://127.0.0.1:5222`

Read these files only:

- `AGENTS.md`
- `context/mw_protocol_p0_max_clean_rounds_20260805_context.md`
- `runs/mw_protocol_p0_max_clean_rounds_20260805.md`
- `reviews/mw_protocol_p0_max_clean_rounds_20260805.md`
- `metrics/mw_protocol_p0_max_clean_rounds_20260805.md`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/medical_writing_corpus_analysis_ai.py`
- `prompts/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent.md`

The fixed product receipt remains DeepSeek `deepseek-v4-flash` with thinking/max for LLM and translation-support, official PaddleOCR-VL-1.6 for OCR, and oMLX `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX` for body translation. The prior visible continuation proved 4/4 critical anchors and created the immutable completed corpus artifact `mwca_d259c8cc698d41d741fd0fbd`, but a parent-generation race left the persisted parent at `translating` without the analysis identity. A bounded source repair now performs an exact pipeline/snapshot/frozen-route read-only reconciliation; it never invokes a model or rewrites the immutable corpus row. The live status check after restart showed `awaiting_corpus_admission`, `round1_material_ready=true`, `design_recommendations_unlocked=true`, and the same translation batch/failed items.

Resume from this state through the real UI. Do not restart search, triage, download, preparation, OCR, or the already completed corpus-analysis call. Do not use HTTP/API calls as a substitute for user clicks. The only acceptable user interaction evidence is headful/visible Playwright or equivalent browser interaction; API reads may be used only to cross-check what the UI visibly reported. Keep the existing failed OCR and failed-retryable translation rows immutable and do not click a retry merely to make the page look green.

First reopen the current research-pipeline screen and verify the recovery projection is truthful: the UI must no longer present a translating hang, must show the design/research-material action that is actually available, and must not show a duplicate analysis/model-call count. If the UI disagrees with the status, investigate the route/state projection root cause and record it before acting.

Then continue the engineer acceptance path using visible controls: complete/confirm the required PICOS or study-definition decisions, open the evidence-bound design recommendation, generate a complete Protocol draft, perform the required review/consistency/freeze gates, and export the formal Word document. Read the whole resulting document, not only its headings. Check that every required regulatory section contains indication-specific, phase-appropriate, design-consistent Chinese content; there must be no empty chapter bodies, generic “不适用” padding, `待……决策/确定后……`, AI/log traces, or unresolved placeholders. Verify tables, numbering, TOC/TOF, cross-references, reference links/locators, style/headers/footers, and render the Word file in the real document viewer when possible.

At every unexpected result, trace the first broken contract (source/route, request, persisted row, parent projection, UI action, or export) and distinguish harness defects from product defects. Do not silently accept an HTTP 200, a skeleton, a single successful button, or a stale status. If a true blocker remains, stop at that exact boundary without inventing content, state the minimal reproducible evidence and the safest next action. Do not broaden to the senior-medical-monitor role or the multi-provider matrix in this session.

## Output

Return a compact execution handoff containing: sources and evidence read; visible actions and actual outputs; model/provider calls and whether any were duplicated; full-draft/Word locators and checks; P0–P4 findings with root causes; failed paths and uncertainty; and the next recommended action. Do not claim a clean round unless the full Word and all required gates are actually evidenced. The runner-owned report must be written to `runs/role_acceptance/mw_protocol_p0_20260805_round9_engineer_cursor_agent_followup.md`.
