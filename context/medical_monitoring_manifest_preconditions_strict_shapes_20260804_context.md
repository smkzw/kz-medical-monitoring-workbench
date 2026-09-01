# Task Context: medical_monitoring_manifest_preconditions_strict_shapes_20260804

Created: 2026-08-04 19:47:09
Objective: 收紧医学监查源清单预条件对项目、来源、路由和角色文本字段的严格形状校验，确保 malformed manifest 不会被字符串化后进入结构解析准备态
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_manifest_preconditions.py` — diagnostic-only source-manifest precondition validator.
- `tests/test_monitoring_manifest_preconditions.py` — five-project and malformed-manifest contract tests.
- `services/api/app/project_source_manifest.py` — public manifest producer used by the tests.
- `records/active_slices/medical_monitoring_manifest_preconditions_20260804/` — prior diagnostic evidence and boundary record.
- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` §2/§8 — source admission and release-boundary requirements.

## Scope

- In scope: make manifest text fields non-coercing; non-string project/source/route/role values must remain missing and produce a blocked report; add focused regression and evidence.
- Out of scope: source workbook/protocol reads, path resolution, field mapping, adapter activation, provider/runtime/browser/Playwright, API/SQLite writes, B6/C14, real projects and medical-writing surfaces.

## Success Criteria

- All five current public manifests keep `ready_for_structure_parse` with zero issues.
- Numeric/object/bytes values in project/source/route/role text positions cannot yield a clean report.
- Existing duplicate/unknown/unavailable/missing-source behavior remains unchanged.
- Diagnostic-only and all execution/medical authority flags remain false.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not open source data or resolve paths; this contract must stay metadata-only.
- Use `apply_patch` for source/test/evidence edits and preserve unrelated worktree changes.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 19:47:09: Task initialized by `tools/hermes_workflow_guard.py init-task`.
