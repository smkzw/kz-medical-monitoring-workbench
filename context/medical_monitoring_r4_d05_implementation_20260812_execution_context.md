# Execution Context: medical_monitoring_r4_d05_implementation_20260812

Created: 2026-08-12 06:02:04
Objective: 实现并验证R4-D05访视评估样本时序合成离线纵切
Task type: `long_horizon_code`
Risk: `high`
Execution module trigger: Codex identified 4 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_k3_256k` -> `pi` / `cms-smk` / `deepseek-v4-flash`
- Execution manager: `complex_manager_cursor` -> `cursor` / `cursor-cli` / `auto`
- Execution-manager fallback: `Codex takes over complex execution management directly`

## Source Of Truth

- Frozen contract: `reviews/medical_monitoring_r4_d05_visit_schedule_slice_contract_v1_20260812.md`, final SHA-256 `23172cac905b3b152937976a7ee5d7eb895bac274ced7fc40a49b5f7a205921c`, status `FROZEN_R4_D05_CONTRACT_V1_2`.
- Contract acceptance: `context/medical_monitoring_r4_d05_contract_acceptance_record_20260812.md`.
- Official-source decision record: `context/medical_monitoring_r4_d05_visit_schedule_discovery_20260812.md`.
- Shared R4 contract: `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`.
- Adjacent accepted implementation: `poc/medical_monitoring_ai_native_r4/README.md`, `src/mm_r4/{contracts,coverage,lifecycle,protocol,protocol_projection,protocol_fixtures}.py`, root exports and their tests.
- R0-R8 plan: `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`.
- Current filesystem is authoritative. Do not restore from summaries or rejected D04/D05 hashes.

Baseline before dispatch:

- R4 full suite: `985 passed in 1.04s` with `PYTHONDONTWRITEBYTECODE=1` and no pytest cache.
- Shared hashes: contracts `993d6bea...e5c4`; lifecycle `99fec3e3...d795`; protocol `4665c511...7f47`; protocol projection `c4cf09ce...38b0`; protocol fixtures `ea512044...b30f`; root init `d5e0050c...ca5ad`; README `9858bb4e...ab12`.
- Port 8911 has no listener.

## Risk Boundaries

- Synthetic/offline only. Do not read or run any real project, provider, service, browser, product path or database; do not start 8911.
- Do not modify R1/R2/R3, D01-D04 accepted source/tests, `contracts.py`, `coverage.py`, `lifecycle.py`, `protocol*.py`, product frontend/backend, or the medical-writing subsystem.
- No security design/testing, dependency installation, credential handling or external account action.
- New implementation paths are limited to:
  - `poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule.py`
  - `poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule_evaluator.py`
  - `poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule_projection.py`
  - `poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule_fixtures.py`
  - matching new `tests/test_visit_schedule_*.py` files.
- Integration-only writes are limited to `poc/medical_monitoring_ai_native_r4/src/mm_r4/__init__.py` and `poc/medical_monitoring_ai_native_r4/README.md`; only worker_04 or the manager may touch them after worker 01-03 outputs exist.
- Workers 01-03 must not edit the same file: worker_01 owns `visit_schedule.py` + contract test; worker_02 owns evaluator + slice test; worker_03 owns projection/fixtures + projection/challenge tests. Worker_04 owns only root exports/README and read-only regression evidence.
- New files may import frozen public surfaces read-only. If the contract genuinely requires a shared-file change, stop and report the exact need; do not broaden scope.
- Worker/manager outputs are evidence, not final acceptance. Codex owns clinical interpretation, full regression, immutable snapshot and final acceptance.

## Success Criteria

1. Every public D05 object and enum in §§3-12 is immutable, validated and content-addressed; illegal gate state, identity, cutoff, bundle, assignment and typed-anchor combinations fail closed.
2. Expected-set is frozen only after applicability/routing/anchor/scope resolution; future/out-of-cutoff records do not enter medical denominators; fixed and chained anchors are distinct.
3. Visit and activity assignment are bidirectional; encounter bundles and consumption ledgers prevent silent duplicate use; no nearest-date/VISITNUM/row-order shortcut.
4. Five L1 dispositions, coverage notices, positive candidates, enrollment-aware three-part Query drafts, public lifecycle adapter input and Chinese labels satisfy the frozen contract.
5. Renderer-neutral Journey keeps planned visits and actual encounters separate, supports pending/out-of-cutoff anchors and stable bidirectional joins; no internal labels leak to audience payloads.
6. All 116 contract challenges map to named executable assertions or explicit accepted adjacent tests; golden hashes and input-order replays are deterministic.
7. Focused D05 tests pass; R4 full, frozen R2 and R3 suites, Ruff/compileall and root imports pass; D01-D04/shared hashes remain unchanged except authorized `__init__.py`/README integration.
8. Port 8911 remains stopped; no real-project, product, R5 UI, provider, medical-writing or security scope is touched.

## Execution Order And Stop Conditions

Execute sequentially: worker_01 → worker_02 → worker_03 → worker_04 → manager. Later workers must inspect current files and consume prior accepted new modules; do not re-create or rewrite another worker's file. Stop and report if a dependency is missing, a prior worker file drifted during the pass, or the contract cannot be implemented without a prohibited shared-file modification. Slow execution is pending, not failure; use one session per role and same-session correction only for a concrete gap.

## Work Items

1. 实现D05领域对象、双cutoff、gate、bundle与typed anchor合同
2. 实现expected-set、访视与活动双向assignment、评价和Query/lifecycle接线
3. 实现Patient Journey投影、116行合成挑战矩阵与确定性金样
4. 完成根包导出、README、聚焦及D01-D04/R2/R3相邻回归并整理执行证据

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
