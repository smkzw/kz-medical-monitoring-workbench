# Execution Context: medical_monitoring_r4_d07_runtime_20260813

Created: 2026-08-13 23:10:20
Objective: 在隔离 R4 POC 中实现冻结 D07 临床安全性、实验室与检查运行时，并通过 144 例独立 oracle、中文 Query/Journey、生命周期与相邻回归验收。
Task type: `long_horizon_code`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_k3_256k` -> `pi` / `cms-smk` / `deepseek-v4-flash`
- Execution manager: `complex_manager_cursor` -> `cursor` / `cursor-cli` / `auto`
- Execution-manager fallback: `Codex takes over complex execution management directly`

## Source Of Truth

- Frozen contract: `reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md`, file SHA-256 `0b1f42c108ab6d4f5caa11a879cd2233328518e061772f74668cf1afd520fe84`, semantic SHA-256 `6facbaed37a97f7963a3010072687d0a2509a0f0e768058bd71067b36ec3b02a`.
- Accepted freeze record: `context/medical_monitoring_r4_d07_artifact_freeze_acceptance_record_20260813.md`.
- Immutable typed input: `reviews/medical_monitoring_r4_d07_typed_fixture_catalog_v1_20260813.json`.
- Test-side authorities only: `reviews/medical_monitoring_r4_d07_expected_outcome_oracle_v1_20260813.json`, `reviews/medical_monitoring_r4_d07_challenge_manifest_registry_v1_20260813.json`, `tools/generate_d07_challenge_registry.py`, `tests/test_d07_artifact_generator.py`. Runtime source must not import/read them or case/test/fixture identifiers or expected values.
- Allowed implementation roots: `poc/medical_monitoring_ai_native_r4/src/mm_r4/`, `poc/medical_monitoring_ai_native_r4/tests/`, and the R4 README. Existing D01-D06/R1-R3 are read-only semantic patterns and adjacent regression targets.
- Current filesystem is authoritative; preserve concurrent unrelated work.

## Risk Boundaries

- No product or production writes; do not read/run real projects; do not modify the medical-writing subsystem.
- Do not start any service or port 8911. Do not implement/test system-security features.
- Do not edit the frozen contract, catalog, oracle, registry or generator to make tests pass.
- New source writes are limited to D07-specific modules, minimal root exports/README, and D07-specific tests. If an existing frozen implementation file appears to require semantic change, stop that edit and report it.
- D07 owns clinical safety/laboratory/examination interpretation only. D01 AE/MH, D04 protocol/PD, D06 efficacy and D08 cross-domain causality remain typed handoffs; no duplicate risks.
- No D09/D10 aggregation, regulatory conclusion/report, Query sending/reply tracking, R5 UI or product acceptance claim.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.

## Work Items

1. 实现 D07 闭合 typed runtime、pre-evaluator integrity、确定性医学求值、owner/handoff/priority/lifecycle；仅写 D07 新模块与专属单元测试。
2. 实现 test-only 144 例 catalog/oracle/DSL 运行器、确定性重放与 mutation suite；严禁 runtime 读取 oracle/manifest/registry。
3. 实现 D07 中文三段式 Query、共享访视轴 Journey event/risk marker/source jump/audience validation、最小导出/README 与聚焦/相邻回归。

## Acceptance Checks

- Pre-evaluator integrity follows the frozen first-failure order and produces no medical/priority/risk/Query/Journey output on failure.
- Runtime has no oracle/registry/expected-output reverse dependency; test-only harness executes all 144 cases through runtime and exact-matches the closed DSL oracle, including deterministic replay and mutation failures.
- All frozen typed contracts for unit/range/grade/baseline/trend/CS-NCS/follow-up/organ-pattern/examination/owner/priority/lifecycle are covered.
- Query is natural Chinese with exactly basis/finding/action sentences; PD wording requires accepted typed D04 permission.
- Journey uses the shared visit/time spine, specific medical event/risk labels, reversible source jumps, exact scope/hash equality and internal-term rejection.
- Focused D07, all R4 and R1-R3 adjacent suites pass, plus Ruff/compile/import/export; 8911 stays stopped.
- Workers attach precise file paths, hashes and commands. They do not self-accept; manager and fresh independent verifier own acceptance.

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.

## Final acceptance — 2026-08-14

The final immutable snapshot is accepted for the synthetic/offline D07 boundary. Independent Luna session `019ffdb2-3613-7872-aa8e-47fcbaee88ad` returned `ACCEPT_D07_RUNTIME` after closing Journey/Query target validation, typed project thresholds, materialized `target_ref`, frozen/overlay identity separation and overlay top-level hash consistency. Final gates: D07 challenge matrix `303 passed`, R4 `3657 passed`, adjacent R1/R2/R3 `327/598/339 passed`, generator three-way checks and Ruff passed, 8911 stopped. Authority record: `context/medical_monitoring_r4_d07_runtime_acceptance_record_20260814.md`. Next safe action is the D08 contract freeze; D07 is not product/UI/real-project acceptance.
