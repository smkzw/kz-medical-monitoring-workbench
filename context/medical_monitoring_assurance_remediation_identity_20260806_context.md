# Task Context: medical_monitoring_assurance_remediation_identity_20260806

Created: 2026-08-06 07:35:40
Objective: 保障整改矩阵保留重复 risk_instance_id 行并阻断歧义聚焦，补齐 display identity contract 与离线验证
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringAssuranceRemediation.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringAssuranceRemediation.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringAssuranceRemediation.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (`read_only` / `blocked`)
- P10 ledger and traceability: `records/active_slices/medical_monitoring_goal_p10_20260730/{LOOP_LEDGER,REQUIREMENTS_TRACEABILITY,TASK_CONTEXT}.md`

## Scope

- In scope: feature-owned assurance-remediation matrix normalization, duplicate-ID display key/identity state, read-only focus guard, focused fixture/static contract, offline Node/Python/build verification, task evidence.
- Out of scope: backend/API/schema/database/CAS, risk deduplication or source repair, risk status/closure judgment, focus target resolution, provider/service/browser/Playwright/API login, real-project LOOP, B6/C14/P8/source-token/Safety-PV, shared App/styles/main, and medical-writing artifacts.

## Success Criteria

- Duplicate risk rows are retained and explicitly marked rather than silently dropped.
- Ambiguous rows remain visible but cannot focus a subject/site; unique rows preserve existing focus behavior.
- React display keys are namespaced/source-indexed and never replace risk identity in payloads or callbacks.
- Focused/full offline regressions pass; protected shell hashes and stopped-port boundary remain unchanged; review-gate accepts evidence.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 07:35:40: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 07:36:00: Audited remediation normalization/view and found duplicate `risk_instance_id` rows returned early while the view keyed rows directly by risk ID.
- 2026-08-06 07:36:30: Retained duplicate rows with source indices and `ready`/`duplicate` state; added display-only `assuranceRemediationDisplayKey`; ambiguous focus button is disabled/guarded with explicit copy. Unique rows remain unchanged.
- 2026-08-06 07:37:00: Remediation Node contract passed; monitoring/timeline Python 91 passed; full medical-monitoring Node 38/38 passed; Vite build passed with existing large-chunk advisory.
- 2026-08-06 07:37:30: Ports 8911/5174/8910/4173 confirmed stopped; gate remains `read_only`/`blocked`; protected App/styles/main hashes unchanged.
