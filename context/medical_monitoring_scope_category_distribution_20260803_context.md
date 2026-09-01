# Task Context: medical_monitoring_scope_category_distribution_20260803

Created: 2026-08-03 21:45:09
Objective: Expose the existing explicit project risk category distribution in the compact scope summary with visible labels, preserving read-only evidence boundaries
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringScopeSummary.mjs` and its focused test.
- `frontend/src/features/medical-monitoring/MedicalMonitoringScopeSummary.jsx` and `.css`.
- `services/api/app/medical_monitoring_summary.py::_risk_rollup` (read-only contract source for `category_counts`).
- Current release re-anchor: `records/active_slices/medical_monitoring_release_gate_reanchor_20260803/REANCHOR.json`.
- The backend already emits explicit trial-level `category_counts`; the normalized frontend model already preserves it but the card does not render it.

## Scope

- In scope: render the existing explicit project-level risk-category distribution with a visible group label; add a focused model assertion for category ordering and keep the surface read-only.
- Out of scope: B6/C14 activation, CAS/source-token repair, risk writes or disposition actions, API contract changes, project data imports, server/browser startup, real-project runs, and external tester dispatch.

## Success Criteria

- Category counts are visible only when supplied by the explicit rollup; missing/invalid values remain absent or blocked by the existing normalizer.
- Severity, category, and batch-delta groups are visually distinguishable without adding controls or inferred labels.
- Focused model test, full medical-monitoring Node regression, correct-directory Vite build, and empty-port check pass.
- No B6/C14/CAS/runtime evidence or source files are modified.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 21:45:09: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 21:46:xx: Re-anchored from current filesystem; confirmed `categoryCounts` is already normalized and supplied by the backend trial rollup but unused in the card. Selected a small read-only visibility slice.
