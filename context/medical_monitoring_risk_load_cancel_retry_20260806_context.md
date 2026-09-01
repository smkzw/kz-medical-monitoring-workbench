# Task Context: medical_monitoring_risk_load_cancel_retry_20260806

Created: 2026-08-06 00:30:43
Objective: improve P1-05 medical-monitoring risk checklist loading UX with explicit cancel/retry and truthful stale-result messaging while preserving project identity and runtime gate
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- PRD gap matrix P1-05: large-project loading needs truthful progress,
  cancellation, retry and explicit empty states.
- `frontend/src/App.jsx` `MonitoringPage` risk snapshot effect and checklist
  ledger header.
- `frontend/src/features/medical-monitoring/MedicalMonitoringRiskChecklist.jsx`
  current error/loading/empty rendering.
- Existing medical-monitoring frontend static contracts, Node module tests and
  current `CURRENT_REAL_LOOP_GATE_AUDIT.json`.

## Scope

- In scope: a project-bound risk-index request cancellation seam, a same-query
  retry trigger, truthful cached-result/loading copy, and a retry action in the
  Checklist error state; focused static tests and build verification.
- Out of scope: backend precomputation/index architecture, risk facts,
  pagination schema, medical status, API/server/runtime/SQLite, providers,
  browser/Playwright, real projects/LOOP, B6/C14, medical-writing code, and
  broad performance refactoring.

## Success Criteria

- A senior medical monitor can see whether the current condition is loading,
  whether a previous result remains visible, and can cancel or retry without
  changing project/risk identity or inventing a zero-risk result.
- Abort cleanup prevents stale responses from writing after cancellation or
  query/project changes.
- Error state exposes a retry action; loading state exposes cancellation only
  while an active request exists.
- Existing monitoring static/Node contracts and Vite build pass; writing
  source remains untouched; runtime gate remains blocked.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not start 8911, 5174, 8910, or 4173, services, browsers, providers, API
  login, or real project data while the formal gate is blocked.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 00:30:43: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 00:32:52: Added controller-owned cancellation, same-query retry,
  truthful retained-result/loading copy, and Checklist error retry control.
  Monitoring/static contracts: 164 passed; medical-monitoring Node suite: 35
  files passed; Vite build: 1957 modules transformed and passed. Medical-writing
  protection sample remains 197 passed / 2 existing translation-batch failures;
  no writing source changed.
- 2026-08-06 00:32:52: Review-gate passed with no warnings. Current gate remains
  `read_only / blocked`; ports 8911/5174/8910/4173 remain empty. Next safe
  action is real large-project cancel/retry/performance exercise only after
  formal B6 outcomes and source-token/CAS revalidation open the gate.
