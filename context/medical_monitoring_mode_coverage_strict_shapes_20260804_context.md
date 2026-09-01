# Task Context: medical_monitoring_mode_coverage_strict_shapes_20260804

Created: 2026-08-04 19:52:16
Objective: 收紧医学监查三模式真实LOOP覆盖证据的严格字符串与集合形状，防止 malformed role/project/mode evidence 被字符串化后计入覆盖
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_real_loop_mode_coverage.py` — read-only three-mode coverage evaluator.
- `tests/test_monitoring_real_loop_mode_coverage.py` — clean/dirty/duplicate/missing coverage tests.
- `services/api/app/monitoring_real_loop_acceptance.py` — canonical role/project/run identity consumed by the mode evaluator.
- `records/active_slices/medical_monitoring_real_loop_mode_coverage_20260803/MODE_COVERAGE.json` — current blocked, no-accepted-row mode evidence.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` — current runtime authority boundary.

## Scope

- In scope: strict string and collection shapes for mode evidence IDs, mode/role/run IDs, evidence refs, hashes and summaries; focused regressions and evidence.
- Out of scope: real LOOP runs, Playwright/browser/provider/API login, real projects, persisted acceptance promotion, B6/C14, source-token/CAS, runtime/database writes and medical-writing surfaces.

## Success Criteria

- Existing fixture-only clean/dirty/missing mode assessments keep their results.
- Non-string IDs/hashes/summaries or scalar reference fields cannot satisfy mode coverage.
- Current persisted mode coverage remains blocked and authority-free.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This change must remain a pure diagnostic contract and cannot manufacture real
  user-view or scientific evidence.
- Use `apply_patch` for source/test/evidence edits; preserve unrelated changes.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 19:52:16: Task initialized by `tools/hermes_workflow_guard.py init-task`.
