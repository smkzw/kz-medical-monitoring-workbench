# Task Context: medical_monitoring_ai_candidate_source_binding_fail_closed_20260804

Created: 2026-08-04 22:37:01
Objective: Require completed independent-AI candidate evidence to bind to an explicit input source/hash pair; keep source-less revisions available for non-candidate recovery/data-gap contracts and verify adjacent tests.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_contracts.py`: immutable AI input, candidate and evidence contracts.
- `tests/test_monitoring_ai_repository.py`: candidate completion/source-binding regressions.
- `services/api/app/monitoring_ai_router.py`, `monitoring_ai_source_packet.py`, and daily/protocol services: production constructors that should continue to emit explicit source bindings.
- Existing P10/B6/C14/approved-input/host-identity records: runtime, provider, browser, real-project and medical-approval gates remain closed/read-only.
- Current filesystem is authoritative; no real project folder or production path is in scope.

## Scope

- In scope: make `validate_candidates_for_job` reject any candidate evidence whose source/hash pair is not explicitly present in the input revision, including the empty-source case; add a focused regression and run related offline contracts.
- Out of scope: requiring every non-candidate input revision to have sources, changing source packet construction, runtime/provider/browser/API login, SQLite outside test fixtures, real projects, UI, or medical-writing surfaces.

## Success Criteria

- A completed candidate cannot pass with an empty allowed source-pair set.
- Existing valid source-bound candidates continue to pass.
- Source/hash mismatch remains fail-closed and all relevant AI/repository/real-loop contracts pass.
- No runtime/provider/browser/Playwright/API-login/real-project action occurs; reserved ports remain empty.

## Risk Boundaries

- Only the monitoring AI contract and directly related test/evidence surfaces may change.
- Preserve source-less revision support for startup-recovery/data-gap inspection; the stricter boundary applies only when provider candidates are validated.
- No delegated agent/provider/Hermes session; Codex owns final verification.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 22:37:01: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 22:38:00: Confirmed the empty-source conditional in candidate validation and checked production constructors; protocol, risk, batch and daily-run paths emit explicit source bindings.
- 2026-08-04 22:40:00: Removed the empty-set bypass, added the source-less revision regression, and passed focused repository/service/API and product-AI suites.
