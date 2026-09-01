# Task Context: medical_monitoring_scope_category_labels_20260803

Created: 2026-08-03 21:49:19
Objective: Map explicit risk-category codes to the already fetched project taxonomy labels in the read-only scope summary, preserving code traceability and fail-closed fallback
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx` risk-taxonomy fetch and project-identity guard.
- `frontend/src/features/medical-monitoring/MedicalMonitoringScopeSummary.jsx`, `.css`, `medicalMonitoringScopeSummary.mjs`, and focused test.
- `services/api/app/medical_monitoring_risk_taxonomy.py::risk_taxonomy_payload` and `services/api/app/medical_monitoring_summary.py::_risk_rollup` (read-only contract sources).
- Current release gate re-anchor and B6/C14/CAS status in `records/active_slices/medical_monitoring_release_gate_reanchor_20260803/REANCHOR.json`.

## Scope

- In scope: accept the already project-identity-validated taxonomy as an optional read-only prop, map exact category codes to explicit taxonomy labels for display, keep the original code in the title/accessible text, and fall back to the code when a label is missing.
- Out of scope: taxonomy edits, category reclassification, API changes, writes, disposition actions, B6/C14/CAS/source-token work, service/browser/runtime startup, project imports, Playwright or external tester dispatch.

## Success Criteria

- Official labels are used only for exact code matches in the supplied taxonomy; unknown/malformed entries remain source codes and visible warnings are not suppressed.
- The category bars remain compact and traceable (label plus code in title/accessible text), with no new decision control.
- Focused model/UI static checks, full medical-monitoring Node regression, correct-directory Vite build, and empty-port check pass.
- No release-gate state or backend source changes.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 21:49:19: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 21:49:xx: Re-anchored taxonomy source and selected exact-match display mapping; Codex will implement directly without dispatch.
