# Task Context: medical_monitoring_risk_lineage_20260802

Created: 2026-08-02 16:15:52
Objective: 在不跨越 B6/C14 权限边界的前提下，为风险清单增加显式来源绑定状态，避免数据敏感医学监查员把来源不完整或混合误读为可比较/完整；完成前端合同、回归与 review-gate
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringRiskChecklist.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringModels.test.mjs`
- Existing frontend risk projection and contract tests under `tests/test_frontend_monitoring_contract.py`, `tests/test_frontend_timeline_contract.py`, `tests/test_frontend_safety_projection_contract.py`, and `tests/test_frontend_unified_risk_workbench_contract.py`.
- Current B6/C14 gates remain read-only inputs; this slice must not change them.

## Scope

- In scope: add a pure, fail-closed summary of explicit risk-row source binding and show its concise status in the risk Checklist; add focused regression cases and run the existing related contracts/build.
- Out of scope: clinical inference, freshness inference, source repair, API/schema/runtime changes, B6/C13/C14/aggregate/CAS/source-token writes, `App.jsx`/`styles.css`, services, browser/runtime startup, real projects, and medical-writing files.

## Success Criteria

- Rows with one explicit source binding are labeled as bound without calling them fresh or clinically valid.
- Mixed source bindings and missing bindings are visibly distinguishable; messages state that they cannot prove completeness/no risk.
- No title, row order, batch number alone, or model output is treated as source proof.
- Existing medical-monitoring Node tests, related frontend Python contracts, Vite build, and Hermes workflow `review-gate` pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not dispatch Hermes or any sub-agent for this small local slice; Codex performs implementation and final review directly.
- Do not change protected shared surfaces `frontend/src/App.jsx` or `frontend/src/styles.css`.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 16:15:52: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 16:16: Reviewed current risk-row projection and Checklist. Implemented `riskEvidenceLineageSummary`/`riskEvidenceLineageMessage`, rendered the status in the Checklist, and added four model assertions. No API/runtime/shared-surface change.
- 2026-08-02 16:17–16:22: Tightened the boundary after review: a batch label alone is now `partial`, never `bound`; reran model tests (**60 passed**), all 22 medical-monitoring Node files, Vite (**1925 modules**), and four related frontend Python contracts (**64 passed**). Hermes was not dispatched; Codex owns direct acceptance.

## Current Result

- Implementation is complete for this slice. The source-binding summary uses only explicit `sourceRevision`, `sourceVersion`, and `sourceBatchId/source_batch_id/batch` fields; only source revision/version can make a row `bound`, while batch-only rows are `partial`. It reports `bound`, `mixed`, `partial`, `unbound`, or `empty`, and never labels freshness or clinical validity.
- Remaining verification: fill the Codex review/metrics records and run Hermes `review-gate --require-verification`; then append a LOOP ledger entry and continue to the next non-B6 slice.
