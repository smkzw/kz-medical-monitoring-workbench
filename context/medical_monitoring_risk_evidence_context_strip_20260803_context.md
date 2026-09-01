# Task Context: medical_monitoring_risk_evidence_context_strip_20260803

Created: 2026-08-03 21:04:52
Objective: Add a strict read-only risk evidence/context strip so senior monitors can see identity, lineage, evidence readiness and disposition state before reviewing the dock
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Existing risk dock: `frontend/src/App.jsx` (`RiskEvidenceDock`, `RiskDetail`) and `frontend/src/styles.css`.
- Existing row projection/shape conventions: `frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs` (`riskRowEvidenceBadge`, source lineage and disposition labels).
- Existing risk API identity boundary: `createMedicalMonitoringApi` and the current project-bound fetches in `App.jsx`.
- Current filesystem is authoritative. This slice is a read-only presentation consumer of the selected risk object; it does not call an API or write state.
- Release boundary: B6/C14, source-token/CAS and real-loop evidence remain fail-closed; no service, browser, provider or real project may be started.

## Scope

- In scope: strict risk identity/evidence/lineage/disposition summary model; compact component/CSS; mount at the top of the selected risk evidence dock; focused and full frontend regressions/build; task evidence.
- Out of scope: backend/API changes, risk facts, disposition writes, source-fragment fetching, timeline/profile data changes, release gates, browser/Playwright, real projects and clinical interpretation.

## Success Criteria

- Selected risk shows explicit project scope, subject/site IDs, risk instance/key, source snapshot/version, evidence locator/reference status, unread/action state and current disposition in one compact strip.
- Missing or malformed fields remain visible as `待核对`/shape warning; no risk or evidence is inferred from title, row order or fallback IDs.
- Existing evidence tabs, action controls and App shared surfaces continue to build and pass all medical-monitoring Node tests.
- Durable task context, review, metrics and LOOP ledger record the result; commercial release status remains unchanged.

## Risk Boundaries

- Only the workbench frontend feature, existing `App.jsx` import/mount seam, derived build output and task records may change.
- Do not treat evidence locator presence as evidence validity, risk closure or clinical truth; keep source shape and missing lineage visible.
- No disposition write, no API response mutation, no external role dispatch. Codex remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 21:04:52: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Direct Codex slice planned after reviewing the risk checklist, evidence dock, source lineage and disposition contracts. External execution is intentionally not dispatched.
- 2026-08-03: Added strict risk evidence/context normalizer and compact dock strip. Focused model, all 27 medical-monitoring Node files and Vite build passed; no API, runtime, browser, real project or release-gate action occurred.
