# Task Context: medical_monitoring_risk_evidence_response_identity_guards_20260803

## Objective

Guard `RiskEvidenceDock` history and frozen-evidence responses by the
canonical project identity before committing history, source-preview or
source-fragment state; make mismatches visible and clear the affected state.

## Source and scope

- Workbench `frontend/src/App.jsx` `MonitoringPage`/`RiskEvidenceDock` and the
  existing history/evidence-fragment API contracts in `services/api/app/main.py`.
- In scope: risk history response, source-preview responses and opened source
  fragment response; static regressions and offline checks.
- Out of scope: new backend behavior, evidence content, clinical/scientific
  conclusions, source writes, intake/confirmation, provider/service/browser,
  real projects, B6/C14 and runtime.

## Success criteria

- Missing or wrong response `project_id` cannot populate or retain the current
  risk evidence dock state and produces a visible read error.
- Valid canonical responses retain existing rendering and race/request guards.
- Focused Python contracts, Node suites, Vite and Ruff remain green.

## Risk boundary and route

No service/provider/browser/API login/real-project/runtime operation. Workflow
guard route is recorded for audit only and is not dispatched; direct Codex owns
the implementation and acceptance.

## Loop log

- 2026-08-03 13:24:12: `tools/hermes_workflow_guard.py init-task` completed.
- 2026-08-03 13:24:30: Existing backend contracts inspected; both history and
  evidence-fragment payloads already expose canonical top-level `project_id`.
- 2026-08-03 13:28:10: `RiskEvidenceDock` now receives the canonical project id,
  guards history, bulk source previews and opened source fragments before state
  writes, and displays/clears the affected view on identity mismatch.
- 2026-08-03 13:29:40: Final focused pytest passed (92 passed, 17 existing
  warnings); Node 22 suites, Vite build, focused Ruff and medical-risk repository
  tests (22 passed) passed. No runtime/provider/browser route was opened.

## Workflow metadata

- Created: 2026-08-03 13:24:12
- Task type: `finite_code_task`; risk: `high`
- Recorded route: `opencode-go/deepseek-v4-flash/max`; not dispatched
- Codex is final authority; no production or runtime path was opened.
