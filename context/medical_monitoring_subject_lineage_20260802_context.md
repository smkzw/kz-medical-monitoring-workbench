# Task Context: medical_monitoring_subject_lineage_20260802

Created: 2026-08-02 16:27:33
Objective: 在不启动运行时、不跨越B6权限且不修改受保护App.jsx/styles.css的前提下，为Subject Timeline/Patient Profile增加基于明确source_revision与显式来源定位字段的来源绑定摘要、测试与审计记录，禁止从日期/标题/计数推断来源或完整性。
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`
- `packages/contracts/workbench_contracts/models.py` Subject Timeline/Profile contracts
- `services/api/app/mgk10_sar_monitoring_service.py`, `my009_monitoring_service.py`, and `rux_monitoring_service.py`
- `services/api/app/monitoring_project_registry.py` source-revision stability boundary
- `frontend/AGENTS.md` Subject Timeline and Patient Profile visual/source contracts
- Existing release evidence: `records/active_slices/medical_monitoring_goal_p10_20260730/RELEASE_GATE_AUDIT_20260802.md`, B6/C14 fail-closed reports, and current release coverage record

The filesystem is the current truth. This slice is a bounded local code-and-record change; no external source, runtime response, database, or real project listing is treated as evidence.

## Scope

- In scope: expose a compact, explicit source-lineage summary for the Subject Timeline and Patient Profile; count only actual timeline events, metric points, and risk prompts; use explicit `source_locator`, `source_record_id`, evidence locator fields, or evidence span IDs; treat `legacy` as non-authoritative; add focused unit coverage and durable audit/review records.
- Out of scope: changing `App.jsx`, `styles.css`, backend adapters/contracts, API/runtime behavior, source registry, SQLite, B6/C13 disposition authority, event creation/projection, aggregate/CAS replay, service startup, browser acceptance, or any of the three real-project LOOP runs.

## Success Criteria

- A bound payload reports its explicit source revision and traced/untraced record counts without inferring provenance from dates, titles, or counts.
- Missing revision, batch-only payloads, legacy sentinel values, empty payloads, and missing row locators remain visibly non-authoritative and never imply “no risk”.
- Timeline and Profile surfaces show the status and a concise warning/footnote without changing protected app shell or visual stylesheet contracts.
- Subject-model tests, all medical-monitoring frontend model/view tests, focused Python frontend contracts, production frontend build, and source-revision contract tests are recorded with exact outcomes.
- B6/C14 remain fail-closed and no runtime/service/real project is started.

## Risk Boundaries

- Do not modify the protected `frontend/src/App.jsx` or `frontend/src/styles.css` files; preserve their existing hashes.
- Do not treat `source_batch_id`, a default `legacy` revision, dates, titles, row counts, or empty states as proof of source identity, completeness, trend comparability, or absence of risk.
- Do not cross the pending B6 review gate: no disposition approval, aggregate/CAS replay, migration write, event creation, projection, service/API startup, browser session, or real-project LOOP.
- Records may be updated only in task-scoped `context/`, `reviews/`, `metrics/`, `records/active_slices/`, release-audit, and coverage surfaces; production code changes are limited to the two named feature files and their test.
- Codex performs final review and acceptance directly; no external worker or sub-agent is dispatched for this continuation.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

This direct Codex slice has no provider/session timeout. A missing local dependency is recorded as an environment blocker rather than repaired by installing packages or broadening scope.

## Loop Log

- 2026-08-02 16:27:33: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Re-anchored project and frontend instructions, protected-file boundary, pending B6/C14 state, and real-adapter source-revision contracts.
- 2026-08-02: Implemented `subjectEvidenceLineageSummary()` and Timeline/Profile status rendering using explicit source fields only; added six edge-case tests including `legacy` and empty-state handling.
- 2026-08-02: Verified 22/22 medical-monitoring frontend test files, 64 focused Python frontend contracts, successful Vite production build, and 7 source-revision tests; main service-import tests remain collection-blocked by missing global `cryptography`.
- 2026-08-02: Next record action is to persist hashes/review evidence and rebind release coverage; B6 outcome remains pending and all writes/activation remain prohibited.
