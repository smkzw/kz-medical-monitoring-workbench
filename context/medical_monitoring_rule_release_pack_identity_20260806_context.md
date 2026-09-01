# Task Context: medical_monitoring_rule_release_pack_identity_20260806

Created: 2026-08-06 07:43:51
Objective: 规则发布规则包列表保留重复 rule_pack_id 并阻断歧义选择，补齐 display identity contract 与离线回归
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringRuleRelease.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringRuleReleasePanel.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringRuleRelease.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (`read_only` / `blocked`)
- P10 ledger and traceability: `records/active_slices/medical_monitoring_goal_p10_20260730/{LOOP_LEDGER,REQUIREMENTS_TRACEABILITY,TASK_CONTEXT}.md`

## Scope

- In scope: feature-owned rule-pack list normalization, duplicate pack identity state/display key, read-only picker guard and unique-default selection, focused fixture/static contract, offline Node/Python/build verification, task evidence.
- Out of scope: rule-pack deduplication/source repair, rule content or release status changes, backend/API/schema/database/CAS, shadow/confirm/publish actions, provider/service/browser/Playwright/API login, real-project LOOP, B6/C14/P8/source-token/Safety-PV, shared App/styles/main, and medical-writing artifacts.

## Success Criteria

- Duplicate `rule_pack_id` rows remain visible and explicitly marked; they are not silently collapsed by the picker map.
- Default/focus selection only accepts a unique ready pack; ambiguous options are disabled/read-only.
- Display keys are namespaced/source-indexed and never become pack identity in API payloads.
- Existing unique-pack ordering and lifecycle behavior remain unchanged; offline regressions pass and review-gate accepts evidence.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 07:43:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 07:44:00: Audited rule-pack list/picker and found `pickerPacks` merged by `Map(rulePackId)` while sorted packs lacked duplicate identity state.
- 2026-08-06 07:44:30: Added source-indexed pack identity state/display key; duplicate options remain visible but disabled, default/focus selection only chooses ready packs, and unique-pack deduplication behavior is preserved.
- 2026-08-06 07:45:00: Rule-release model Node 67 assertions passed; monitoring/timeline Python 93 passed; full medical-monitoring Node 38/38 passed; Vite build passed with existing large-chunk advisory.
- 2026-08-06 07:45:30: Ports 8911/5174/8910/4173 confirmed stopped; gate remains `read_only`/`blocked`; protected App/styles/main hashes unchanged.
