# Execution Context: medical_monitoring_r4_d07_artifacts_20260813

Created: 2026-08-13 20:13:52
Objective: Generate the synthetic/offline R4-D07 144-case typed fixture catalog, independent expected-outcome oracle, manifest, closed assertion DSL, registry and deterministic generator exactly from the accepted semantic contract, without writing D07 runtime or touching product, real projects, port 8911 or medical-writing.
Task type: `finite_code_task`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `pi` / `cms-smk` / `deepseek-v4-flash`
- Execution manager: `finite_code_manager_cursor` -> `cursor` / `cursor-cli` / `auto`
- Execution-manager fallback: `Codex takes over finite-code execution management directly`

## Source Of Truth

- `reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md` v0.4, SHA-256 `0b1f42c108ab6d4f5caa11a879cd2233328518e061772f74668cf1afd520fe84`; independent semantic acceptance `runs/codex-subagent_medical_monitoring_r4_d07_contract_20260813_followup3.md`, SHA-256 `467aa75c2714a010eeab825b73d463726590a9fe6c2632e10b5cafb65acbcd63`.
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`, accepted D05/D06 contracts, and the D07 external decision record are read-only adjacency authority.
- D06 artifact files and `tools/generate_d06_challenge_registry.py` are read-only engineering patterns only. D07 clinical cases, expected leaves and rule semantics must come from the D07 contract and must not be copied from D06.
- Current filesystem is authoritative; the workbench is not a Git repository, so record explicit file hashes and checks.

## Authorized Read Paths

- `AGENTS.md`
- the D07 contract/context/semantic review and external decision under `reviews/`, `context/`, `runs/`;
- accepted D05/D06 contracts and the R4 risk coverage matrix;
- `tools/generate_d06_challenge_registry.py` and the three D06 validation JSON files solely for generator/canonicalization conventions.

## Authorized Write Paths

- `tools/generate_d07_challenge_registry.py`
- `reviews/medical_monitoring_r4_d07_typed_fixture_catalog_v1_20260813.json`
- `reviews/medical_monitoring_r4_d07_expected_outcome_oracle_v1_20260813.json`
- `reviews/medical_monitoring_r4_d07_challenge_manifest_registry_v1_20260813.json`
- `tests/test_d07_artifact_generator.py` only if needed for deterministic artifact/schema/hash/static-independence validation; it must not import or implement D07 runtime.
- The execution-module context/plan/review/metrics/prompts/runs/logs already created for this task.

No other source, test, product, medical-writing or generated path is authorized.

## Risk Boundaries

- No D07 runtime/source implementation and no edits to D01-D06 or R1-R3.
- No product/R5/frontend/service/port 8911, real project/data/provider/model execution, or medical-writing access.
- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.

## Work Items

1. Implement a deterministic D07 artifact generator and exact schema/hash/integrity validation, reusing only proven D06 infrastructure patterns without copying D06 clinical semantics.
2. Materialize exactly 144 synthetic D07 typed fixtures and an independently authored exact-leaf oracle covering every matrix row, ownership, scope, medical, lifecycle and Journey boundary.
3. Generate manifest/registry/DSL, run bijection/hash/duplicate/independence/mutation-style static validations, and return hashes plus an auditable handoff; do not implement runtime.

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.

## Acceptance Checks

- Exactly 144 unique cases and complete row distribution `12/16/16/16/14/18/14/12/10/8/8` for IDs `001..144`.
- Catalog contains typed input only, never expected outcomes; oracle contains only bindings and exact medical/trace/source/integrity leaves, never runtime code; manifest/registry provide five-way case-fixture-oracle-manifest-test bijection.
- Canonical JSON, contract semantic hash range, artifact hashes and generator source hash follow v0.4 exactly and reproduce byte-identical outputs on two runs.
- Closed DSL/operators/clauses reject unknown keys, callbacks/code strings, invalid paths, missing/extra leaves and invalid value types.
- Static import/text audit proves D07 runtime is absent and the generator does not derive oracle expected values from runtime or fixture medical branches.
- Mutations cover stale hashes, wrong scope/revision/cutoff/authority/correction/identity, D05 gates/applicability, unit/range/grade/CS-NCS, owner/query/priority/lifecycle/Journey payload/source jump, duplicate substantive inputs and synchronized rehash without authority.
- Generator self-check, focused artifact tests if created, Ruff/compile, JSON parse/hash/bijection/distribution checks pass; port 8911 remains stopped.
- Workers may create artifacts and evidence but may not declare final acceptance. Cursor manager reviews all worker outputs; Codex and a fresh independent verifier own acceptance.
