# Execution Context: mm_r7_slice09c_contract_20260830

Created: 2026-08-30 19:41:18 CST
Objective: 在 Slice-09A/09B 已接受边界上，冻结 R7 Slice-09C synthetic/offline 业务审计核验、恢复事件对账与技术日志轮转/保留合同；面向中文资深医学监察员提供记录完整/发现异常/需重新恢复的最小产品语义，不暴露路径表名或内部标识，不进入风险/Journey，不触碰真实项目、模型、浏览器或医学写作。
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

- `context/medical_monitoring_r7_slice08_overall_review_and_slice09_plan_20260830.md`
- `context/medical_monitoring_ai_native_rearchitecture_audit_20260809_context.md`（D16）
- Slice-09A/09B frozen contracts and acceptance records under `reviews/` and `context/`
- Current R1/R7 source and tests under `poc/medical_monitoring_ai_native_r1` and `poc/medical_monitoring_ai_native_r7`
- `services/api/app/medical_monitoring_r7_product_router.py` and its tests
- Current filesystem is authoritative; worker reports are evidence inputs, not authority.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. 只读审查 R1-R7 当前业务审计、事件链、principal、hash-chain、backup/migration/continuity/publication 现状与缺口，提出唯一权威链、核验边界、篡改检测、跨备份/恢复/迁移对账和中文结果合同。
2. 只读审查 09A/09B ledger、rollback/retained_for_triage、startup recovery 与产品路由，提出 09C 项目级核验状态机、幂等/恢复、来源-运行-发布-连续性-恢复事件闭包及 P0-P4 故障注入矩阵。
3. 只读审查当前日志/缓存/运行目录和本地单用户运行约束，提出 stdlib-first 技术日志容量/期限轮转、写失败降级、活动文件/归档/清理边界、中文用户投影和 deterministic acceptance matrix；技术日志不得承担医学事实或业务审计证明。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
