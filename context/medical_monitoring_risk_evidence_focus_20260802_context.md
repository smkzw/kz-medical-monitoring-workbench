# Task Context: medical_monitoring_risk_evidence_focus_20260802

Created: 2026-08-02 16:47:48
Objective: 在不启动运行时、不跨越B6权限且不修改App.jsx/styles.css的前提下，让Patient Profile风险提示和PD/Query消费面直接显示显式关联事件、指标键与证据span数量；空关联显式提示未绑定，不从提示文字或计数推断临床关联，并补齐回归与审计记录。
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`
- `packages/contracts/workbench_contracts/models.py` `TimepointRiskPrompt` fields (`related_event_ids`, `related_metric_keys`, `evidence_span_ids`)
- `frontend/AGENTS.md` risk-focus and source-evidence contracts
- Prior lineage/locator evidence: `records/active_slices/medical_monitoring_subject_lineage_20260802/` and `medical_monitoring_subject_locator_visibility_20260802/`

The filesystem is authoritative. This is a bounded offline consumer-layer slice; it will not claim that explicit links prove clinical correctness or source authenticity.

## Scope

- In scope: add a pure `riskPromptEvidenceSummary` that reads only explicit related event IDs, metric keys, risk IDs and evidence span IDs; show compact linked-fact counts/identifiers beside Profile risk and PD/Query prompts, with an explicit unbound state; add a per-row risk Checklist evidence badge based only on explicit locator/reference arrays.
- Out of scope: synthesizing links from prompt text/date/order/count, changing risk facts or severity, API/backend/adapter/SQLite/runtime, source-token/B6/C13/aggregate/CAS, App shell, styles, service startup, browser, or real-project LOOP.

## Success Criteria

- A prompt with explicit links shows deterministic event/metric/evidence counts and stable identifiers; an empty link set says “未绑定关联事实” and does not imply no risk. Checklist rows show `证据定位 N 条`, `来源引用 N 条`, `来源证据形状异常`, or `来源证据缺失` without inferring from titles.
- Existing focusRiskId routing and Timeline/Profile content remain behaviorally unchanged; only evidence relationship visibility is added.
- Focused tests, full Node suite, Python frontend contracts, build, release coverage replay, protected hashes and Hermes review-gate pass.

## Risk Boundaries

- Do not modify `frontend/src/App.jsx` or `frontend/src/styles.css`; preserve their required hashes.
- Do not infer associations from title, date, free text, severity, row count, or risk label; do not synthesize missing IDs.
- Do not start 8911/5174 or any service/provider/API/browser/SQLite/real project, and do not write B6/C13/aggregate/CAS/source-token/activation state.
- Only the two feature files, the focused test, and task-scoped records/audit surfaces may be updated; no external worker is dispatched.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

Direct Codex continuation has no provider/session timeout. Environment dependency gaps will be recorded rather than repaired opportunistically.

## Loop Log

- 2026-08-02 16:47:48: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Re-anchored the `TimepointRiskPrompt` contract and the existing Timeline/Profile risk-focus path; no runtime or external route was used.
- 2026-08-02: Next bounded action is a pure explicit-link summary plus visible unbound state, followed by focused/full regression and hash-bound release coverage rebind.
- 2026-08-02: Extended the same boundary to the dense risk Checklist row badge; 63 model assertions, 22/22 Node files, 64 Python contracts and the production build passed.
