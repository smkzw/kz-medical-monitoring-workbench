# Task Context: medical_monitoring_assurance_panel_activation_order_20260804

Created: 2026-08-04 20:49:10
Objective: Ensure the medical-monitoring assurance panel activates its project-bound request scope before task loading/detail effects, preventing strict-mode remounts from starting disposed requests while preserving fail-closed task and evidence behavior.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/MedicalMonitoringAssurancePanel.jsx` — assurance task/detail/audit request effects.
- `frontend/src/features/medical-monitoring/medicalMonitoringProjectRequestScope.mjs` — project-bound activation/disposal semantics.
- `tests/test_frontend_monitoring_contract.py` — assurance and source contracts.
- Current workbench filesystem and applicable AGENTS files; B6/C14 and runtime gates remain closed.

## Scope

- In scope: move the existing request-scope activation effect before assurance task loading/detail effects and add a static ordering invariant; preserve all cancellation, principal checks and fail-closed evidence behavior.
- Out of scope: API/service/storage, B6/C14, source-token/CAS, approved-input, runtime/provider/browser/Playwright/API login, real projects, databases and medical-writing.

## Success Criteria

- The assurance panel activates its project request scope before any open-state load can begin.
- Existing monitoring Node/Python contracts and Vite build pass; no gate or authority state changes.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 20:49:10: Task initialized by `tools/hermes_workflow_guard.py init-task`.
