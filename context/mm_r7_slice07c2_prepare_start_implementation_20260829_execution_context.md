# Execution Context: mm_r7_slice07c2_prepare_start_implementation_20260829

Created: 2026-08-29 02:06:14 CST
Objective: 实现冻结的 R7 Slice-07C-2 synthetic/offline 原子 prepare-and-start、public run history、幂等与长等待恢复；不实现发布、result-entry、前端或真实项目。
Task type: `finite_code_task`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.
Route schedule: `night`; resolved once at packet creation in `Asia/Shanghai`.
Effective worker chain: `codebuddy-cli/glm-5.3-flash:max -> mtplx/mtplx-qwen38-27b-optimized-quality:medium -> openai-codex/gpt-5.6-luna:xhigh`

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor` -> `codebuddy` / `codebuddy-cli` / `glm-5.3-flash`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `reviews/medical_monitoring_r7_slice07c_three_mode_product_loop_contract_v0_2_20260829.md`
- `reviews/medical_monitoring_r7_slice07c2_prepare_start_contract_v0_1_20260829.md`
- accepted Slice-07C-1 source, tests and acceptance record in the current filesystem.
- Synthetic inputs only; no real-project paths are authorized.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. 新增 stdlib-only launch registry：项目级 SQLite busy_timeout/显式关闭、规范请求指纹、public token、同 key 重放/冲突、状态与有界历史；只改 R7 POC 新模块及必要导出。
2. 在产品 R7 router 接入 POST /runs/prepare-and-start 与 GET /runs：服务端解析 snapshot/baseline/rule tokens，生成 manifest，绑定、准备、启动并公开中文历史；只改 router 与产品路由测试。
3. 补充 synthetic 多候选锁库前 baseline、三模式/幂等/跨项目/过期 token/start 失败恢复/确定性测试、evidence receipt 与 README；只改 R7 tests/evidence/README，不改产品源码。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
