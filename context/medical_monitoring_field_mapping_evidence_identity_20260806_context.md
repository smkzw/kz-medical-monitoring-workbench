# Task Context: medical_monitoring_field_mapping_evidence_identity_20260806

Created: 2026-08-06 06:17:25
Objective: 为字段映射原始画像依据建立显示键与缺失身份 fail-closed 提示，避免证据项 key 碰撞和空定位误读
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringFieldMappingView.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringFieldMappingPanel.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringFieldMappingView.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Current real-loop gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (read-only/blocked; no runtime activation)

## Scope

- In scope: retain a source index for normalized evidence-summary rows; provide a deterministic display-only evidence key; render explicit missing locator/identity states in the field-mapping evidence panel; add offline regressions/static contract.
- Out of scope: backend/API schema, evidence repair, source truth or medical interpretation, mapping confirmation semantics, shared App shell, runtime/provider/browser/real-project execution, P8 authority, B6/C14 or commercial gate.

## Success Criteria

- Multiple evidence rows without `evidence_id` no longer share a React key.
- Empty locator/identity is visibly `来源定位待核对` / `来源证据身份缺失；不可据此确认映射` instead of blank evidence-looking text.
- Display key never becomes an evidence, clinical or server identity.
- Focused Node, monitoring/timeline Python, full Node and Vite checks pass; protected shared shell hashes remain unchanged; ports stay stopped.

## Risk Boundaries

- Only feature-owned source/tests and task evidence paths may change; no production data or runtime may start.
- This slice does not promote incomplete evidence to a mapping or medical conclusion.
- Codex remains final authority; no delegated provider was used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 06:17:25: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 06:17: Audited field-mapping evidence rendering; found optional evidence identity plus `key={item.evidence_id}` collision/blank-locator risk.
- 2026-08-06 06:18-06:20: Added source-index evidence key and explicit missing identity/locator copy; added Node/static regressions.
- 2026-08-06 06:20-06:22: Focused/full tests and Vite build passed; initial build cwd error was corrected by running from `frontend/`; ports stayed stopped.
