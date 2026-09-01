# Task Context: medical_monitoring_daily_ai_candidate_display_identity_20260806

Created: 2026-08-06 06:27:43
Objective: 为日常AI候选卡建立候选与证据项的 display-only 稳定键，避免缺失/重复身份导致列表覆盖并保持待核对语义
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringDailyAiCandidates.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyAiCandidates.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyAiCandidates.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Current real-loop gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (read-only/blocked; no runtime activation)

## Scope

- In scope: retain source indices on normalized daily-AI candidate/evidence rows; add display-only candidate/evidence keys; replace direct candidate/evidence IDs in rendered lists; add partial duplicate/missing-ID regressions/static contract.
- Out of scope: candidate status/confirmation/approval, evidence repair or source retrieval, backend/API schema, shared App shell, runtime/provider/browser/real-project execution, P8 authority, B6/C14 or commercial gate.

## Success Criteria

- Partial candidates/evidence with missing or duplicate IDs remain readable and do not collide in React lists.
- Display keys are namespaced/UI-only and do not replace candidate, evidence, source or risk identity.
- Existing partial/unknown/“不得确认” semantics remain visible; no automation or mutation is added.
- Focused Node, monitoring/timeline Python, full Node and Vite checks pass; protected shared shell hashes remain unchanged; ports stay stopped.

## Risk Boundaries

- Only feature-owned candidate view/model/test and task evidence paths may change; no backend/source data/runtime may be changed or started.
- This is a rendering-key repair, not proof of AI factuality, source validity, clinical correctness or candidate confirmation.
- Codex remains final authority; no delegated provider was used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 06:27: Audited daily AI candidate card; found partial candidate/evidence objects still keyed directly by nullable/duplicate IDs.
- 2026-08-06 06:28-06:30: Added source-index display keys for candidate/evidence rows and partial duplicate/missing-ID regressions/static contract.
- 2026-08-06 06:30-06:33: Focused/full tests, Vite build and stopped-port checks passed.
