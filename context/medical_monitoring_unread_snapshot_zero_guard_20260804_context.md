# Task Context: medical_monitoring_unread_snapshot_zero_guard_20260804

Created: 2026-08-04 22:03:20
Objective: Prevent unread or unavailable medical-risk snapshots from being presented as an explicit zero in the workbench UI; verify source-only contracts and preserve all runtime authority gates.
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

The risk checklist and monitoring header had a data-sensitive display gap:
before a risk snapshot was read, fallback values could be rendered as numeric
zero. This bounded source patch makes unknown/unavailable counts visibly
unknown without changing risk computation, API contracts or runtime authority.

## Source Of Truth

- `frontend/src/App.jsx` — monitoring risk count presentation and checklist
  wiring.
- `frontend/src/features/medical-monitoring/MedicalMonitoringRiskChecklist.jsx`
  — checklist total validation and label rendering.
- `tests/test_frontend_monitoring_contract.py` and
  `tests/test_frontend_unified_risk_workbench_contract.py` — static contracts.
- Existing B6/release/real-loop gate artifacts — authority and runtime
  boundary only; they were read, not changed.

## Scope

- In scope: fail-closed risk-count display for pending/unavailable snapshots;
  explicit unknown label in the checklist; focused regression contracts.
- Out of scope: backend/API schema, risk computation, source data, database,
  service/runtime/provider/browser/Playwright/API-login, real projects,
  medical writing, UAT or release authority.

## Success Criteria

- A missing or unread risk snapshot is never displayed as an explicit numeric
  zero in the monitoring header or checklist.
- An explicit non-negative integer zero returned by a valid snapshot remains
  visible as zero.
- Focused frontend contracts, all medical-monitoring Node contracts and the
  production build pass; reserved ports remain empty.
- No authority or persisted gate artifact changes.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 22:03:20: Task initialized by
  `tools/hermes_workflow_guard.py init-task`; no external role dispatched.
- 2026-08-04 22:04:00: Added pending/unavailable display guards and updated
  the stale static assertion to match the strict integer validation.
- 2026-08-04 22:05:00: Focused frontend contracts **84 passed**, all 33
  medical-monitoring Node contracts passed and Vite build passed.
- 2026-08-04 22:06:00: Read-only gate recheck kept B6 fresh/no issues but
  activation/medical approval/write false; release and real-loop remain
  blocked; ports 8911/5174/8910/4173 remain empty.
