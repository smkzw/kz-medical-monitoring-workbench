# Task Context: medical_monitoring_remove_demo_risk_fallback_20260804

Created: 2026-08-04 21:07:48
Objective: Remove the remaining MG-K10 demo risk fallback from the shared medical-monitoring subject view path so all projects require project-bound monitoring data.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx` — root monitoring subject-view construction and project selection.
- `frontend/src/features/medical-monitoring/medicalMonitoringFixtures.mjs` — demo fixtures that must not feed the shared real-project risk path.
- `tests/test_frontend_monitoring_contract.py` — project-neutrality source contract.
- Current workbench filesystem and applicable global/workbench `AGENTS.md` files.
- B6/C14/approved-input/host-attestation/runtime/provider/browser/real-project gates remain closed; ports 8911, 5174, 8910 and 4173 must remain empty.

## Scope

- In scope: remove the remaining `demoRiskRows` fallback from the shared subject-view path and strengthen the source contract so a real project cannot inherit an MG-K10 demo risk.
- Out of scope: removing compatibility-only demo subject fixtures, API/service/storage changes, B6/C14, runtime/provider/browser/Playwright/API login, real projects, databases and medical-writing.

## Success Criteria

- No `demoRiskRows` import or fallback remains in `App.jsx`.
- A subject view without a project-bound profile/risk remains an explicit not-loaded state rather than a demo risk.
- Focused/adjacent static contracts, all monitoring Node contracts and the Vite build pass; gates and ports remain unchanged.

## Finding And Decision

The active root page still passed an MG-K10-only `demoRiskRows.find(...)` result into `buildSubjectView` before rendering any monitoring subject page. This could make a missing real response appear as a populated risk for only one project. The smallest coherent correction is to pass no fallback risk; the existing fetched `subjectProfile` and `monitoringSubjectCatalog` remain the only project-bound inputs.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 21:07:48: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 21:07–21:10: Removed the root demo-risk fallback and tightened the project-neutrality contract; focused/adjacent contracts passed.
- 2026-08-04 21:10: Re-ran all 32 medical-monitoring Node contracts, the Vite build and required-port checks; all passed.
