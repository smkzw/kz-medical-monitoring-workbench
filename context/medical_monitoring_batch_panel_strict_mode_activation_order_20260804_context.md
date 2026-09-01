# Task Context: medical_monitoring_batch_panel_strict_mode_activation_order_20260804

Created: 2026-08-04 20:46:12
Objective: Ensure the medical-monitoring batch panel activates its project-bound request scope before its first load effect, preventing strict-mode remounts from starting an already-disposed request; preserve all existing cancellation and fail-closed behavior.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/MedicalMonitoringBatchPanel.jsx` — batch workspace effects and request-scope lifecycle.
- `frontend/src/features/medical-monitoring/medicalMonitoringProjectRequestScope.mjs` — `activate`, `dispose`, `begin` and cancellation semantics.
- `tests/test_frontend_monitoring_contract.py` — static contracts for the real user-facing monitoring page.
- Current workbench filesystem and applicable AGENTS files; B6/C14 gates remain closed.

## Scope

- In scope: place the request-scope activation effect before the initial batch-load effect and add a static ordering invariant; preserve the existing mounted guard, `batch-view` cancellation and request semantics.
- Out of scope: API/service, backend storage, B6/C14, source-token/CAS, approved-input, runtime/provider/browser/Playwright/API login, real projects, databases and medical-writing.

## Success Criteria

- The activation effect is declared before the first load effect, so React strict-mode effect replay cannot start loading while the scope is disposed.
- Existing monitoring Node/Python contracts and Vite build pass; no gate or authority state changes.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 20:46:12: Task initialized by `tools/hermes_workflow_guard.py init-task`.
