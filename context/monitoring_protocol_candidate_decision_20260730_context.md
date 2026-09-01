# Task Context: monitoring_protocol_candidate_decision_20260730

Created: 2026-07-30 04:01:51
Objective: 实现医学监查方案准备候选的医学经理接受/驳回闭环，基于冻结候选和真实来源证据幂等形成可审阅事实或规则草稿，并提供来源漂移与CAS保护
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/monitoring_p10_protocol_preparation_orchestration_20260730.md`
- `context/monitoring_p10_protocol_preparation_frontend_20260730.md`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `services/api/app/monitoring_protocol_preparation_router.py`
- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_rule_authoring_service.py`
- `services/api/app/monitoring_protocol_rule_repository.py`
- `services/api/app/monitoring_protocol_rules.py`
- 对应 `tests/test_monitoring_protocol_preparation.py` 与规则编制测试

## Scope

- In scope:
  - 方案准备候选接受/驳回专用 API；
  - 候选、作业输入、方案版本、来源 entry/hash、quote/locator 的冻结身份复核；
  - 候选决定 CAS、同决定重试幂等、相反决定冲突；
  - 接受后复用现有方案事实仓形成可审阅事实草稿；
  - 返回规则模板审阅、规则包草稿、影子验证、发布的下一动作链；
  - 聚焦测试、相邻规则编制回归和 durable record。
- Out of scope:
  - 前端、`main.py`、医学写作、字段映射、daily run、风险导出；
  - 候选接受后自动确认确定性规则、自动建规则包、自动影子验证或发布；
  - 为数据缺口生成替代条款；
  - 新建平行事实库、规则库或风险库。

## Success Criteria

- 只有属于当前项目、当前已确认方案版本及方案准备 workflow 的已完成候选可决定。
- 请求必须携带候选输入 revision 与方案准备 source revision；任一漂移均在写入前失败关闭。
- 驳回只记录用户决定，不创建事实或规则。
- 接受后以冻结候选及真实原文证据幂等创建现有 `ProtocolFact` 草稿；重试不重复创建。
- 并发同决定可恢复；相反决定、不同事实类型或事实键复用返回 409。
- 响应不出现“待医学批准”，明确候选决定已经完成，并指出后续是规则模板审阅而非再次批准候选。
- 不发布正式规则；专属测试、规则编制相邻回归、Ruff/py_compile 通过。

## Risk Boundaries

- 本任务已获用户授权直接编辑共享工作区中的后端文件与测试。
- 不直接读写运行数据库；只通过 repository/service 合同写入测试临时库。
- AI 候选状态库与方案事实库是两个持久化边界，不能提供跨库原子事务；
  因此采用“写前完整预检、候选决定 CAS、事实投影确定性幂等、失败后同请求恢复”的
  小型 saga，不伪称跨库原子。
- 不触碰用户明确排除的文件和子系统。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-30 04:01:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-30: 完成现状核对。现有通用候选 decision 具备输入 revision CAS；
  `MonitoringRuleAuthoringService.adopt_ai_candidate()` 已能将已接受候选投影为
  可审阅 `ProtocolFact` 草稿并保持 quote/locator/hash lineage；缺口是二者尚未
  形成方案准备专用、来源漂移受控、重试幂等的一体化 API。
- 2026-07-30: 实现专用决定 API、冻结来源复核、同决定幂等、相反决定冲突和
  接受后事实草稿投影；补充“候选已接受但事实未写入”的恢复用例。专属及相邻
  回归 81 项通过，新增方案准备文件 Ruff 与相关文件 py_compile 通过。下一步仅为
  真实独立 AI 候选完成后的内容一致性与浏览器 LOOP，不属于本后端切片的完成条件。
