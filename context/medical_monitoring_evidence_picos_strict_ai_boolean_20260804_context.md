# Task Context: medical_monitoring_evidence_picos_strict_ai_boolean_20260804

Created: 2026-08-04 22:54:39
Objective: Require literal boolean semantic-AI readiness in the evidence PICOS workflow gate and status label; add a regression for string-valued gateway status.
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/evidence_picos_workflow.py`: backend PICOS evidence-design workflow and AI-boundary gate.
- `tests/test_evidence_picos_workflow.py`: workflow/gate regression contracts.
- `services/api/app/ai_gateway.py`: canonical strict gateway-status producer.
- Existing P10/B6/C14/approved-input/host-identity records: runtime/provider/browser/real-project/medical approval remain closed.

## Scope

- In scope: require literal boolean semantic-AI readiness for the PICOS gate and configured label; add a regression for string-valued gateway status and run related offline tests.
- Out of scope: provider/runtime/browser/API login, real projects, database state, UI changes, medical-writing artifacts, and release authority.

## Success Criteria

- String-valued semantic-AI status cannot produce `ok` or `configured` in the PICOS workflow.
- Canonical boolean status remains covered by existing workflow/API tests.
- Related evidence/PICOS, AI, real-loop/assurance tests and syntax checks pass; reserved ports remain empty.

## Risk Boundaries

- Only the PICOS workflow, directly related test, and evidence surfaces may change.
- No delegated agent/provider/Hermes session, service startup, browser, API login, database, real project or production artifact mutation.
- Codex remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 22:54:39: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 22:56:00: Source inspection found two PICOS workflow truthiness sites; no runtime/provider/browser action was permitted.
- 2026-08-04 22:58:00: Changed both sites to literal-boolean checks, added the string-status regression, and completed offline verification; review-gate remains the next bounded action.
