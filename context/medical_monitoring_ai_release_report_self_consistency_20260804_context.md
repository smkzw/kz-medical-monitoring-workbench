# Task Context: medical_monitoring_ai_release_report_self_consistency_20260804

Created: 2026-08-04 22:44:06
Objective: Make offline independent-AI release gate reports self-consistent when constructed directly: ready/approval-required states must match evidence-condition booleans and non-empty evidence/hash anchors.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_release_gate.py`: immutable offline independent-AI release-gate report and builder.
- `tests/test_monitoring_ai_release_gate.py`: release status and offline permission regressions.
- Existing P10/B6/C14/approved-input/host-identity evidence: runtime/provider/browser/real-project/medical-approval activation remains closed.
- Current filesystem is authoritative; no persisted production release artifact is to be rewritten.

## Scope

- In scope: reject directly constructed reports that claim READY or APPROVAL_REQUIRED without consistent evidence-condition booleans, evidence IDs, and required generalization snapshot anchor; preserve the pure builder output and hard-false runtime/provider/write permissions.
- Out of scope: changing release transitions, prompt/model selection, persisted artifacts, runtime activation, provider/browser/API login, real projects, UI, or medical-writing.

## Success Criteria

- A READY report with all flags true but no evidence IDs or generalization hash fails model validation.
- APPROVAL_REQUIRED is only valid when every non-approval evidence condition is true and approval is false.
- Existing builder-created ready/candidate/blocked reports remain valid and related AI/release tests pass.

## Risk Boundaries

- Only the release-gate module, its direct tests, and task evidence surfaces may change.
- No delegated agent/provider/Hermes session, runtime, browser, API login,
  database, real project, or production artifact mutation.
- Codex remains final authority; all offline permission flags stay false.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 22:44:06: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 22:46:00: Reproduced direct report states with empty evidence anchors and inconsistent approval booleans; builder output remained valid.
- 2026-08-04 22:48:00: Added report self-consistency validation and regressions; focused/full AI, real-loop/assurance, compile and port checks passed.
