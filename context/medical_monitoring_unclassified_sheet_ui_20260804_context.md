# Task Context: medical_monitoring_unclassified_sheet_ui_20260804

Created: 2026-08-04 09:13:18
Objective: 将 raw-intake 未分类数据表作为可见、简洁、fail-closed 的医学监查 UI 提示，完成前端契约/静态构建/聚焦回归；不启动保留端口服务
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Latest `AGENTS.md` files, `frontend/AGENTS.md`, current raw-intake public
  payload, `frontend/src/App.jsx`, `frontend/src/styles.css`, and
  `tests/test_frontend_monitoring_contract.py`.
- Previous LOOP 5.87 contract: `unclassified_sheet_names` is an explicit
  fail-closed data-gap signal.

## Scope

- In scope: show a compact, high-salience warning in the medical-monitoring
  command surface when the backend reports unclassified listing sheets; keep
  the warning data-gap language and list only safe sheet names; add static
  contract coverage and build checks.
- Out of scope: changing backend semantics, AI/provider calls, browser/server
  startup, route/authorization, real projects, B6/C14, or unrelated UI.

## Success Criteria

- No warning is rendered for missing/empty/legacy payload fields.
- When one or more names are present, the UI shows count, sample names and a
  clear statement that those sheets are excluded from risk conclusions until
  field mapping and medical-monitor confirmation.
- Desktop density remains compact; no additional persistent panel or demo data
  is introduced.
- Python frontend contract tests, focused Node tests, and `npm run build` pass;
  reserved ports remain empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Because `frontend/AGENTS.md` asks for browser preview but the active medical
  monitoring boundary forbids starting 8911/5174, use static source/build
  verification only and record browser preview as not run for this slice.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 09:13:18: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 17:20:00: Added a compact UI warning for
  `unclassified_sheet_names`; Python contract 30 passed, medical-monitoring
  Node suites 31 passed, and Vite build passed. Browser preview was not run
  because the active 8911/5174 boundary remains closed.
