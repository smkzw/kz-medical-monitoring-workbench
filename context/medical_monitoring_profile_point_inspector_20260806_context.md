# Task Context: medical_monitoring_profile_point_inspector_20260806

Created: 2026-08-06 05:17:03
Objective: Restore Patient Profile trend-point click-through to raw value, source text, reference range, CS/NCS and risk context without opening runtime gates
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md:69-83` and
  `docs/medical_monitoring_manual/医学监查子系统说明书.md:1707-1763` are the local
  Patient Profile contract: a trend point must expose raw value, visit/date,
  reference range, CS/NCS, source body and associated risk before locator detail.
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
  is the production Patient Profile/TrendSparkline surface.
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
  remains the source-bound read model for explicit source locators, metric
  points, risk IDs and shape warnings.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
  is the runtime authority boundary: `read_only / blocked`, with provider,
  runtime and write flags false.

## Scope

- In scope: the Patient Profile trend-point interaction, its local styles,
  static frontend contract, derived build output and this task's evidence
  records.
- Out of scope: backend/API contracts, source ingestion, risk semantics,
  medical confirmation, P8/B6/C14, Safety/PV, App ownership migration,
  medical-writing assets, providers, services, browser/Playwright sessions,
  real projects, runtime/SQLite/CAS writes and ports.

## Success Criteria

- A user can click or keyboard-focus a plotted trend point (and its retained
  detail row) and see an explicit raw value, visit/date, reference range,
  CS/NCS, value status, source body, source locator and risk-ID state.
- Missing source body/locator/risk IDs remain visibly `未提供`/unbound and are
  never converted into a no-risk or source-validity conclusion.
- First-screen density stays compact: the inspector is closed until a point
  is selected, and the chart/list remains usable for sparse and invalid data.
- Focused tests, full medical-monitoring Node tests, static frontend contract,
  production build and reserved-port checks pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This is direct Codex work; no delegated agent or provider session is used.
- No live runtime/browser validation is claimed while the current real-loop
  gate remains `read_only / blocked`.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 05:17:03: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Local PRD/manual review identified that hover-only SVG titles did
  not satisfy the required click-through raw-fact contract.
- 2026-08-06: Added keyboard/click selection and a compact explicit-fact
  inspector; no server or medical semantics changed.
- 2026-08-06: Focused/full frontend tests and build passed; ports remain stopped.
