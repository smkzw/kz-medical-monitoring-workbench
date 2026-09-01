# Execution Context: medical_monitoring_r4_d08_artifacts_20260814

Created: 2026-08-14 13:16:08
Objective: 以已双审放行且哈希固定的 D08 v0.5 合同为唯一语义输入，构建不少于200条 synthetic/offline typed fixture catalog、独立 expected-outcome oracle、五列双射 manifest registry、确定性只验证装配 generator 及负向变异测试；不得实现 runtime、启动8911、读取真实项目或触碰产品/医学写作
Task type: `finite_code_task`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `pi` / `cms-smk` / `deepseek-v4-flash`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_6_20260814.md`, exact file/full-NFC-LF semantic SHA-256 `ff3d3a1bd9844ac8808ca7f9ada1466317763eb883e60d825f15bb3015ac4d64`.
- `context/medical_monitoring_r4_d08_draft_artifact_build_acceptance_record_20260814.md`, the round-5 semantic reviews and round-6 single-delta reviews are the limited artifact-build authorization; they do not authorize runtime.
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` and accepted D01-D07 contracts are read-only adjacency authority.
- D07 catalog/oracle/registry, `tools/generate_d07_challenge_registry.py`, and `tests/test_d07_artifact_generator.py` are read-only engineering patterns. D08 typed inputs, outcomes and clinical semantics must be derived from D08 v0.5, never copied from D07.
- The current filesystem is authoritative; this workbench is not a Git repository, so use explicit file hashes and before/after checks.

## Authorized Read Paths

- `AGENTS.md`, this execution context and plan;
- the D08 v0.5 contract, artifact-build acceptance record, round-5 reports and R4 risk coverage matrix;
- accepted D01-D07 contracts only to validate owner/consumer shape;
- D07 generator/test/catalog/oracle/registry solely for canonicalization, schema, integrity and deterministic-build patterns.

## Authorized Write Paths

- `tools/generate_d08_challenge_registry.py`;
- `reviews/medical_monitoring_r4_d08_typed_fixture_catalog_v1_20260814.json`;
- `reviews/medical_monitoring_r4_d08_expected_outcome_oracle_v1_20260814.json`;
- `reviews/medical_monitoring_r4_d08_challenge_manifest_registry_v1_20260814.json`;
- `tests/test_d08_artifact_generator.py`;
- the execution-module context/plan/review/metrics/prompts/runs/logs created for this task.

No other source, test, product, medical-writing or generated path is authorized.

## Risk Boundaries

- No production writes.
- No D08 runtime/source implementation and no edits to D01-D07 or R1-R3.
- No product/R5/frontend/service/port 8911, real project/data/provider/model execution, or medical-writing access.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. 设计并实现 deterministic D08 artifact generator、exact schema/hash/semantic binding 与 replay validation，只复用 D07 工程模式不复制临床语义
2. 物化不少于200条 D08 typed synthetic fixtures，覆盖合同§12分区、owner zero-risk、cutoff、temporal、identity、propagation、visibility、fanout 与 anti-overfit
3. 独立物化 exact expected-outcome oracle、五列双射 registry/manifest/assertion DSL，并实现负向变异与双遍字节一致性验证

## Ordered Execution

Workers run sequentially to avoid shared-file races: worker_02 first materializes the typed catalog and may create the initial D08 generator scaffold; worker_03 then adds an independently persisted oracle and registry/DSL assembly; worker_01 finally consolidates the generator, exact validations and focused tests. A later worker may repair an earlier authorized artifact only when the contract and deterministic checks require it, and must record the change.

## Acceptance Checks

- At least 200 unique cases, exact consecutive IDs and §12 partition floors; five D08-owned classes each cover all five dispositions plus counterevidence/hidden/FP/FN; D01-D07 consume-only cases assert zero D08 medical risk/Query.
- Catalog contains typed input only; oracle contains exact expected outcomes and leaves but no runtime code; registry has unique five-column case/fixture/oracle/manifest/test bijection and no orphan.
- Exact catalog/case key sets from v0.5; typed gate signals include routing ambiguity, cutoff boundary, identity fanout and time-missing; waiver states are exactly `full_set/explicit_empty/missing`.
- Required cutoff, temporal direction, covered-zero/uncovered, n-ary, hidden, correction/propagation, fanout and anti-overfit cases are materialized; same substantive input cannot map to conflicting outcomes.
- Generator pins contract full/semantic hash and all artifact hashes, validates canonical JSON and schema before assembly, never derives expected outcomes from fixture branches or runtime, and reproduces byte-identical artifacts twice.
- Mutations for stale/resealed hashes, missing/extra keys, wrong scope/cutoff/owner/grain/L1, waiver fourth state, contains-direction flip, time-missing priority, hidden leakage, bijection drift and oracle/runtime coupling fail closed.
- Generator self-check, focused pytest, compile/Ruff and independent JSON/hash/distribution checks pass; 8911 remains stopped.

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.

## Final Acceptance Update — 2026-08-14

Status: `ACCEPT_D08_CONTRACT`. Authoritative final record:
`context/medical_monitoring_r4_d08_contract_final_acceptance_20260814.md`.
The final independent verifier accepted the immutable snapshot only after two
REVISE rounds and a complete 16,881-leaf reconstruction/mutation gate. Runtime
is the next separately contracted stage; UI, services and real projects remain
blocked.
