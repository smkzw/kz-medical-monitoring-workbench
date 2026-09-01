# Task Context: medical_monitoring_identity_mismatch_visible_fail_closed_ux_20260803

Created: 2026-08-03 13:16:37
Objective: Make wrong-project monitoring read responses visibly fail closed while clearing affected state, without adding runtime or provider behavior.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Source Of Truth

- Workbench `frontend/src/App.jsx` `MonitoringPage` read effects and existing
  risk/raw-intake error surfaces.

## Scope

- In scope: for risk snapshot, taxonomy, focused-risk and raw-intake identity
  mismatches, clear affected state and show an explicit project-identity error;
  add static regressions and offline checks.
- Out of scope: API/backend contracts, provider/service/browser, write actions,
  clinical/scientific conclusions, real projects, B6/C14 and runtime.

## Success Criteria

- Wrong-project or missing-identity responses remain fail-closed and become
  visible to the risk-sensitive medical monitor; valid responses retain current
  behavior.
- Focused frontend contracts, Node suites, Vite and Ruff remain green.

## Risk Boundaries

- No service/provider/browser/API login/real-project/runtime write; no B6/C14
  authority or release claim.
- Route is recorded for audit only and will not be dispatched; direct Codex owns
  verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 13:16:37: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 13:16:55: Direct Codex selected; no external route dispatched.
- 2026-08-03 13:19:13: First focused pytest run exposed one stale static assertion expecting the old positive identity branch; the assertion was removed because the implementation is intentionally fail-closed on `!==`.
- 2026-08-03 13:19:32: Final focused pytest passed (76 passed, 17 existing warnings); all 22 medical-monitoring Node suites passed; frontend Vite production build passed with the existing large-chunk advisory. No runtime or provider route was opened.
