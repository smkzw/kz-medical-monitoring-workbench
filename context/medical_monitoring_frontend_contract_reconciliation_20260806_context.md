# Task Context: medical_monitoring_frontend_contract_reconciliation_20260806

Created: 2026-08-06 00:23:52
Objective: reconcile current medical-monitoring evidence/subject-route implementation with adjacent frontend contracts without changing medical facts, runtime gate, or medical-writing surface
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` P1-03/P1-04 evidence and route requirements.
- `frontend/src/App.jsx` current `riskSourceGroups`, `RiskEvidenceSequence`,
  `RiskSourceReference`, `RiskEvidenceDock`, and active monitoring route binding.
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
  and `medicalMonitoringSubjectModels.mjs` current Timeline/Profile route contract.
- `tests/test_frontend_monitoring_contract.py`,
  `tests/test_frontend_timeline_contract.py`, and
  `tests/test_frontend_unified_risk_workbench_contract.py` as adjacent static
  acceptance contracts; the four current failures are the observation to
  reconcile, not authority to invent medical behavior.
- `CURRENT_REAL_LOOP_GATE_AUDIT.json` and prior P10/v11 records for the
  runtime boundary. No production path, runtime database, or real project will
  be activated in this slice.

## Scope

- In scope: make the current risk evidence presentation expose its existing
  source-group/locator semantics consistently, keep source fragment context
  visibly risk-bound and traceable, and make the active monitoring route
  binding explicit enough for the Timeline/Profile catalog contract. Update or
  add focused static contracts only when they represent the current intended
  behavior; preserve source authority and the new route scroll state.
- Out of scope: medical facts, backend/API/schema, source capture, risk
  identity, dispositions, runtime SQLite, service/browser/provider/API login,
  real projects/LOOP, B6/C14, external model execution, medical-writing code,
  broad App.jsx extraction, or visual redesign beyond the source-traceability
  labels required by the existing contract.

## Success Criteria

- Risk evidence has one explicit grouping path and retains fixed order
  `原始事实 → 方案依据 → 系统规则/计算 → 来源定位`.
- Source fragment context visibly identifies the associated risk and source
  lineage; only valid source locators remain actionable.
- Monitoring route project identity is explicit and subject catalog handoff
  remains project-bound; no demo fallback or stale-project response is allowed.
- The four currently failing static tests either pass after the focused code
  fix or are revised narrowly with a documented reason when the assertion is
  stale; pure frontend tests and Vite build remain green.
- The runtime gate and medical-writing surface remain untouched and blocked.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not start 8911, 5174, 8910, or 4173; do not run browser/Playwright,
  providers, API login, real project data, or real LOOP while B6/C14 is blocked.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 00:23:52: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 00:24:10: Four adjacent Python static failures were reproduced.
  Three are source-shape assertions around the current extracted evidence
  sequence/route-binding architecture; one exposes a missing explicit
  `溯源：` label and the source-view class marker. The next action is a bounded
  source/UI reconciliation, not a runtime or medical change.
- 2026-08-06 00:27:26: Added explicit source-group handoff, bound-fragment count,
  fail-closed empty-source copy, source fragment `关联风险`/`溯源` context,
  source-view group marker, and explicit manifest route-project binding. The
  four static failures became 4 passed; adjacent frontend/monitoring contracts
  are 164 passed; medical-monitoring Node suite is 35 files passed; Vite build
  passed. Medical-writing protection sample remains 197 passed / 2 existing
  translation-batch failures outside changed files.
- 2026-08-06 00:27:26: Review-gate passed with no warnings. Runtime gate remains
  `read_only / blocked`; no service, browser, provider, API login, real project,
  B6/C14 or medical-writing action occurred. Next safe action remains formal
  B6 outcomes → source-token/CAS revalidation before runtime activation.
