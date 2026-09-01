# Execution Context: mm_r6_runtime_slice_04_20260828

Created: 2026-08-28 00:04:12
Objective: 按 context/medical_monitoring_r6_runtime_slice_04_contract_20260828.md 实现 synthetic/offline 三模式 ModeContract、daily ModeOutput 与结构化 Query 草稿，严格限制允许路径，保护既有 slices 与医学写作，保持 8911/5174 停止。
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

1. 实现三模式合同与 Run 门：不可变 ModeContract、execution basis、entry conditions、cutoff/source revision、carry-forward、fixed-total 与 silent conversion 失败关闭。
2. 实现通用 ModeOutput 和 daily 四输出，重点结构化 affected Query draft 的依据+发现+行动项、中文确定性投影、证据/身份绑定与未发送未关闭边界。
3. 独立验证模式/输出/Query/tamper/identity/cutoff/producer/authority/数字一致性，跑 normal/-O/-OO×3 hash seeds、全 POC、医学写作边界和端口停止，生成 receipt。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
