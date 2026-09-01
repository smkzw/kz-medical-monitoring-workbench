# Task Context: medical_monitoring_frontend_shared_consumer_regression_20260803

Created: 2026-08-03 14:16:28
Objective: 验证医学监查与并行医学写作共享前端消费者全量 Node 回归与 Vite 构建无回归
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/**/*.test.mjs`
- `frontend/src/features/medical-writing/**/*.test.mjs`
- `frontend/src/features/writing-reference/**/*.test.mjs`
- `frontend/package.json` and the existing Vite build configuration
- `.venv/bin/python -m pytest -q tests/test_monitoring_*.py`
- The shared root consumer `frontend/src/App.jsx` and existing 5.06–5.14
  identity-boundary changes
- B6/C14 gate JSON and the offline boundary checkpoint for non-runtime limits

## Scope

- In scope: run the complete local frontend Node test-file set and the Vite
  production build; verify that medical-monitoring and the parallel
  medical-writing/writing-reference consumers remain green.
- Out of scope: source edits, service/API/provider/browser login, real projects,
  SQLite/runtime writes, B6/C14 changes, visual/browser acceptance, and release
  or commercial claims.

## Success Criteria

- All discovered frontend `*.test.mjs` files pass.
- The complete monitoring Python suite passes with warnings recorded explicitly.
- Vite production build succeeds; existing chunk-size advisory may remain.
- No listener on 8911/5174 and no medical-writing source changes occur.
- Codex records the exact counts and keeps this evidence separate from runtime,
  scientific, UAT and commercial acceptance.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Route is recorded only; direct Codex ran the bounded checks and did not
  dispatch an external agent.
- B6 remains `pending_review`, C14 remains blocked, and 8911/5174 remain
  stopped.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 14:16:28: Task initialized by `tools/hermes_workflow_guard.py init-task`.
