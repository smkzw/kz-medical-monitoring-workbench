# Task Context: medical_monitoring_risk_history_identity_20260806

Created: 2026-08-06 08:15:47
Objective: 离线审计风险跨批次趋势的 snapshot_id 身份显示，保留重复/缺失历史点但避免来源身份被误读
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringRiskHistoryTrend.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringRiskHistoryTrend.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringRiskHistoryTrend.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
- Current read-only/blocked gate and the source files above; no runtime data source was opened.

## Scope

- In scope: risk cross-batch trend point display/reconciliation identity; retain duplicate or missing `snapshot_id` records while making source ambiguity explicit and collision-safe.
- Out of scope: history deduplication, server/schema/source repair, change of direction/transition calculation, severity/status interpretation, API/backend/database/CAS/B6/C14/P8/source-token/Safety-PV, providers, services, browser/API login, real projects, shared shell/styles/main and medical-writing paths.

## Success Criteria

- Duplicate/missing snapshot identities remain visible and receive `duplicate`/`missing` display state and source-indexed keys.
- Trend rows no longer use direct snapshot identity for React reconciliation; the UI states that an ambiguous point is not singly source-confirmable.
- Focused/full offline contracts and Vite build pass; protected shell hashes remain unchanged and four runtime ports remain stopped.

## Risk Boundaries

- Only the feature-owned risk-history model/view/test/static-contract files and this task's records/context/review/metrics may change; no runtime or data-store write.
- Display metadata and warning copy must not substitute `snapshot_id`, deduplicate history, alter raw severity/status/batch delta, or change direction/transition semantics.
- Do not start 8911, 5174, 8910 or 4173; no provider, browser/Playwright, API login, real project, runtime/SQLite/CAS, B6/C14, P8/source-token, Safety/PV or medical-writing action.
- Codex is final authority; Hermes dispatch was not used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 08:15:47: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Confirmed the history normalizer retained partial/missing snapshot records but did not flag duplicate `snapshot_id` values; the trend strip keyed rows by snapshot identity/index without an explicit source-ambiguity warning.
- 2026-08-06: Added source-indexed display identity state/key and duplicate issue evidence. The trend strip uses the display key and labels ambiguous points; raw history and direction calculation remain unchanged.
- 2026-08-06: Risk-history Node **23** passed; focused monitoring/timeline Python **97** passed; all 38 monitoring Node files passed; Vite build passed (1,956 modules; existing >500 kB advisory); runtime ports stopped; `review-gate --require-verification` returned `ok=true` with no warnings/errors.
