# Task Context: medical_monitoring_overview_pending_counts_20260804

Created: 2026-08-04 22:08:59
Objective: Prevent project-overview risk counts from showing initialization or missing data as numeric zero; require project-identity readiness and preserve all runtime authority gates.
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

The preceding risk-snapshot guard exposed the same data-sensitive failure mode
in the project overview: the initial dashboard object has no confirmed project
identity, while its missing severity counts could be displayed as zero.

## Source Of Truth

- `frontend/src/App.jsx` — `OverviewPage` and dashboard request state.
- `tests/test_frontend_monitoring_contract.py` — static UI safety contract.
- Existing B6/release/real-loop gate artifacts — read-only authority boundary.

## Scope

- In scope: dashboard project-identity readiness guard, missing/invalid
  severity-count display guard, focused static contract and minimal pending
  visual styling.
- Out of scope: backend/API schema, risk computation, source data, database,
  service/runtime/provider/browser/Playwright/API-login, real projects,
  medical writing, UAT or release authority.

## Success Criteria

- Overview content does not render until the returned dashboard is bound to
  the active project identity.
- Missing or invalid severity values display `—`; an explicit non-negative
  numeric zero remains visible.
- Focused contracts, all medical-monitoring Node contracts and Vite build pass;
  reserved ports stay empty and gate artifacts are unchanged.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 22:08:59: Task initialized by
  `tools/hermes_workflow_guard.py init-task`; no external role dispatched.
- 2026-08-04 22:06–22:09: Added overview pending identity guard, strict
  severity-count display and a lightweight pending-state style; added a
  regression contract.
- 2026-08-04 22:09: Focused frontend contracts **85 passed**, all 33
  medical-monitoring Node contracts passed and Vite build passed.
