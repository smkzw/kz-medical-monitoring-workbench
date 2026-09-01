# Task Context: mw_protocol_p0_phase0b_postcorrective_acceptance_20260801

Created: 2026-08-01 23:15 CST
Objective: 在不触碰冻结 r42/r36、医学监查并发线或上游研究链路的前提下，验收 AI-first Protocol prefill 的持久化 executor、单次 transport、证据门与 UI/runtime 合同。
Task type: `clinical_document_router`
Risk: `high`
Goal state: `active`

## Re-anchor

- 重新读取并遵循 `/Users/smkzw/.codex/AGENTS.md`、工作区和 Workbench/Frontend `AGENTS.md`。
- 重新读取 `runs/MW_R42_NO_LOSS_PAUSE_20260731_1609.md`、商业化 gap roadmap/context/independent challenge，以及 Phase 0B fact-handoff records。
- 当前文件系统是最终真相；父 Session 已删除，本记录是证据重建续作，不声称恢复原始逐条对话。
- Approved product route remains Protocol P0 first, Synopsis second, CSR later; AI-first/reviewer-first remains unchanged.

## Source of Truth And Boundaries

- Current source snapshot is the Workbench tree under `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Corrective source files inspected: `services/api/app/medical_writing_authoring_journey.py`, `medical_writing_authoring_prefill*.py`, `main.py`, `ai_gateway.py`, and the medical-writing frontend panels.
- Isolated runtime clone used for this acceptance: `runs/runtime_phase0b_postcorrective_20260801`.
- Target project: `proj_user_cfd2d29284c8` / `艾加莫德α注射液 · 全身型重症肌无力 · III期 · MW-III-B7DF09C0`.
- Frozen artifacts untouched: original r42 runtime, v36 single-item transition stores, candidate-ready/excluded/failed rows, OCR/translation outputs, and medical-monitoring SQLite/WAL/SHM files.
- No formal `完成第一步`/framing commit, corpus admission, public research start, triage, download, OCR, translation, or document generation was invoked.

## Acceptance Contract

1. Same revision/different-key generation has one durable reservation and one provider transport attempt.
2. Dispatched-but-uncommitted outcomes are `unknown_outcome`, fail closed across restart, and require explicit force for a new logical call; force preserves prior attempt lineage.
3. Pending/manual-only/insufficient/unsupported-substantive candidates cannot pass the single-candidate adoption route; composite path remains the explicit override/skip route.
4. Evidence identity is rebuilt from effective draft-wins state and current catalog; tampered/stale bindings fail closed.
5. Browser UI disables pending-like single actions, exposes reviewer-visible fact provenance/gaps, survives service restart, and does not show a runtime contract mismatch after the frontend is rebuilt against the current backend fingerprint.
6. Read-only impact preview can require confirmation without changing revision, event counts, pipeline state, or upstream stores.

## Evidence

- Current focused suite: `625 passed, 17 pre-existing deprecation warnings`.
- Reservation class: `17 passed` in `tests/test_medical_writing_authoring_prefill_ai.py -k GenerationReservationTests`.
- Frontend production build: `npm run build` passed; Vite emitted the current runtime manifest.
- Frontend/runtime manifest: expected backend `api-29ac0d262dd16d6d`, frontend `web-99d342818e803fe4`, contract `medical-writing-api-2026-07-17.1`.
- API restart: isolated service restarted on `127.0.0.1:18905`; `/api/health` and `/api/runtime-readiness` returned healthy/ready.
- Post-restart clone counts: authoring events `3944`, reservations `1`, fact conversations `1`, fact events `4`, durable jobs `5`; journey revision `8`, `stage1_in_progress`, `framing_complete=false`; reservation remains completed with transport attempts `1` and empty `attempt_history`.
- Both authoring and fact SQLite `PRAGMA integrity_check` returned `ok`.
- Real Microsoft Edge Computer Use reselected the target, opened 医学写作, expanded 项目与产品, and recovered the same fact conversation, provenance, high-impact gaps and reviewer controls after restart. Evidence: `runs/runtime_phase0b_postcorrective_20260801/evidence/ui_post_restart_rebuilt_frontend.{txt,jpeg}`.
- Read-only impact preview returned `requires_confirmation=true`, changed field `framing.document_title`, dependents `front_matter` and `protocol_synopsis`, while revision/event counts stayed unchanged. Evidence: `evidence/impact_preview_readonly_after_restart.json`.

## Risk And Next Safe Action

- The current corrective acceptance is ready for independent review; it is not a formal Protocol production or multi-model release pass.
- Keep formal framing and upstream research gates blocked until reviewer-visible missing framing decisions and corpus/impact conditions are independently READY.
- Next safe action: record this acceptance, run the workflow review gate, then continue only with reviewer-visible framing candidates or a separately authorized clone-only runtime action. Do not rerun frozen work or silently confirm a formal commit.

## Corrective Recheck — 2026-08-01 23:32–23:36 CST

The independent challenge previously invalidated the historical READY claim with a runtime fingerprint drift (P1), a force-supersede SELECT/UPDATE race (P2), and an edit-confirmation pending-state leak (P3). The historical evidence above is retained as historical evidence only; it is not used as current acceptance proof.

Current fixes and evidence:

- `services/api/app/medical_writing_authoring_journey.py` now reads and re-keys a terminal reservation under `BEGIN IMMEDIATE`; the UPDATE is a status + null-safe `event_id` CAS and refuses non-terminal rows. A new deterministic regression proves a completed owner row with the same logical call id/event cannot be overwritten by a stale force supersede.
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx` now derives the live editing candidate and disables both edit-confirmation buttons when that candidate becomes pending-like, retaining the server fail-closed contract.
- Reservation class: `18 passed, 81 deselected`.
- Current focused backend/contract suite: `626 passed, 17 pre-existing deprecation warnings`.
- Frontend candidate-panel tests: `11 passed`; production build: passed. The manifest was rebuilt after the latest backend source snapshot and records `expectedBackendBuildId=api-b1908b240f885d8a`, `frontendBuildId=web-02f0a4bfffec7d67`.
- Isolated API on `127.0.0.1:18905` returned `ready=true`, `integrity_check=ok`, and the same `api-b1908b240f885d8a` fingerprint. The isolated Vite runtime on `127.0.0.1:18906` served the same manifest. Evidence: `runs/runtime_phase0b_postcorrective_20260801/evidence/runtime_contract_post_blocker_fix.json`, `runtime_readiness_post_blocker_fix.json`, `runtime_build_post_blocker_fix.json`, and `api_health_post_blocker_fix.json`.
- Real Edge Computer Use re-opened the rebuilt frontend, entered 医学写作 for the target project, and showed the reviewer-first Protocol page with the formal `完成第一步` button still disabled. Evidence: `ui_post_blocker_fix_rebuilt_frontend.txt` and `.jpeg`. API log contained only GETs; no state-changing POST or upstream/model call was made.
- Logical SQLite dumps for all 19 clone stores match `runs/runtime_phase0b_handoff_20260801` exactly; authoring revision/events remain `8/3944`, reservation `1` completed with one transport attempt and empty history, fact intake `1/4`, durable jobs `5`, and integrity checks remain `ok`. No frozen r42/v36 or monitoring store was changed.
- Temporary API/Vite services were stopped cleanly; ports `18905` and `18906` are closed.

