# Task Context: medical_monitoring_protocol_candidate_identity_guard_20260806

Created: 2026-08-06 06:33:04
Objective: 为方案规则准备候选建立缺失/重复 candidate_id 的 fail-closed 决定门，并为主题/候选/原文证据建立 display-only keys
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringProtocolPreparation.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringProtocolPreparationPanel.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringProtocolPreparation.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Current real-loop gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (read-only/blocked; no runtime activation)

## Scope

- In scope: detect duplicate/missing topic and candidate IDs in normalized protocol-preparation payloads; add display-only topic/candidate/evidence keys; prevent candidate accept/reject when candidate identity is missing/duplicate; add offline regressions/static contract.
- Out of scope: backend/API identity repair, source/protocol content changes, decision authorization model, shared App shell, runtime/provider/browser/real-project execution, P8 authority, B6/C14 or commercial gate.

## Success Criteria

- Candidates with missing/duplicate `candidate_id` remain viewable but cannot submit accept/reject and show an explicit blocker.
- Topic/candidate/protocol-evidence rows do not collide in React when identifiers are missing/duplicated.
- Display keys do not become protocol, source, candidate or medical identities.
- Focused Node, monitoring/timeline Python, full Node and Vite checks pass; protected shared shell hashes remain unchanged; ports stay stopped.

## Risk Boundaries

- Only feature-owned protocol-preparation model/view/test and task evidence paths may change; no backend/source data/runtime may be changed or started.
- This is a client-side fail-closed identity guard, not proof of protocol source truth or medical decision correctness.
- Codex remains final authority; no delegated provider was used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 06:33: Audited protocol-preparation candidate actions and evidence blocks; found direct nullable/duplicate ID keys and no candidate-ID decision guard.
- 2026-08-06 06:34-06:37: Added identity-state normalization, display-only keys, decision disable/early-return and explicit blocker copy; added Node/static regressions.
- 2026-08-06 06:37-06:40: Focused/full tests, Vite build and stopped-port checks passed.
