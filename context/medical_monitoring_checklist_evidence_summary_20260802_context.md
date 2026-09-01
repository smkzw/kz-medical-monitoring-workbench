# Task Context: medical_monitoring_checklist_evidence_summary_20260802

Created: 2026-08-02 17:19:18
Objective: 为风险 Checklist 增加当前页显式证据覆盖摘要，保持少点击、数据敏感且不改变风险事实或运行边界
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs` owns explicit row evidence-shape semantics (`riskRowEvidenceBadge`).
- `frontend/src/features/medical-monitoring/MedicalMonitoringRiskChecklist.jsx` is the dense risk list consumer; existing `.risk-checklist-column-state` styles are the available compact surface.
- Current release audit/coverage, B6/C14 records and protected `frontend/src/App.jsx`/`styles.css` hashes remain read-only boundaries.

## Scope

- In scope: add pure current-page evidence coverage summary/message helpers; render a compact page-scoped status line in the Checklist; add model assertions and preserve existing row badge behavior.
- Out of scope: project-total claims, API/backend/SQLite/runtime, App/styles changes, risk facts/severity/disposition, source inference, services/browser/real projects, B6/C13/C14.

## Success Criteria

- The summary counts bound locator rows, reference-only rows, missing rows and malformed rows from explicit fields only; it says `当前页` and never claims project completeness.
- Empty pages stay distinct from no-risk; missing/abnormal evidence explicitly does not mean no risk.
- Node suite, focused Python contracts, Vite build, release gate, audit/coverage replay and Hermes review gate pass; protected hashes remain unchanged.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 17:19:18: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Direct Codex route; no external dispatch. Existing per-row badges were confirmed, but no compact page-level evidence distribution was visible to a lazy, data-sensitive reviewer.