Residual boundary:

- The current bounded slice is eligible only for independent post-fix review. It is not formal framing acceptance, public research/corpus admission, Protocol production, Synopsis/CSR, or the later serial multi-model/full-button release gate. `完成第一步`, impact confirmation, competitor rerun, corpus admission, OCR/translation, and document generation remain untouched.

## Independent Post-Fix Review — 2026-08-01 23:40 CST

The same-session independent reviewer completed a read-only post-fix challenge and confirmed:

- P1/P2/P3 are closed in the current snapshot: backend fingerprint `api-b1908b240f885d8a` matches dist, production bundle, saved readiness and served manifest; supersede uses `BEGIN IMMEDIATE` plus terminal status and null-safe `event_id` CAS; the completed-owner regression is present; both edit-confirmation buttons use live pending-state gating and the built bundle contains the change.
- No P0–P3 issue remains for the bounded isolated prefill/runtime slice.
- P4 evidence caveat remains: original raw pytest/build/API request logs were not separately saved for this recheck, and the “editor already open, then candidate becomes pending” transition was not dynamically exercised in the browser. The counts and source/build evidence are recorded and the backend remains fail-closed if the stale UI action is attempted.

Updated bounded verdict: `READY_FOR_POST_FIX_ISOLATED_PREFILL_RUNTIME; NOT_READY_FOR_FORMAL_FRAMING_OR_UPSTREAM_RESEARCH`.
