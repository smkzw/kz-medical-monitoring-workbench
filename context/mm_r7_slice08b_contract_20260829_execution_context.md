# Execution Context: mm_r7_slice08b_contract_20260829

Created: 2026-08-29 15:56:39 CST
Objective: 冻结R7 Slice-08B真实R5 authority、R6 ModeOutput子项与publication artifact成员/字节校验的最窄实现合同；不得修改产品源码、启动服务或真实项目
Task type: `finite_code_task`
Risk: `medium`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.
Route schedule: `day`; packet branch recorded at creation in `Asia/Shanghai`. Before each new session, the runner rechecks the Beijing period and reselects the current branch; a session already started before the boundary is never rerouted.
Effective worker chain: `cursor/auto -> google-antigravity/gemini-3.7-flash:high -> mtplx/mtplx-qwen38-27b-optimized-quality:medium -> opencode-go/muse-spark-1.2-contributor:xhigh -> openai-codex/gpt-5.6-luna:max`

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor` -> `pi` / `cursor` / `auto`
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

1. 核对现有R5PublicationAuthorityInputAssembler/R5AuthorityPacket的身份、摘要、成员和项目运行边界，提出只复用不重建的桥接合同
2. 核对R6 ModeOutput三模式结构、validate_mode_output与可独立沿用子项，定义canonical子项摘要、禁止整包/页面沿用与失败关闭条件
3. 核对R7 ResultPublication/continuity registry现有schema，定义最小additive artifact member清单、授权根路径下真实字节SHA-256复核、CAS/重放/迁移测试矩阵及08B非目标

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
