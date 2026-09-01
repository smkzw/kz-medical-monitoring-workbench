# Task Context: mw_protocol_p0_phase0b_fact_handoff_20260801

Created: 2026-08-01 22:37:33
Objective: 隔离验证事实采集到正式框架交接；证明提案采用可持久化、幂等且不触发上游检索或改写冻结数据
Task type: `clinical_document_router`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Global operating contract: `/Users/smkzw/.codex/AGENTS.md`.
- Workspace/workbench contracts: `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md` and `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/AGENTS.md`.
- Approved route and no-loss boundary: `runs/MW_R42_NO_LOSS_PAUSE_20260731_1609.md`, `plans/mw_commercial_writing_gap_and_roadmap_20260731.md`, `context/mw_commercial_writing_gap_20260731_context.md`, `reviews/mw_commercial_writing_gap_20260731_independent_challenge.md`, and `runs/MW_PROTOCOL_P0_PHASE0B_RUNTIME_DRAFT_WORD_NO_LOSS_PAUSE_20260801_2218.md`.
- Product contracts inspected: `services/api/app/medical_writing_fact_intake.py`, `services/api/app/medical_writing_authoring_journey.py`, `services/api/app/main.py`, `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`, `packages/contracts/workbench_contracts/models.py`.
- Isolated runtime: `runs/runtime_phase0b_handoff_20260801`; source code was not edited. Target project: `proj_user_cfd2d29284c8` / `艾加莫德α注射液 · 全身型重症肌无力 · III期 · MW-III-B7DF09C0`.
- Runtime evidence: `runs/runtime_phase0b_handoff_20260801/evidence/` (SQLite backup/hash evidence and real Computer Use screenshots/AX captures).

## Scope

- In scope: one isolated fact-intake conversation; one independent-AI turn; reviewer adoption of a non-quantitative fact and a low-confidence technology-type candidate; save/reload of a framing draft; deterministic idempotency/optimistic-revision tests; impact-isolation audit.
- Out of scope: r42/r36 upstream rows, candidate-ready/excluded items, downloads, triage, OCR, translation, attempt 2/3, formal framing commit, PICOS/corpus gate, document generation, Word export, Synopsis/CSR, and multi-model release testing.

## Success Criteria

- Real UI evidence shows the AI separates user-stated, inferred, unknown and conflicting facts and preserves high-impact gaps.
- Only the isolated runtime changes: fact-intake conversation/events and one framing draft; formal journey remains incomplete.
- Repeated request/restart does not create extra fact-intake conversations, AI turns, journey events, durable jobs, or provider calls.
- Draft save is idempotent/auditable and records `downstream_invalidated=false` with `competitor_search_plan=preserved`; no research-pipeline POST occurs.
- Source clone SQLite integrity and pre-existing project/reference rows remain unchanged; no product source edits.
- Focused deterministic, API, frontend-contract and authoring-journey tests pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Never click `完成第一步` or confirm an impact preview in this slice: `commitPayload` invokes `runPublicSearch` after a completed framing commit. Keep the formal framing gate and upstream research route untouched.
- The entered facts are explicitly runtime-test assumptions, not medical facts for a production protocol.
- Do not touch the concurrent medical-monitoring task or its SQLite/WAL/SHM files.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Current Evidence And Decision

- The isolated AI route completed one turn through the real UI using `alibaba_token_plan / qwen3.8-max-preview`; it returned 31 proposals, 8 high-impact gaps and 3 prioritized questions. The UI displayed explicit provenance and pending adopt/edit/reject controls.
- Adopted `p05_technology_description` then `p06_technology_type` through real Computer Use clicks. The fact-intake database has one conversation, four events (create, AI turn, two apply events), revision 4; confirmed values are persisted in the conversation layer only.
- Saved framing draft through the UI. Journey moved from revision 7 to 8, remains `stage1_in_progress`/`framing_complete=false`, with missing `design_pattern`, `population_intent`, `intrinsic_objectives`. Event payload states `competitor_search_plan=preserved`, `downstream_invalidated=false`, `completion_state_unchanged=true`.
- After API restart, GET and browser reload recovered the same conversation/draft. Counts stayed: fact conversations 1, fact events 4, authoring journeys 1, authoring events 3944, durable jobs 5. Research pipeline stayed `awaiting_corpus_admission` at 90%; retry/resume idempotency keys remained empty.
- No `/research-pipeline/start`, triage, download, OCR, translation or formal stage-commit request occurred in the API log for this slice.
- A non-mutating impact-preview request against the persisted framing draft returned `requires_confirmation=true`, two changed fields and affected dependents `corpus_coverage`, `intervention_sections`, `safety_assessments`, `trial_rationale`; journey revision/event counts and pipeline state remained unchanged. This confirms formal commit is a material boundary and must not be clicked in this slice.
- The frontend Vite terminal showed HMR updates to several medical-writing files from a concurrent workspace process while the isolated runtime was open. Codex did not edit product source; the next resume must re-check the current source and applicable AGENTS before relying on static line numbers.

