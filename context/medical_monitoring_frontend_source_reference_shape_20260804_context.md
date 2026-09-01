# Task Context: medical_monitoring_frontend_source_reference_shape_20260804

Created: 2026-08-04 19:59:07
Objective: 防止医学监查风险来源分组把非字符串 locator 隐式转成合法可点击证据，同时保留 listing→方案→系统规则顺序和 malformed evidence 的可见边界
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx` — medical-monitoring risk dock/source grouping code (`riskSourceGroups`, `RiskSourceReference`).
- `tests/test_frontend_unified_risk_workbench_contract.py` — static contract for source grouping/order and evidence dock behavior.
- `frontend/src/features/medical-monitoring/medicalMonitoringRiskEvidenceContext.mjs` — consumer-side malformed evidence/lineage state.
- `records/active_slices/medical_monitoring_project_completion_audit_20260804/COMPLETION_MATRIX.md` — P1 evidence-order and risk-sensitive UX requirements.

## Scope

- In scope: surgical hardening of risk-source grouping to accept only explicit non-empty text locators/labels; preserve listing→protocol→system-rule order; add static regression.
- Out of scope: redesigning `App.jsx`, changing medical-writing components, API/service/runtime/provider/browser/Playwright, source data, risk facts, medical dispositions, or release gates.

## Success Criteria

- Numeric/object evidence locators are not converted to clickable/displayable strings.
- Valid string locators retain source preview and ordering behavior.
- Existing frontend monitoring contract suite and build remain clean.
- The risk context remains the visible malformed-evidence warning; no false "evidence bound" state is created.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Shared root file ownership is limited to the `riskSourceGroups` region; preserve
  unrelated `App.jsx` and medical-writing changes.
- Record the pre-change App hash before editing and use `apply_patch` only.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 19:59:07: Task initialized by `tools/hermes_workflow_guard.py init-task`.
