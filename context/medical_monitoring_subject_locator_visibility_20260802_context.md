# Task Context: medical_monitoring_subject_locator_visibility_20260802

Created: 2026-08-02 16:42:47
Objective: 在不启动运行时、不跨越B6权限且不修改App.jsx/styles.css的前提下，让Subject Timeline/Patient Profile的事件、趋势点、PD/Query、风险提示和事件索引直接显示显式来源定位，缺失定位时明示缺失，并补齐离线回归与审计记录。
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`
- `packages/contracts/workbench_contracts/models.py` explicit event/trend source fields
- `frontend/AGENTS.md` Subject Timeline/Profile evidence and desktop-density contracts
- Prior source-lineage slice: `records/active_slices/medical_monitoring_subject_lineage_20260802/`

The current filesystem is authoritative. This is an offline presentation/contract slice; no runtime response or real listing is treated as evidence.

## Scope

- In scope: expose the explicit locator (or “来源定位：缺失”) in Timeline detail rows, metric point detail rows, PD/Query cards, risk prompt cards, and the Profile source-event index; reuse the same locator extraction used by the lineage summary and add focused regression assertions.
- Out of scope: backend/API/adapter/contract changes, source registry, App shell, stylesheet, risk facts, clinical interpretation, locator synthesis, browser/runtime, SQLite, B6/C13 authority, aggregate/CAS, source-token revalidation, service startup, and real-project LOOP.

## Success Criteria

- Every visible record surface uses only explicit source locator, source record ID, evidence locator/list, or evidence span ID; title/date/count/order cannot create a locator.
- Missing locators remain visible as missing and do not silently disappear; long locators remain text-wrapped by existing layout rules.
- Protected `App.jsx`/`styles.css` hashes remain unchanged and all relevant Node/Python/build checks pass.
- Release audit/coverage remains hash-consistent and blocked; no authority or runtime permission changes.

## Risk Boundaries

- Do not modify `frontend/src/App.jsx` or `frontend/src/styles.css`; preserve required hashes.
- Do not infer or normalize locators from dates, titles, event IDs, row counts, or free text; do not claim a locator proves source authenticity or completeness.
- Do not start 8911/5174 or any service/provider/API/browser/SQLite/real project; do not write B6/C13, aggregate/CAS, source-token, migration, event, projection, or activation state.
- Only task-scoped context/review/metrics/records/release-audit/coverage surfaces may be updated beyond the three feature/test files; no external worker is dispatched.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

This direct Codex continuation has no provider/session timeout. Missing dependencies are documented as environment blockers, not installed opportunistically.

## Loop Log

- 2026-08-02 16:42:47: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Reused the lineage helper and added explicit locator labels to Timeline/Profile consumer surfaces; no shell/API/runtime write occurred.
- 2026-08-02: Subject-model locator assertions passed; full Node suite (22/22), focused Python contracts (64), Vite build (1925 modules), and release-gate regression (7) passed. Protected hashes and coverage replay remain unchanged.
- 2026-08-02: Hermes `review-gate --require-verification` returned `ok=true` with no warnings/errors; no runtime or real-project execution was performed.
