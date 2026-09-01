# Task Context: medical_monitoring_release_gate_strict_shapes_20260804

Created: 2026-08-04 19:41:58
Objective: 收紧医学监查商业发布门对证据 ID、哈希、摘要和 B6 状态的严格类型校验，防止 malformed payload 被字符串化后误计入发布判定
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_release_gate.py` — pure in-memory commercial release evaluator.
- `tests/test_monitoring_release_gate.py` — focused release-gate contract tests.
- `records/active_slices/medical_monitoring_release_evidence_coverage_20260802/CURRENT_RELEASE_COVERAGE.json` — current read-only 16-gate decision (`blocked`, `release_ready=false`).
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` — current B6/C14 and runtime boundary (`write_permitted=false`).
- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` §4/§8 — release gates and evidence boundary.

## Scope

- In scope: strict input-shape validation for release-gate IDs, SHA-256 strings, evidence summaries, B6 status, and decision tuple fields; focused regression tests and evidence records.
- Out of scope: B6 reviewer outcomes, aggregate/CAS replay, source-token revalidation, runtime/provider/browser activation, SQLite, real projects, frontend, medical-writing files, and release-status promotion.

## Success Criteria

- Non-string IDs/hashes/summaries/B6 status are rejected rather than coerced.
- Existing valid release evaluation and blocked B6 evaluation remain unchanged.
- Focused tests plus adjacent release-contract regression pass.
- The persisted current release decision remains `blocked`, `release_ready=false` and no authority flags change.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This is a diagnostic/read-only contract change; no runtime or persistent-data writes are permitted.
- Use `apply_patch` for source/test edits; preserve unrelated worktree changes.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 19:41:58: Task initialized by `tools/hermes_workflow_guard.py init-task`.
