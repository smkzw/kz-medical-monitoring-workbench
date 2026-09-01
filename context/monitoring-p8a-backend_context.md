# Task Context: monitoring-p8a-backend

Created: 2026-07-29 22:25:44
Objective: 实现 P8-A 后端权威风险分类字典与医学风险 Checklist 七列稳定查询，完成聚焦、风险仓库、医学监查 API 和全监查回归，并记录 handoff/review/metrics
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `context/monitoring_p8a_backend_context.md`
- `reviews/monitoring_p8_risk_workspace_gap.md`
- Current `RiskCase`, medical risk repository, monitoring summary/router,
  deterministic-rule and AI risk bridges, RUX/MG-K10/MY009 adapters, and
  monitoring-specific tests.
- Current filesystem is authoritative. This workspace has no Git metadata, so
  changed-path review uses an explicit task file inventory and file timestamps.

## Scope

- In scope: a monitoring-only versioned closed risk taxonomy; explicit
  rule/category classification; legacy compatibility projection; CM versus
  EX/EC/DA/IP validation; Safety/PV overlay; current-snapshot seven-column
  filtering/sorting and stable snapshot pagination; focused tests; P8-A
  handoff/review/metrics.
- Allowed product files: `services/api/app/medical_monitoring_summary.py`,
  `services/api/app/medical_monitoring_router.py`,
  `services/api/app/medical_risk_repository.py`,
  `services/api/app/monitoring_rule_risk_bridge.py`,
  `services/api/app/monitoring_ai_risk_bridge.py`, a new monitoring taxonomy
  module, and necessary real-project monitoring adapters.
- Out of scope: `frontend/src/App.jsx`, global CSS, medical writing, shared AI,
  P7B/P7C rule lifecycle, shared contracts unless strictly required, live API
  restart, and the real runtime database.

## Success Criteria

- Title/rationale/display text changes do not change risk classification.
- Safety/PV remains an independent projection on one risk instance.
- CM cannot produce study-treatment categories and EX/EC/DA/IP cannot produce
  CM categories.
- Legacy coarse categories map explicitly without text-based refinement and
  preserve original-code lineage.
- Current snapshot API returns stable taxonomy projection and supports the seven
  declared filters/sort keys, deterministic tie-breaking, unknown-field
  rejection, and snapshot-pinned pagination.
- RUX, MG-K10, and MY009 paths remain compatible and expose stable projection.
- Focused, repository, monitoring API, and full monitoring regression pass.

## Risk Boundaries

- Do not modify or query the real runtime database; tests use temporary stores.
- Do not restart the API.
- Do not modify the excluded frontend, medical-writing, shared-AI, P7B/P7C, or
  shared-contract surfaces.
- Preserve existing API parameters where compatible; reject ambiguous conflicts.
- Codex owns final verification and acceptance.

## Solution Discovery

- Existing local architecture remains the selected route: a monitoring-only
  taxonomy/projection layer plus FastAPI query enums and repository snapshot
  lookup. No new dependency or executable component is required.
- External verification consulted FastAPI official query validation/Enum
  guidance and Python's official Enum documentation. These support typed closed
  query values; project-specific classification semantics remain controlled by
  the local P8-A contract.
- Rejected: title/rationale keyword classification, shared-model expansion, and
  real-database migration. Each would violate an explicit boundary or create
  unnecessary cross-subsystem risk.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 22:25:44: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29: Read the global/workspace instructions, P8-A contract, P8 gap
  review, live backend implementation, real adapters, and relevant tests.
- 2026-07-29: Selected a monitoring-only taxonomy and read-time projection;
  snapshot pinning will reuse exact persisted snapshots rather than mutate or
  recompute state.
- 2026-07-29: Implemented taxonomy, bridges, repository normalization,
  seven-field query/projection, snapshot pinning, and real-adapter categories.
- 2026-07-29: Independent review found that CM/study-treatment validation was
  not uniform at the persistence gate; added write-gate validation and tests.
- 2026-07-29: Final evidence: focused 88, repository 19, API 13, and full
  monitoring regression 716 passed. No API restart or real DB operation.
