# Task Context: medical_monitoring_risk_projection_evidence_rollup_20260802

Created: 2026-08-02 17:01:31
Objective: 补齐项目-中心-受试者风险投影的显式证据覆盖与计数守恒契约，保持前端消费只读且不触碰运行库/B6
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringRiskProjection.mjs` and its Node contract test are the source of truth for the read-only canonical project/site/subject risk projection.
- `frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs` owns the existing rendered-row evidence-shape guard; the projection must remain compatible with the explicit evidence fields already normalized there.
- Current release evidence remains in `records/active_slices/medical_monitoring_goal_p10_20260730/RELEASE_GATE_AUDIT_20260802.md` and the coverage JSON. B6/C14 records and protected `App.jsx`/`styles.css` hashes are read-only boundaries for this slice.

## Scope

- In scope: add a pure, deterministic evidence-coverage summary to project/site/subject rollups; expose explicit locator/reference/linked-view counts and a project site-partition conservation flag; add focused Node assertions and task evidence.
- Out of scope: App.jsx/styles.css changes, API/backend/SQLite/runtime writes, source-token revalidation, B6/C13/C14 activation, risk fact/disposition changes, browser/UAT, real-project execution, provider dispatch, and new inference from titles, counts, or labels.

## Success Criteria

- Every canonical rollup reports evidence coverage from explicit normalized evidence IDs/locators only; no-evidence rows remain visible as missing rather than no-risk.
- Project/site/subject scopes retain deterministic counts; project site partition (site-assigned plus unassigned) is explicitly marked conserved or not conserved.
- Existing medical-monitoring Node suite, focused frontend contract suite, Vite build, release gate and review gate remain green; protected hashes and stopped ports remain unchanged.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 17:01:31: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Direct Codex implementation/review only; no external route dispatched. Initial inspection confirmed the projection already deduplicates by `risk_instance_id`, groups site/subject rows deterministically, and preserves explicit evidence/linked-view arrays, but does not expose cross-layer evidence coverage or site-partition conservation.
