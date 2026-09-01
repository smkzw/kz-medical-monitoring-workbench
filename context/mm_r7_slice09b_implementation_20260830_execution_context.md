# Execution Context: mm_r7_slice09b_implementation_20260830

Created: 2026-08-30 13:58:09 CST
Objective: 按冻结的 R7 Slice-09B v0.1+v0.2 合同实施 synthetic/offline 项目格式只读识别、staging-only 升级、失败恢复和中文产品投影；保护医学写作与真实项目，保持 8911/5174 停止。
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

1. 实现显式 schema manifest、只读 ProjectSchemaInspector、旧/当前/未知/损坏分类和 synthetic legacy fixture/单元测试；普通 constructor 对 legacy/unknown/malformed fail closed 且零字节改动。
2. 实现 migration plan、根级 ledger 扩展、sibling staging、R1 4/5到6 与 launch v1/v2/v3到v4 的 marker-last staged migration、目录切换/回滚、崩溃恢复与故障注入测试，复用 09A 维护门/指纹/闭包原语。
3. 实现最小中文 ProjectOpen/Upgrade progress/result DTO 与产品路由、legacy 持久化只读 facade/写阻断，并建立 DTO 禁用字段、确定性、09A/R1/R7 相邻回归和边界证据。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
