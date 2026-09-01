# Task Context: medical_monitoring_ai_candidate_confirmation_semantics_20260806

Created: 2026-08-06 05:44:01
Objective: 在只读 AI 候选预览中区分“医学经理确认/采纳”与“组织审批”：已采纳、已驳回、已替代的候选不得继续显示待确认；提议候选仍保持 fail-closed 的医学确认提示。
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

PRD P0-06 要求医学经理确认候选后，该项在当前监查中成为已确认结论；只有需要正式 Query/Finding 或其他角色批准的事项才进入组织流程。当前 `MedicalMonitoringDailyAiCandidates` 的元信息无论候选状态如何都显示“需医学确认”，会让已采纳/已驳回/已替代状态重新回到待确认语义，造成用户误读。

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` §2.3、P0-06。
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyAiCandidates.mjs`：候选状态和置信度归一化。
- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyAiCandidates.jsx`：只读候选卡展示。
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyAiCandidates.test.mjs` 与 `tests/test_frontend_monitoring_contract.py`：现有回归契约。
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`：真实 LOOP gate 当前 `read_only / blocked`。

## Scope

- In scope: add a deterministic status-aware review-state label helper; use it in the candidate card; add focused unit/static assertions and durable evidence.
- Out of scope: adding accept/reject/confirm buttons, API calls, actor fields, backend/schema/database changes, P8 authority, B6/C14, runtime/provider/browser/Playwright/API login, real projects, Safety/PV, medical-writing, or shared `App.jsx`/styles changes.

## Success Criteria

- `accepted` renders as an already confirmed/adopted monitoring conclusion, not pending confirmation or organization approval.
- `rejected` and `superseded` render terminal state wording that does not invite repeat confirmation.
- `proposed` remains “需医学确认” or “需补证据” according to the explicit confidence flags; malformed/unknown status remains “状态待核对”.
- No new action authority is introduced; the card stays read-only.
- Focused Node/static contracts and the full medical-monitoring Node suite pass; protected shared files and ports remain unchanged/stopped.

## Risk Boundaries

- Do not change candidate status transitions or backend truth; this is presentation/normalization only.
- Do not relabel an accepted candidate as organization-approved; use “医学已确认/已采纳” and keep external approval separate.
- Keep 8911/5174/8910/4173 stopped. Do not call services, providers, browsers, API login, real projects, SQLite/CAS, source-token, B6/C14 or release gates.
- No medical-writing or shared shell source changes.

## Timeout Policy

- Direct Codex only; no delegated agent or external provider is required for this bounded feature-owned contract.
- A malformed candidate must remain visibly non-confirmable; tests must cover missing/unknown status as well as terminal states.

## Loop Log

- 2026-08-06 05:44:01: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 05:44:xx: Re-read current P0/P1 matrix and candidate card source; found the unconditional “需医学确认” meta label independent of `candidate.status`.
- 2026-08-06 05:5x: Added a deterministic review-state helper and read-only card rendering. Terminal states now explain their current meaning; only proposed candidates remain confirmation/evidence gated. Added focused Node and Python static assertions; no actions or API calls were added.
- 2026-08-06 05:5x: Focused candidate contract, frontend static contracts, full medical-monitoring Node suite, Vite build and listener checks passed; existing large-chunk advisory remains unchanged.
