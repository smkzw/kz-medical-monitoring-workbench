# Task Context: medical_monitoring_evidence_design_semantic_ai_boolean_20260804

Created: 2026-08-04 22:46:51
Objective: Use strict boolean semantic-AI readiness in the evidence-design workspace so non-boolean or false status values cannot render an AI action surface.
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/evidence-design/EvidenceDesignWorkspace.jsx`: evidence-design AI action surface.
- `tests/test_frontend_evidence_design_contract.py`: static UI contract tests.
- `frontend/src/App.jsx` and `services/api/app/ai_gateway.py`: shared gateway status vocabulary; semantic readiness is an explicit boolean.
- Existing P10/B6/C14/approved-input/host-identity records: no runtime/provider/browser/real-project activation.

## Scope

- In scope: change the evidence-design semantic-AI guard from truthiness to strict `=== true`, add a focused static regression, run frontend contracts/build and keep ports empty.
- Out of scope: evidence-design API behavior, backend/provider configuration, runtime/browser/API login, real projects, data, or medical-writing artifact changes.

## Success Criteria

- `semantic_ai_tasks_enabled: false`, missing, or string-valued status renders the disabled state in source contract; only literal `true` exposes the AI action surface.
- Existing evidence-design UI contracts, monitoring frontend contracts, Node contracts, and Vite build pass.
- No service/browser/provider starts and required ports remain empty.

## Risk Boundaries

- Only the evidence-design component, direct static test, and task evidence surfaces may change.
- No delegated agent/provider/Hermes session, API login, runtime, database, real project, or production artifact mutation.
- Codex remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 22:46:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 22:48:00: Found the evidence-design workspace's truthiness semantic-AI guard during cross-surface status audit.
- 2026-08-04 22:50:00: Switched the guard to literal boolean true; frontend contracts, Node tests, py_compile, build and port checks passed.
