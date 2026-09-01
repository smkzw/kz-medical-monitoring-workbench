# Task Context: mw_protocol_p0_phase0b_fact_to_framing_ui_contract_20260802

Created: 2026-08-02 04:20:28
Objective: 在复制出的无 secrets 临时 runtime 中，以真实 Computer Use 审核已持久化的事实提案如何进入研究框架/PICOS审核面；验证证据标签、高影响缺口、草稿/完成阶段阻断和刷新可恢复性，不触碰原始 clone、r42/v36 或上游任务。
Task type: `html_ppt_visual_browser`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max-preview` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/.codex/AGENTS.md` and workspace/workbench `AGENTS.md`
- `context/mw_protocol_p0_phase0b_runtime_draft_word_20260801_context.md`
- `runs/codex_mw_protocol_p0_phase0b_postcorrective_acceptance_20260801.md`
- `runs/MW_PROTOCOL_P0_PHASE0B_RUNTIME_DRAFT_WORD_NO_LOSS_PAUSE_20260801_2218.md`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/App.jsx` and `frontend/vite.config.mjs`
- `services/api/app/main.py`, `services/api/app/medical_writing_fact_intake.py`, and authoring-journey services
- Read-only source clone `runs/runtime_phase0b_postcorrective_20260801` (only selected SQLite stores will be copied; the original remains untouched)
- Current user authorization for routine local project operations; no authority is inferred to alter the original clone or frozen r42/v36 data.

## Scope

- In scope: copy only the project/journey/fact-intake stores needed for `proj_user_cfd2d29284c8` into a fresh temp runtime with no provider secrets; start task-only API/frontend ports; use actual Edge/Computer Use to inspect persisted fact proposals, evidence labels, high-impact gaps, framing/PICOS surface, disabled `完成第一步`, refresh persistence, and the no-document boundary.
- In scope: read-only browser inspection plus reversible local UI actions only if needed to expose the existing persisted proposal; screenshot/AX evidence, API readiness/build identity, and task-owned logs.
- Out of scope: modifying the original clone; committing framing/PICOS; starting public research/triage/download/OCR/translation; any model call; DOCX/Word; r42/v36 rows; stable runtime; medical-monitoring files; Synopsis/CSR; final multi-provider loop; product-source edits unless a deterministic UI contract defect is proven.

## Success Criteria

- API and frontend serve matching build identities from task-only ports and task-only runtime.
- The target journey remains revision 8 / `stage1_in_progress` / framing incomplete; fact conversation remains revision 4 with persisted confirmed values and unresolved gaps.
- Computer Use can visibly reach the fact-intake panel and the research-framing fields; confirmed values are visibly carried into the corresponding fields and evidence/gap labels remain explicit.
- `完成第一步` is visibly disabled or blocked for the unresolved required design facts; no hidden enablement or silent write occurs.
- Reload returns the same persisted proposal/confirmed-value state; no duplicate fact event, AI job, upstream pipeline, or project revision is created.
- Any UI defect is either fixed with a focused source/test delta and rechecked, or recorded with exact evidence and next safe action.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Copy only non-secret SQLite stores. Do not copy `ai_provider_master.key`, `ai_provider_secrets.json`, provider settings, source artifacts, or monitoring databases into the task runtime.
- Do not use API calls as a substitute for Computer Use clicks for UI claims. API is limited to health/readiness and post-inspection evidence queries.
- If browser displays a provider/login/permission prompt, do not transmit credentials or start an external provider; stop that action and record the blocker.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 04:20:28: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 04:21:00: Source/scope/success/risk boundaries recorded. Direct Codex Computer Use selected; no external worker/model dispatch.
- 2026-08-02 04:24:30: Created fresh task runtime `/tmp/mw_phase0b_fact_ui.SiFfQr`; copied only `user_projects.sqlite3`, `medical_writing_authoring_journey.sqlite3`, `medical_writing_fact_intake.sqlite3`, `medical_writing_greenfield.sqlite3`, and `medical_writing_durable_jobs.sqlite3` from the read-only Phase 0B clone. Provider keys/secrets/settings, source artifacts, and monitoring stores were not copied.
- 2026-08-02 04:24:45: Task API on `127.0.0.1:18931` returned health 200 and the expected shared corpus count. Readiness returned HTTP 503 because the intentionally secret-free runtime had no `independent_ai` provider settings; no provider was configured and no model call was made.
- 2026-08-02 04:25:00: Frontend on `127.0.0.1:18932` was opened in Microsoft Edge using Computer Use. The persisted project selector visibly exposed and selected `艾加莫德α注射液 · 全身型重症肌无力 · III期 · MW-III-B7DF09C0`. The UI visibly fail-closed at `当前版本组合不可进入写作工作区`, showing HTTP 503, matching frontend/backend build identities (`web-971cf3d724e46f26` / `api-e1278fe936fc25d0`), contract `medical-writing-api-2026-07-17.1`, and the message `医学写作内容未被修改...`; the fact-intake/framing surface and `完成第一步` could not be reached.
- 2026-08-02 04:25:10: Captured Computer Use screenshot at `/var/folders/yb/31r9763x6_54mdxswxk36c4w0000gn/T/com.openai.sky.CUAService/Edge%20Screenshot%202026-08-02%20at%204.26.13%20AM.jpeg`. This is direct UI evidence, not an API substitute. API/frontend task listeners were stopped and verified closed on ports 18931/18932. No original clone, product source, r42/v36 row, event, job, revision, or upstream data changed.
- 2026-08-02 04:25:20: Verdict is `BLOCKED_BY_FAIL_CLOSED_RUNTIME_READINESS; NOT_READY_FOR_FACT_TO_FRAMING_UI_ACCEPTANCE; NO_PRODUCT_CHANGE`. The next safe action is a non-secret, deterministic readiness fixture/test seam (or an already declared compatible isolated runtime) followed by the same Computer Use inspection; do not add credentials or bypass the readiness contract.

## Superseding follow-up: deterministic readiness fixture and real UI acceptance

- 2026-08-02 04:41–04:49: A deterministic in-memory readiness seam was used only to satisfy the existing `independent_ai` readiness contract (`fixture`, `fixture-no-call`, no provider/model call). It did not bypass the UI gate, add credentials, or claim independent-AI generation. The task API/frontend ran on `127.0.0.1:18933/18934` with the same task-scoped runtime; both listeners were stopped and verified closed after inspection.
- Microsoft Edge Computer Use (real browser actions, not API substitutes) selected the persisted target project, opened 医学写作, opened `高级微调`, and visibly verified: research-framing status `研究框架待确认 · 版本 8`; persisted title/indication/product/III期 and technology type; 10 high-impact gaps; fact-intake user/AI turns; evidence labels (`用户明述`/`AI推断`), confidence levels, rationale, explicit IV-versus-hyaluronidase-SC conflict, and unresolved dose/design/safety gaps. `完成第一步` and `保存草稿` remained disabled with the existing required-facts help. After a real browser refresh and re-entry, the same values, labels, gaps, status, and disabled actions persisted.
- Evidence screenshots were copied into the task temp root: `/tmp/mw_phase0b_fact_ui.SiFfQr/edge_fact_cards_20260802.jpeg` (SHA-256 `77a5cd5e151d09eddc9de864efa0835a958aba7e610066b9600594f3b3eebde7`), `/tmp/mw_phase0b_fact_ui.SiFfQr/edge_completion_gate_20260802.jpeg` (SHA-256 `e3269d449dc4f7cb5d89889686af7a7703d7c2251e243603636f72306e895cb5`), and `/tmp/mw_phase0b_fact_ui.SiFfQr/edge_after_refresh_20260802.jpeg` (SHA-256 `3efd2978cd9e42e99789f4036a60b4e4d8dc4d45dbd751b74f6ec54571d63869`).
- Fixture-side write observation (must not be omitted): because this runtime deliberately copied only five SQLite stores and omitted the triage/preparation/translation stores needed by `_round1_material_ready`, a read-only status request recomputed the persisted soft-terminal projection as not currently provable and appended exactly one `research_pipeline_progress` event. The event was `mwjourney_event_8c759a8520c35d96255f3d77`, stage `awaiting_corpus_admission`, percent `90`, revision `8`; the temp journey row remained revision `8`. Fact-intake conversation/events remained identical (revision 4, 4 events), durable jobs remained 5, and no source clone/r42/v36 row changed. This is a fixture incompleteness effect, not evidence that the real source clone was modified; it also exposes a release residual: a status/read path can persist a projection when dependent evidence stores are unavailable. Do not claim strict zero-write UI acceptance until the complete isolated store set or an explicit fail-closed read-only guard is exercised.
- Superseding verdict: `PASS_FOR_BOUNDED_FACT_TO_FRAMING_UI_CONTRACT; NOT_READY_FOR_PROTOCOL_RELEASE`. No product source was changed in this UI task. The next safe bounded action is to complete the canonical page-hash receipt producer/runtime artifact gate in its own isolated fixture, with the projection side effect retained as an explicit residual for release review.
