# Task Context: medical_monitoring_p9_evidence_order_20260805

Created: 2026-08-05 10:15:26
Objective: Fix P1-03 evidence panel hierarchy so readable facts precede protocol basis and rule explanation, with source locators secondary and collapsible, without changing evidence authority or runtime boundaries
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` P1-03: evidence order must be readable fact text → protocol basis → system rule/calculation → secondary locator.
- `docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md` §9/P5: the risk workspace must keep evidence readable and traceable while preserving the same risk, subject, filter, and scroll context.
- `frontend/src/App.jsx`: `RiskEvidenceDock`, `RiskDetail`, `riskSourceGroups`, and `RiskSourceReference` are the current source-bound UI path.
- `frontend/src/styles.css`: current evidence groups use a three-column layout and expose locators inline.
- `services/api/app/monitoring_source_fragment.py` and `services/api/app/monitoring_risk_evidence.py`: frozen fragment fields (`primary_summary`, `fields`, `locator`) are the only readable source evidence allowed; UI must not synthesize missing facts.
- `packages/contracts/workbench_contracts/models.py`: `RiskCase.evidence_span_ids` and `WorkbenchItemSourceRef` define explicit evidence bindings.
- Runtime/real-project gate remains read-only and blocked; no service, provider, browser, API login, or real-project data may be activated in this slice.

## Scope

- In scope: change the evidence presentation order in the monitoring risk workspace; make the four evidence stages explicit; make locator text secondary/collapsible; preserve source preview/open behavior and project/risk identity guards; add focused source-level tests/build checks and durable records.
- Out of scope: backend contracts, source capture, risk semantics, route state, real projects, runtime activation, external AI calls, service/browser startup, medical disposition behavior, and the parallel medical-writing subsystem.

## Success Criteria

- The risk detail and source-evidence views visibly follow `1 原始事实 → 2 方案依据 → 3 系统规则/计算 → 4 来源定位（展开查看）`.
- Missing source stages remain explicit and do not use the risk title/rationale as a fabricated raw fact.
- Locator strings are not prominent by default but remain available through a keyboard-accessible disclosure and the existing read-only source action.
- Existing evidence preview/frozen-fragment identity checks remain unchanged.
- Focused frontend tests, the full pure frontend module set, syntax check, and Vite production build pass; no service/runtime or real-project activation occurs.

## Risk Boundaries

- Only `frontend/src/App.jsx`, `frontend/src/styles.css`, the generated `frontend/dist/` bundle produced by the verified build, focused frontend tests/helpers, and this task's context/review/metrics/record files may change.
- Do not change evidence payloads, source authority, API contracts, risk identity, or frozen snapshot semantics.
- Do not start ports 8911/5174/8910/4173, services, providers, Playwright, external testers, or real projects.
- Codex owns final source, test, runtime-boundary, and acceptance verification.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 10:15:26: Task initialized by `tools/hermes_workflow_guard.py init-task`.
