# Execution Context: mm_r7_slice09d_implementation_20260831

Created: 2026-08-31 00:08:11 CST
Objective: 按冻结合同 v0.2 实施 R7 Slice-09D synthetic/offline 性能、容量与长任务恢复基线：冻结通用 corpus/generator/input-side oracle/measurement schema/fault matrix，完成最小 stdlib-first runner、确定性/恢复/资源裁决和证据输出。严禁真实项目/模型/浏览器、8911/5174/8984、医学写作、安全专项；不得硬编码疾病/药物/量表/风险/listing 列名或布局。
Task type: `long_horizon_code`
Risk: `medium`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.
Route schedule: `unscheduled`; packet branch recorded at creation in `Asia/Shanghai`. Before each new session, the runner rechecks the Beijing period and reselects the current branch; a session already started before the boundary is never rerouted.
Effective worker chain: `openai-codex/gpt-5.6-luna:max -> codex/gpt-5.6-luna:max`

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor` -> `pi` / `openai-codex` / `gpt-5.6-luna`
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

1. 实现版本化 15-profile synthetic corpus manifest、通用 generator、input-side oracle 与反过拟合静态/mutation guards；只使用 opaque identity，不触碰真实资料，提供 focused tests 与固定 artifacts。
2. 实现 stdlib-first measurement runner/schema：7 workload 基准包、process-cold/warm、calibration、watchdog、资源 guard、raw JSONL/stat summary/capacity statement 与独立 15-cell determinism；不得运行 24 小时全量基准，本执行先完成可验证 T0/T1 bounded proof。
3. 实现 fault/recovery matrix 与中文 DTO 投影验证：中断/cancel/lease/generation/迟到回调/backup/restore/migration/audit/log/resource 边界；复用现有 09A-09C seam，最小改动并完成 R1/R7 相邻回归。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