## Downstream-Only Transition Design

- The safe transition for this slice is the existing `save_stage_draft` contract, not formal `commit_stage`: accept a fact-intake revision plus reviewer decisions, persist only `framing_draft`, bump the authoring revision once, write one idempotency-keyed audit event, preserve the existing search plan, and return missing fields without promoting formal framing.
- The contract must reject stale revisions and idempotency-key payload reuse with different content; replay must return the original draft response. It must not call `runPublicSearch`, mutate corpus/Protocol/Word state, or silently resolve unresolved high-impact facts.
- The runtime event and focused authoring-journey tests already satisfy this contract (`competitor_search_plan=preserved`, `downstream_invalidated=false`, `completion_state_unchanged=true`). Therefore no product source change is justified now; the formal commit remains a separate, explicitly confirmed gate.

## Loop Log

- 2026-08-01 22:37:33: Initialized tracked task via `hermes_workflow_guard.py init-task`.
- 22:24–22:32: Fresh isolated services and real Computer Use fact-intake turn; one hard wait was required for the independent provider.
- 22:32: Adopted description; 22:34 adopted technology-type candidate; 22:35 saved framing draft.
- 22:37–22:39: Stopped/restarted API, reloaded UI, reselected target project and verified persisted draft and unchanged upstream state.
- 22:39: Deterministic/unit/API/frontend/authoring-journey checks complete; no source change justified.

## Next Safe Action

Keep formal framing commit blocked. The downstream-only draft transition is proven in deterministic tests and the isolated runtime; next resume should address the remaining framing decisions through reviewer-visible AI candidates, without confirming the formal stage. Do not start upstream research or document generation until the corpus gate and an explicit commit decision are independently READY.

## Corrective Continuation — 2026-08-01 23:15 CST

The model-change re-anchor and post-conference corrective acceptance are recorded in `context/mw_protocol_p0_phase0b_postcorrective_acceptance_20260801_context.md`, `runs/codex_mw_protocol_p0_phase0b_postcorrective_acceptance_20260801.md`, `reviews/codex_mw_protocol_p0_phase0b_postcorrective_acceptance_20260801_review.md`, and `metrics/mw_protocol_p0_phase0b_postcorrective_acceptance_20260801_metrics.md`.

- Current source, not worker-reported hashes, was inspected. The durable reservation schema is v2; dispatched non-commit outcomes fail closed as `unknown_outcome`; prefill transport is limited to one attempt; pending/manual-only/insufficient/unsupported-substantive single adoption is blocked.
- Current focused tests are `625 passed` (17 pre-existing deprecation warnings); the dedicated reservation class is `17 passed`.
- Fresh clone `runs/runtime_phase0b_postcorrective_20260801` survived API restart and rebuilt-frontend reload. Counts remained authoring events 3944, reservation rows 1, fact conversations 1, fact events 4, durable jobs 5; journey revision remained 8 and formal framing incomplete.
- `/api/runtime-readiness` is `ready`; Vite production build passed and its runtime manifest matches the current backend fingerprint. Real Computer Use recovered the reviewer-visible fact conversation and high-impact gaps after restart.
- A read-only impact preview required confirmation and changed no SQLite state. Formal `完成第一步`, impact confirmation, public research, corpus admission, OCR/translation and document generation remain intentionally untouched.

The corrective slice is ready for independent review, but formal framing and upstream research remain blocked. Goal stays active.
