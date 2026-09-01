# Execution Context: mm_r7_slice08d_execution_20260830

Created: 2026-08-30 09:31:59 CST
Objective: 按冻结08D v0.1+v0.2合同完成三模式synthetic综合回归、独立oracle、15格确定性、故障恢复及相邻边界证据；不启动服务、不运行真实项目/模型、不触碰医学写作或08C视觉
Task type: `finite_code_task`
Risk: `medium`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.
Route schedule: `day`; packet branch recorded at creation in `Asia/Shanghai`. Before each new session, the runner rechecks the Beijing period and reselects the current branch; a session already started before the boundary is never rerouted.
Effective worker chain: `cursor/default -> google-antigravity/gemini-3.7-flash:high -> mtplx/mtplx-qwen38-27b-optimized-quality:medium -> opencode-go/muse-spark-1.2-contributor:xhigh -> openai-codex/gpt-5.6-luna:max`

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor` -> `pi` / `cursor` / `default`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `context/mm_r7_slice08d_execution_contract_20260830.md`
- `plans/mm_r7_slice08d_execution_assignments_20260830.md`
- `reviews/medical_monitoring_r7_slice08d_three_mode_regression_contract_v0_1_20260830.md`
- `reviews/medical_monitoring_r7_slice08d_three_mode_regression_contract_v0_2_20260830.md` (precedence appendix)
- Current source under `poc/medical_monitoring_ai_native_r7/src/mm_r7/` and directly related tests named in the frozen contract.
- Current product-router test `tests/test_medical_monitoring_r7_product_router.py` and existing 08C frontend contract tests for read/regression only.
- Frozen 08A/08B/08C acceptance records; 08D must preserve the 08B real R5/R6/artifact closure and accepted 08C desktop UI.

Authorized writes are limited to the task-owned test/evidence surfaces and any smallest production correction proven necessary by a failing frozen-contract test, exactly as assigned in `context/mm_r7_slice08d_execution_contract_20260830.md`. Medical-writing, real-study data, UI redesign, services, browser artifacts, and security work are excluded.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.
- Do not start ports 8911/5174 or any app server; do not call real VLM/LLM or read the five real study projects.
- Do not run ego(lite), Playwright, screenshots, or repeat the frozen 08C visual assessment.
- Do not modify medical-writing or broaden into system-security design/testing.
- Use existing stdlib seams and tests first. A production-source edit requires a demonstrated contract failure and must be the smallest coherent correction.

## Work Items

1. 实现冻结20格三模式synthetic矩阵与输入侧独立oracle，必要时仅修复被测试证明的最小连续性/桥接缺陷
2. 实现5种hash seed乘3种优化级别确定性、真实PRAGMA busy_timeout、全故障钩子、CAS/重放/迟到回调恢复覆盖
3. 执行固定相邻回归、公开中文边界、compileall、路径中性、医学写作保护和8911/5174停止证据，形成机器可读清单

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
