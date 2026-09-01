# Task Context: p3_monitoring_rule_lineage

Created: 2026-07-29 05:09:26
Objective: 加固P3监测规则CM/IP核心边界、字段血缘和候选生命周期，并完成定向回归
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rules.py`
- `services/api/app/monitoring_rule_templates.py`
- `tests/test_monitoring_rule_templates.py`
- `tests/test_monitoring_rule_core_boundaries.py`
- Real RUX and MY009 listing files already referenced by the template test fixture.

## Scope

- In scope: core CM/IP family boundaries, deterministic field-lineage validation,
  candidate compilation lifecycle, complete fixture lineage, and focused tests.
- Out of scope: repository/database/service changes and unrelated tests.

## Success Criteria

- Hand-built study-treatment rules containing CM fail in the core model.
- Hand-built CM-policy rules containing EX/EC/DA/IP fail in the core model.
- Missing, conclusion-derived, model-output, and dependency-free lineage fails closed.
- Auditable raw and deterministic base lineage compiles.
- All 11 existing real-protocol rule families still compile and evaluate.
- Focused monitoring-rule tests pass.

## Risk Boundaries

- Write only the user-assigned implementation/test files plus workflow-owned task records.
- Do not modify repository, service, database, or other test modules.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 05:09:26: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29: Baseline template suite passed (28 tests); direct core checks
  reproduced both CM/IP bypasses.
- 2026-07-29: Implemented core CM/IP exclusions, template v2 lineage,
  candidate compilation, and complete 11-family fixture lineage.
- 2026-07-29: Assigned template/new-boundary suites passed 39 tests; API and
  repository hardening passed 14 tests. One legacy core-rule assertion now
  fails because a concurrently updated service requires stable record evidence.
  Real-MY008 collection is blocked in the active Python environment by missing
  `cryptography`; neither surface is in this task's write authority.
- 2026-07-29: Concurrent service fail-closed lifecycle/evidence suite passed
  all 17 tests.
- 2026-07-29: Final combined assigned/adjacent regression passed 70 tests.
