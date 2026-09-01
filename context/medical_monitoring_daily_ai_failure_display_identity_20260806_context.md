# Task Context: medical_monitoring_daily_ai_failure_display_identity_20260806

Created: 2026-08-06 06:40:07
Objective: 为日常AI失败账本建立重复 job_id 的显式告警与 display-only failure key，避免失败证据行覆盖
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringDailyAiEvidence.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyAiEvidence.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyAiEvidence.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Current real-loop gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (read-only/blocked; no runtime activation)

## Scope

- In scope: retain failure-row source index; detect duplicate failure `job_id`; add display-only failure key; preserve all explicit failure rows and current no-retry semantics; add offline regressions/static contract.
- Out of scope: failure-count policy changes, retry/recovery actions, backend/API schema, shared App shell, runtime/provider/browser/real-project execution, P8 authority, B6/C14 or commercial gate.

## Success Criteria

- Duplicate `job_id` failure rows remain visible with an explicit partial issue and unique display keys.
- Failure count and detail mismatch behavior remains fail-closed; no failure is deduplicated away or converted to zero.
- Display key is UI-only and does not imply retryability or job identity repair.
- Focused Node, monitoring/timeline Python, full Node and Vite checks pass; protected shared shell hashes remain unchanged; ports stay stopped.

## Risk Boundaries

- Only feature-owned AI evidence view/model/test and task evidence paths may change; no backend/source data/runtime may be changed or started.
- This is a display/accounting guard, not a retry decision, failure remediation or clinical conclusion.
- Codex remains final authority; no delegated provider was used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 06:40: Audited failure evidence rows; found direct `key={failure.jobId}` with no duplicate-job guard.
- 2026-08-06 06:41-06:43: Added duplicate warning, source index and display-only failure key; added Node/static regression.
- 2026-08-06 06:43-06:46: Focused/full tests, Vite build and stopped-port checks passed.
