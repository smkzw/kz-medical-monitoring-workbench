# Execution Context: mm_r7_slice07c1_setup_diff_rules_implementation_20260829

Created: 2026-08-29 00:52:32 CST
Objective: 实施已冻结 R7 Slice-07C-1：仅用 synthetic 数据建立三模式 run options、同模式已发布基线、canonical keyed diff、项目级版本化特殊风险规则和模板到 work-unit 的同源数据合同；不实现 prepare-and-start、结果发布或前端。
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
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- current R7 POC source/tests and the project-scoped R7 product router/tests.
- Synthetic fixtures only; no real-project source is authorized for this slice.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. 领域模块：在 R7 POC 内新增 stdlib-only run-setup 数据合同，定义三模式 options、同模式已发布基线、canonical keyed diff、项目级规则 preview/registry revision、模式模板到 work-unit 的确定性生成；只改 poc/medical_monitoring_ai_native_r7/src/mm_r7 下新模块与必要导出，不改产品 router/前端。
2. 产品 API：在现有 medical_monitoring_r7_product_router 中接入 GET run-setup/options、POST risk-rules/preview、POST/GET risk-rules，复用 canonical project/workspace/authorization/error 约定；只改该 router 及产品路由聚焦测试，不实现 prepare-and-start/结果发布/前端。
3. 验证与证据：补充 R7 synthetic fixture 和 07C-1 端到端确定性测试，覆盖三模式、全量载体增量语义、跨 hash seed、混合模式/未发布/跨项目基线、规则歧义/版本/历史不变、模板分母；只改 R7 tests/evidence/README，不改生产源码或前端。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
