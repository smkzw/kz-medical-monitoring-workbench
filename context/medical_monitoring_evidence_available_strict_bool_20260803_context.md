# Task Context: medical_monitoring_evidence_available_strict_bool_20260803

Created: 2026-08-03 12:12:54
Objective: Make RiskEvidenceFragmentSnapshot.available fail closed on non-boolean persisted values without enabling runtime or authority paths.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint
because it is a high-risk contract change requiring source-grounded tests and a
durable review handoff.

## Source Of Truth

- `packages/contracts/workbench_contracts/models.py`
- Existing medical-monitoring risk export/bridge tests
- Current B6/C14 gate JSON and the P10 offline boundary checkpoint

## Scope

- In scope: strict Boolean parsing for `RiskEvidenceFragmentSnapshot.available`
  and focused regression evidence.
- Out of scope: runtime/provider/service/browser/API login, real projects, UI,
  B6/C14 activation, CAS/source-token writes, migration and medical-writing
  changes.

## Success Criteria

- Literal booleans remain accepted; strings, numbers and `None` fail closed.
- Focused/adjacent monitoring tests, Ruff, compileall and review-gate pass.
- No runtime or authority boundary is opened.

## Risk Boundaries

- Do not write to production paths or runtime state.
- Do not synthesize B6 reviewer outcomes or activate C14.
- Codex is final authority; no delegated agent was dispatched.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 12:12:54: Task initialized by
  `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Direct model probe confirmed Pydantic coerced malformed values
  before the patch.
- 2026-08-03: `StrictBool` contract patch and five malformed-value regressions
  implemented; focused/adjacent set passed 70 tests.
- 2026-08-03: Shared high-signal set passed 508 tests; one unrelated oMLX
  translation availability assertion failed.
- 2026-08-03: Full monitoring-suite attempt terminated by SIGTERM near 75%;
  no full-suite pass claimed.
