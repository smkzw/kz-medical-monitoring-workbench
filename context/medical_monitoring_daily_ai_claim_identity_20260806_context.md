# Task Context: medical_monitoring_daily_ai_claim_identity_20260806

Created: 2026-08-06 07:28:37
Objective: 补齐每日 AI 候选声明列表的缺失/重复 claim_id 身份防护与显示键契约，保持只读展示并完成离线验证
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringDailyAiCandidates.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyAiCandidates.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyAiCandidates.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (`read_only` / `blocked`)
- P10 ledger and traceability: `records/active_slices/medical_monitoring_goal_p10_20260730/{LOOP_LEDGER,REQUIREMENTS_TRACEABILITY,TASK_CONTEXT}.md`

## Scope

- In scope: feature-owned AI candidate claim normalization, display-only identity key, read-only anomaly copy, focused fixtures/static contract, offline Node/Python/build verification, task evidence.
- Out of scope: backend/API/schema/database/CAS, source repair or deduplication, candidate adoption/rejection, medical interpretation, provider/service/browser/Playwright/API login, real-project LOOP, B6/C14/P8/source-token/Safety-PV, shared App/styles/main, and medical-writing artifacts.

## Success Criteria

- Every claim remains visible in source order; missing/duplicate `claim_id` is explicitly marked and creates a review issue.
- Claim React keys are namespaced and source-indexed for display only; no direct `key={claim.claimId}` remains.
- No claim-level selection or automation is introduced; candidate card remains read-only and source-bound.
- Focused and full offline regressions pass; protected shell hashes and stopped-port boundary remain unchanged; review-gate accepts evidence.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 07:28:37: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 07:29:00: Audited candidate model/view and found direct `key={claim.claimId}` without missing/duplicate claim identity state.
- 2026-08-06 07:29:30: Added source-indexed claim normalization, duplicate/missing fail-closed issue state, display-only `medicalMonitoringAiCandidateClaimKey`, and read-only “身份待核对” copy; no claim action or payload changed.
- 2026-08-06 07:30:00: Focused claim Node test passed; full monitoring/timeline Python and all medical-monitoring Node tests passed; Vite build passed with existing large-chunk advisory.
- 2026-08-06 07:31:30: Ports 8911/5174/8910/4173 confirmed stopped; gate remains `read_only`/`blocked`; protected App/styles/main hashes unchanged.
