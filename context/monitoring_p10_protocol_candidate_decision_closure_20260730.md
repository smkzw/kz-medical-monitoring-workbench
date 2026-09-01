# 医学监查 P10：方案监查准备候选确认闭环

日期：2026-07-30  
状态：后端独立切片实现、聚焦回归与相邻回归通过

## 1. 目标

将既有“方案监查准备”候选审核从只读状态补全为可执行闭环：

1. 医学经理对候选执行“接受”或“驳回”，该动作本身就是候选层面的用户决定；
2. 接受后基于冻结候选及真实方案证据，在既有方案事实仓中幂等形成可审阅事实草稿；
3. 驳回后不创建事实、不生成规则；
4. 不把 AI 候选自动发布为正式规则；
5. 清楚返回后续“规则模板审阅 → 规则包草稿 → 影子验证 → 发布”链路；
6. 全流程不出现“待医学批准”或对同一候选进行二次批准的语义。

## 2. 复用边界

本切片没有新建平行事实库、规则库或风险库：

- 候选决定继续写入既有 `MonitoringAiRepository`；
- 可审阅方案事实继续写入既有 `MonitoringProtocolRuleRepository`；
- 候选到事实的投影复用
  `MonitoringRuleAuthoringService.adopt_ai_candidate()`；
- 后续确定性规则编制、规则包草稿、规则确认、影子验证和发布继续复用既有状态机。

没有新增外部组件或依赖。现有仓储与状态机已经覆盖所需能力，因此本轮不重复进行外部
工具选型，也不引入新的持久化方案。

## 3. API 合同

```text
POST /api/projects/{project_id}/modules/medical-monitoring/
protocol-preparation/protocol-versions/{protocol_version_id}/
candidates/{candidate_id}/decision
```

请求核心字段：

- `decision`：`accepted` 或 `rejected`；
- `actor`、`reason`；
- `expected_input_revision_sha256`：用户当前看到的冻结候选输入版本；
- `expected_source_revision`：用户当前看到的方案准备来源修订；
- 接受时可提供 `proposed_fact_type`、`fact_key`、`title`、`applicability`。

事实类型处理：

- 主题只有一种事实类型时由后端自动采用；
- 主题含多种真实语义时，调用方必须从该主题的 `allowed_fact_types` 中选择；
- 不允许把试验药物条款误投影为 CM 条款，反之亦然；
- 状态接口已返回每个主题的 `allowed_fact_types`，不要求调用方猜测内部枚举。

## 4. 冻结身份与来源漂移门

决定写入前必须同时通过：

1. 方案版本属于当前项目、状态为 `confirmed`；
2. Source Registry entry 仍属于医学监查、仍为 protocol、解析可用；
3. 当前 entry 内容哈希仍与已确认方案版本内容哈希一致；
4. 候选所属作业已完成，任务类型为 `protocol_clause_structuring`；
5. 作业输入 workflow、protocol version、topic 和 source revision 完整且一致；
6. 请求的 input revision 与 source revision 与冻结作业完全一致；
7. 候选 evidence 必须逐条与冻结 evidence packet 的
   `source entry/hash/locator/quote` 完全一致；
8. 候选及 evidence 的 input revision 必须与作业一致。

任一条件不满足均在候选决定写入前失败关闭。数据缺口主题没有候选，因此不能进入决定
API，也不会生成替代事实。

## 5. CAS、幂等与故障恢复

候选状态和方案事实位于两个既有 SQLite 持久化边界，系统不伪称存在跨库原子事务。
采用以下小型 saga：

1. 写入前完成来源、候选、事实类型、事实键、标题和 applicability 全量预检；
2. 候选从 `proposed` 迁移为 `accepted/rejected` 时使用
   `input_revision_sha256` CAS；
3. 同一候选重复提交相同决定时返回幂等复用；
4. 同一候选提交相反决定时返回 409，不覆盖先前决定；
5. 接受后的事实 revision 由候选快照、事实键、事实类型和真实来源确定性生成；
6. 若进程在“候选已接受、事实尚未写入”之间中断，同一接受请求会复用候选决定并补写
   唯一事实草稿；
7. 并发事实写入通过既有 `store_fact()` 不可变身份检查收敛为同一 revision；
8. 不同事实类型、事实键或来源 lineage 试图复用同一候选时返回冲突。

## 6. 事实草稿血缘

接受后形成的 `ProtocolFact` 保留：

- 完整冻结候选；
- protocol version ID 与版本标签；
- source entry ID 与内容 SHA-256；
- source revision 与 candidate input revision；
- 去除可变状态后的 candidate snapshot SHA-256；
- 原始方案 quote 与 locator；
- `evidence_source_types=project_protocol_original`；
- `fact_adoption_status=adopted_as_project_fact_draft`；
- `adoption_basis=medical_manager_explicit_selection`。

事实内部状态仍使用既有 `ai_candidate`，表示“尚未补齐确定性规则模板的事实草稿”；
对外工作流状态明确返回 `user_confirmed_fact_draft`。它不表示还要批准候选。

## 7. 后续动作

接受响应返回：

1. `review_rule_template_and_compile`：审阅和补齐确定性规则模板；
2. `create_rule_pack_draft`；
3. `confirm_rule`；
4. `shadow_validation`；
5. `publish_rule_pack`。

第 1 步是规则逻辑审阅，不是再次批准同一 AI 候选。只有完成既有规则确认、影子验证和
规则包发布门后，规则才可成为正式运行规则。

## 8. 文件改动

- `services/api/app/monitoring_protocol_preparation_service.py`
  - 新增冻结候选预检、决定 CAS、同决定恢复、事实投影和下一动作响应；
  - 状态主题新增 `allowed_fact_types`。
- `services/api/app/monitoring_protocol_preparation_router.py`
  - 新增严格请求模型和候选决定 API。
- `services/api/app/monitoring_rule_authoring_service.py`
  - `adopt_ai_candidate()` 新增可选 `adoption_context`，保持旧调用兼容；
  - 来源或冻结上下文修订时沿用既有 supersede lineage。
- `tests/test_monitoring_protocol_preparation.py`
  - 增加接受、驳回、幂等恢复、相反决定冲突、来源漂移、事实类型边界和 API 测试。

明确未修改：

- `frontend/`
- `services/api/app/main.py`
- 医学写作
- 字段映射
- daily run
- 风险导出
- 任何真实运行数据库

## 9. 验证

```text
pytest:
81 passed
```

覆盖方案准备、规则编制、AI repository/API、方案规则 API、仓储加固、审阅边界和共享
事实投影。

```text
ruff:
All checks passed
```

对本轮新增/主要修改的方案准备 service、router 和专属测试执行。
`monitoring_rule_authoring_service.py` 全文件仍有本轮之前的 Ruff 基线项；本轮新增
`adoption_context` 代码经语法与测试验证，未为清理旧基线进行无关重排。

```text
py_compile:
passed
```

## 10. 残余边界

1. 当前本地 API 进程承载真实独立 AI 队列；为避免无必要重启打断队列，本切片没有重启
   运行进程。下次受控 API 重启后新路由自动生效，不需要修改 `main.py`。
2. 多事实类型主题仍需要调用方选择准确事实类型；后端已返回允许列表并严格限制边界。
   本轮没有改变已排队独立 AI 作业的输出 schema 或 prompt version，避免使真实作业
   身份漂移。
3. 本切片证明的是后端闭环和测试临时库行为；真实独立 AI 候选进入
   `candidate_review` 后，还需按原计划做真实 quote/结构化内容一致性与浏览器审核。

