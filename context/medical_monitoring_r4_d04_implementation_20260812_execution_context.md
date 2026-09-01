# Execution Context: medical_monitoring_r4_d04_implementation_20260812

Created: 2026-08-12 01:41:45
Objective: 依据已冻结D04合同实现入排、方案要求与潜在方案偏离的合成离线纵切，并完成隔离回归
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

- Frozen contract: `reviews/medical_monitoring_r4_d04_protocol_pd_slice_contract_v1_20260812.md`, final SHA-256 `6d0a7ee2fe507555f68f7a719c60dfa2cc92f995fcaf2c4a3825bbcb3bc6d6b5`.
- Frozen R4 common contract and matrix: `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`.
- Adjacent accepted implementation patterns: `poc/medical_monitoring_ai_native_r4/src/mm_r4/{contracts,coverage,lifecycle,cm,cm_projection,cm_fixtures,ip,ip_projection,ip_fixtures}.py` and current R4 tests.
- Frozen dependencies are read-only: `poc/medical_monitoring_ai_native_r1`, `medical_monitoring_ai_native_r2`, `medical_monitoring_ai_native_r3`.
- Current filesystem is authoritative. The already frozen D04 contract contains the bounded official-source discovery decision; this implementation task must not reopen architecture or substitute new protocol rules.

## Risk Boundaries

- Write only `poc/medical_monitoring_ai_native_r4/` plus runner-owned task evidence under the declared context/plan/prompt/run/log/review/metrics paths.
- No production writes and no edits to R1/R2/R3, R5 UI, services, real projects, medical-writing subsystem, or any path outside this workbench.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.
- Use only synthetic/offline fixtures. Do not start any service; TCP 8911 must remain stopped.
- Do not implement security design/testing; the user has explicitly excluded that track.
- Do not hardcode a study name, real subject, fixed universal threshold, fixed listing layout, visit window or medication rule.
- Shared files are single-owner: worker 01 owns `contracts.py` and `lifecycle.py`; worker 03 owns root `__init__.py` and `README.md`. No other worker may edit those files.

## Work Items

1. 实现R4共享候选关键性读取与生命周期高风险持久化钩子，单一所有者修改共享文件
2. 实现D04 protocol领域模型、组合表达式、适用性门、证据评估、中文Query与覆盖缺口通知
3. 实现Journey投影、合成fixtures、公开导出与83项挑战测试，并完成D01-D03/R2/R3相邻回归

## Sequence And Allowed Paths

Workers run serially because work item 02 consumes the shared lifecycle surface and work item 03 consumes the domain model. Do not dispatch them concurrently into the shared filesystem.

1. Worker 01 may edit only `src/mm_r4/contracts.py`, `src/mm_r4/lifecycle.py`, `tests/test_shared_domain_protocol.py`, and `tests/test_lifecycle_projection.py`.
2. Worker 02 may add/edit only `src/mm_r4/protocol.py` and `tests/test_protocol_slice.py`.
3. Worker 03 may add/edit only `src/mm_r4/protocol_projection.py`, `src/mm_r4/protocol_fixtures.py`, `tests/test_protocol_projection.py`, `tests/test_protocol_challenge_matrix.py`, and may update `src/mm_r4/__init__.py` plus `README.md` as their single owner for this task.
4. The manager is read-only unless Codex sends a same-session targeted remediation after reviewing its report.

## Acceptance Checks

- Frozen SHA is unchanged; all 83 contract challenges have a deterministic D04 test or an explicit adjacent accepted-test mapping.
- Focused flag/lifecycle, protocol slice, projection and challenge tests pass.
- Full R4 suite passes; D04 pre-baselines R2=598 and R3=339 pass without behavioral regression; D01-D03 adjacent tests pass.
- Ruff, compileall, public import/object identity and deterministic payload/hash checks pass.
- D05 is only a synthetic producer stub, not an accepted implementation.
- Port 8911 is stopped before and after every stage.

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
