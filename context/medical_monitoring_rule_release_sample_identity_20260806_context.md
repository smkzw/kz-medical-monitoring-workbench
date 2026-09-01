# Task Context: medical_monitoring_rule_release_sample_identity_20260806

Created: 2026-08-06 07:40:40
Objective: 规则发布影子样本列表保留重复 sample_id 并标记 display identity，补齐离线契约与回归
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringRuleReleaseView.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringRuleRelease.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringRuleReleasePanel.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringRuleReleaseView.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (`read_only` / `blocked`)
- P10 ledger and traceability: `records/active_slices/medical_monitoring_goal_p10_20260730/{LOOP_LEDGER,REQUIREMENTS_TRACEABILITY,TASK_CONTEXT}.md`

## Scope

- In scope: feature-owned shadow-sample normalization/display identity, duplicate sample warning, display-only row key, focused fixture/static contract, offline Node/Python/build verification, task evidence.
- Out of scope: sample deduplication/source repair, actual rule outcome/evidence changes, shadow confirmation/publish behavior, backend/API/schema/database/CAS, provider/service/browser/Playwright/API login, real-project LOOP, B6/C14/P8/source-token/Safety-PV, shared App/styles/main, and medical-writing artifacts.

## Success Criteria

- Duplicate `sample_id` rows remain visible with source order/index and explicit identity warning.
- Sample React keys are namespaced/source-indexed and never replace sample identity in shadow/confirmation payloads.
- Existing sample outcome, evidence, count and confirmation semantics remain unchanged for unique rows.
- Focused/full offline regressions pass; protected shell hashes and stopped-port boundary remain unchanged; review-gate accepts evidence.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 07:40:40: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 07:41:00: Audited rule-release shadow sample normalization/table and found duplicate `sample_id` values were accepted while `ReleaseSamples` used the direct sample ID as React key.
- 2026-08-06 07:41:30: Added source-indexed sample display identity state and `ruleReleaseSampleDisplayKey`; duplicate rows remain visible with “身份待核对” and source-identity note. Shadow outcomes and payload fields are unchanged.
- 2026-08-06 07:42:00: Rule-release-view Node contract passed; monitoring/timeline Python 92 passed; full medical-monitoring Node 38/38 passed; Vite build passed with existing large-chunk advisory.
- 2026-08-06 07:42:30: Ports 8911/5174/8910/4173 confirmed stopped; gate remains `read_only`/`blocked`; protected App/styles/main hashes unchanged.
