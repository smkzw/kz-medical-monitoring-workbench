# Execution Context: mm_r8_gate2_synthetic_runtime_20260831

Created: 2026-08-31 11:35:40 CST
Objective: 在不访问真实项目、不调用模型、不启动服务或浏览器、不修改医学写作子系统的前提下，实现并验证 R8 G2 synthetic runtime：canonical digest/manifest revision replay、macOS synthetic source_access_profile、以及不占真实端口的一键 start-stop-restart 生命周期演练。
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

1. 设计并实现纯标准库 canonical digest 规范表、synthetic source/output manifest schema、revision chain 与独立 replay；只修改医学监查 deploy 新模块及其专门测试。
2. 设计并实现目标 macOS synthetic shadow-root source_access_profile 证据：读取允许、写入拒绝、写事件可观察、监测失效 not_evaluable；不得对真实来源做写探针。
3. 设计并实现 synthetic/offline one-click 生命周期演练：start-stop-restart/ready/failure/partial/foreign ownership 均由合成 adapter 驱动且绝不绑定 8911/5174/8984；补中文文档与测试。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
