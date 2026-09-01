# Task Context: medical_monitoring_assurance_backend_completion_gate_20260803

Created: 2026-08-03 05:27:19
Objective: 在核查前保障任务完成写入前校验持久化 rollup 的三层守恒、证据清单和关闭依据，阻断数据库漂移导致的错误完成
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md` §12 P8:
  three-level numbers must agree and closed/explained items need verifiable evidence.
- `services/api/app/monitoring_assurance_service.py` `complete_task`:
  current pre-inspection branch only checks that a persisted rollup exists.
- `services/api/app/monitoring_assurance_repository.py` `RollupSummary` and
  `get_rollup`/`complete_task`: the persisted rollup is an ID/reference-only object and
  the repository is the final write boundary.
- `services/api/app/monitoring_assurance_service.py` `build_rollup_payload`:
  canonical generated shape and explicit trial/site/subject/evidence/remediation fields.
- `tests/test_monitoring_assurance.py`: current real assurance lifecycle and temporary
  SQLite test fixtures.

## Scope

- In scope: a pure fail-closed validator for the persisted pre-inspection rollup and a
  call from `MonitoringAssuranceService.complete_task`; focused tests for generated,
  malformed, duplicate, non-conserved and missing-evidence rollups; current assurance
  backend regression evidence.
- Out of scope: changing rollup generation semantics, risk facts, task authority,
  B6/C14 gates, production/runtime SQLite, route schemas, frontend, real projects,
  browser/provider/service startup, or medical-writing surfaces.

## Success Criteria

- A canonical generated rollup passes unchanged and the existing pre-inspection
  lifecycle still completes only after medical review.
- Missing/invalid snapshot identity, trial/site/subject risk IDs or counts, duplicate
  IDs, incomplete evidence/remediation manifests, or non-zero/missing closure-evidence
  count yields `AssuranceTaskStateConflictError` before repository completion write.
- Existing pre-lock behavior and all assurance backend tests remain green.
- Validation is deterministic, ID/reference-only, does not infer risk facts, and has no
  external/runtime side effect.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 05:27:19: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: frontend evidence-gate correction exposed the corresponding backend
  completion risk; local code review found existence-only pre-inspection completion.
- 2026-08-03: no external discovery or new dependency was needed; the validator will
  reuse the existing generated rollup contract and repository boundary.
- 2026-08-03: added `validate_pre_inspection_rollup` and called it immediately before
  `repository.complete_task`; it checks task/project/snapshot identity, exact trial/site/
  subject ID sets and counts, duplicate IDs, evidence/remediation manifests and explicit
  zero closure-evidence gaps. The validator stores/rechecks references only.
- 2026-08-03: added a temporary SQLite regression that mutates a persisted site identity
  after medical review; completion returns 409 and no completed state is written. Focused
  assurance test **27 passed**, shared monitoring/frontend/timeline contract set **84
  passed**, all 107 monitoring Python files **1783 passed** in 492.68s, and Ruff/compile
  passed. No production/runtime DB or service listener was touched.
