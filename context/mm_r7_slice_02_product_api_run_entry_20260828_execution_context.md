# Execution Context: mm_r7_slice_02_product_api_run_entry_20260828

Created: 2026-08-28 05:01:21
Objective: 按冻结合同实现 R7 Slice-02 隔离产品 API/运行入口：显式 workspace bootstrap、四层 ExecutionProfile、三模式不可变 Run 绑定与稳定中文错误；保持产品主应用、真实项目、端口和医学写作不变
Task type: `finite_code_task`
Risk: `medium`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `cursor` / `cursor-cli` / `auto`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- TODO: Codex must add authoritative source files, screenshots, datasets, or URLs before dispatch.
- Do not add production paths without explicit Codex authorization.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. 实现 run_entry.py：显式幂等 bootstrap、四层 scope 解析、effective profile 冻结、Run bind/replay/conflict 与公共投影；只改 worker_01 允许路径
2. 实现 api.py：最小 FastAPI router、严格 DTO、稳定 code+中文 message、无凭据值泄漏；只改 worker_02 允许路径
3. 实现聚焦测试、确定性/重开/失败关闭矩阵、receipt 与 README；只改 worker_03 允许路径

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
