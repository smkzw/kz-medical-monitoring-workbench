# Execution Context: mm_r7_slice08c_projection_visual_contract_20260829

Created: 2026-08-29 17:38:08 CST
Objective: 基于已接受08A/08B事实、当前R5/R7前端、Patient Journey与受试者流向看板，形成并冻结Slice-08C中文跨轮连续性投影、交互与ego(lite)视觉验收合同；合同阶段只读源码和证据，不改产品、不启动服务/模型/真实项目
Task type: `visual_report_structure`
Risk: `medium`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.
Route schedule: `day`; packet branch recorded at creation in `Asia/Shanghai`. Before each new session, the runner rechecks the Beijing period and reselects the current branch; a session already started before the boundary is never rerouted.
Effective worker chain: `kimi-code/k3-256k:low -> grok-build/grok-4.6:medium -> cursor/auto -> openai-codex/gpt-5.6-luna:max`

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `visual_executor` -> `pi` / `kimi-code` / `k3-256k`
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

1. 审阅08A/08B公开事实与产品DTO，提出最小连续性公开投影字段、中文闭集、排序/筛选与fail-closed合同，不新增风险生命周期或医学推导
2. 审阅当前R5/R7项目中心风险Journey来源下钻和访视轴，提出项目→中心→风险→Journey→来源的同一身份路由、比较交互、事件/风险图标及详情抽屉合同
3. 结合外部设计研究与康哲视觉基线，提出1280/1440/1920信息层级、字体/间距/配色/表格/图表/动效/键盘/焦点/reduced-motion及ego(lite)视觉验收矩阵和非目标

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
