# Task Context: medical_monitoring_real_loop_readiness_semantics_binding_20260804

Created: 2026-08-04 12:10:37
Objective: 将 manifest↔semantics binding hash/matched 约束接入 RealLoopReadiness 并保持 upstream gate fail-closed
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Latest global/workspace/workbench `AGENTS.md` and current filesystem.
- `monitoring_real_loop_readiness.py`, LOOP 5.98 manifest↔semantics binding, and current readiness/
  execution test fixtures.
- Current B6/C14/source-token/CAS/approved-input/runtime evidence remains unresolved and all controlled
  runtime ports must remain stopped.

## Scope

- In scope: add strict semantic-binding matched/hash fields to `RealLoopGateInput` and
  `RealLoopReadinessReport`; require a binding whenever an upstream prerequisite is asserted true;
  update synthetic readiness/execution fixtures and regression tests.
- Out of scope: changing current gate decisions, opening runtime/provider/API/browser/Playwright/
  real-project execution, changing execution/acceptance schemas beyond readiness propagation,
  B6/C14 activation or medical conclusions.

## Success Criteria

- Existing blocked/no-gate paths retain their prior diagnostics without unrelated semantic noise.
- Any true upstream prerequisite without `semantics_binding_matched=true` and valid SHA-256 fails
  closed; execution-ready readiness carries the binding hash and matched flag.
- Compile/Ruff, focused/adjacent/full tests and reserved-port checks pass; review-gate is clean.

## Risk Boundaries

- Only readiness source/tests/records/review/metrics are in scope; no original gate/manifest mutation.
- Direct Codex only; no delegated agent/provider. Readiness remains a planning contract and never grants
  runtime/provider/write authority.
- Keep B6/C14 and 8911/5174/8910/4173 closed; existing non-reserved processes are not modified.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 12:10:37: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 12:11: readiness semantic-binding fields and strict true-gate requirement were added;
  synthetic ready fixtures now carry a binding hash. Focused **55**, adjacent **125**, full **2018**
  passed with 25 warnings; reserved ports and AGENTS hashes unchanged.
- Final Hermes `review-gate --require-verification` returned `{"ok": true, "warnings": [], "errors": []}`.
