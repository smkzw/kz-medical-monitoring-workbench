# Execution Context: medical_monitoring_r4_d05_postverify_corrective_20260812

Created: 2026-08-12 20:05:14
Objective: 修复并验证R4-D05独立验收发现的三个合同缺口
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

- Frozen contract: `reviews/medical_monitoring_r4_d05_visit_schedule_slice_contract_v1_20260812.md`, SHA-256 `23172cac905b3b152937976a7ee5d7eb895bac274ced7fc40a49b5f7a205921c`.
- Independent verifier report: `runs/conference/medical_monitoring_r4_d05_final_acceptance_20260812/codex_luna_verifier.md` (REJECT with two P1 and one P3 implementation gaps).
- Current D05 source/tests under `poc/medical_monitoring_ai_native_r4`; current filesystem is authoritative.
- Pre-corrective decisive baseline: Worker-03 focused 72 passed twice; D05 323; R4 1308; R2 598; R3 339; 8911 stopped.
- Live relevant hashes before dispatch: projection `4547de907085a03591d70b2295f124e11c8ffa46f06255a1451513e9acd05de4`; projection test `da6bd57c86f6fddaafff86044e523b5ddfca05428c64947fa23231dd7cf4b187`; fixtures `18626fa1447893bf84a5cef778df67b5eac28ade64b7b8cb34e8b576655fd3b7`; matrix test `101e443d8416afbf707fd94fca60a6192880ad9ccac9380c40ad41839b4b67be`; visit_schedule `00ecf4b5c777715417c63d3f84102a90784fa8c0d2877fdaec68696f46e4daff`; contract test `8e4fc830d380a88fa479c56a193bc6f185368cf290eb61a3e72d518285a8942e`.

## Risk Boundaries

- Synthetic/offline only. Do not read real projects, product/UI paths, medical-writing, providers, browsers, databases, or services. Do not start 8911.
- No security design/testing, package installation, credential handling, or external action.
- Worker 01 owns only `visit_schedule_projection.py` and `test_visit_schedule_projection.py`.
- Worker 02 owns only `visit_schedule_fixtures.py` and `test_visit_schedule_challenge_matrix.py`.
- Worker 03 runs after 01/02 and owns only `visit_schedule.py`, `test_visit_schedule_contract.py`, and, only if the projection golden changes, the pinned golden constants in `visit_schedule_fixtures.py` plus the exact corresponding golden assertion in `test_visit_schedule_challenge_matrix.py`.
- All other D01-D04/R1-R3/shared/root/README files are protected and read-only.
- Worker and manager outputs are evidence; Codex owns final acceptance.

## Work Items

1. 修复Journey活动标记planned_visit_key稳定关联并添加版本修订反例
2. 强化116行直接场景声明式期望验证并加入空check_fn负控
3. 使Journey根payload_hash覆盖activity/pending/out-of-cutoff标记并验证篡改敏感性

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
