# 医学监查 P10：已确认方案事实草稿到确定性规则模板建议后端闭环

## 1. 本切片目标

在不触碰医学写作、医学监查前端、真实运行数据库和当前候选决定前端的前提下，
完成以下后端闭环：

1. 医学经理已经从方案条款结构化候选中明确选择一条事实草稿；
2. 产品独立 AI 只基于该事实原文、当前激活的不可变字段映射、能力快照和闭合角色，
   提出 1 至 3 个具有实质差异的确定性规则模板建议；
3. 服务端在候选可见前用生产确定性编译器真实预编译；
4. 用户选择建议时即确认该事实与规则模板，复用既有正式
   `confirm_fact_and_compile`，不增加“待医学批准”；
5. 本闭环不创建规则包、不开始影子验证、不发布。

## 2. 不可突破边界

- 产品运行只复用 `MonitoringAiRepository` / `MonitoringAiService` 的持久队列、
  输入修订、运行配置、模型身份、租约和失败恢复；没有 Codex、测试模型或会商模型
  产品依赖。
- AI 输入中的事实必须是用户已明确选择、仍可追溯到已接受方案候选的事实草稿。
  事实原文、定位、方案版本、来源文件哈希任一不一致即失败关闭。
- AI 只允许使用当前事实类型对应的安全规则族，以及当前激活 mapping 中的闭合角色。
  `rule_role` 由服务端根据闭合 `role_concept_id` 确定性生成，AI 必须原样引用；
  不能把合法字段绑定为其他医学语义。
- AI 只输出字段名和域；字段血缘由服务端从不可变 mapping 注入。
- `study_treatment_regimen` 等没有安全确定性规则族的事实返回
  `manual_review/no_safe_deterministic_family`，不调用 AI、不硬编。
- CM 仅表示非试验用药或治疗。试验药物给药、剂量调整、暂停、恢复、停药、
  发放、回收和依从性必须继续使用独立 IP 域及角色。
- 用户选择是正式决定。接受后原事实草稿转为 `superseded`，新事实为
  `medically_confirmed`；同一选择可幂等重放，相反决定冲突。
- API 只返回事实、mapping 版本、候选摘要、确定性字段绑定、选择结果和下一步；
  provider、model、prompt、job 内部键只保留在后端审计。

## 3. 实现摘要

### 3.1 AI 合同与持久队列

- 新增 `rule_template_recommendation` 任务类型及
  `deterministic_rule_template` 候选类型。
- 输入修订增加事实 revision 锚点，并继续绑定方案版本、mapping revision 和精确
  source/hash。
- 新任务复用既有产品 AI 运行绑定、持久作业、受控 JSON 修复、租约、重试、
  模型身份校验和 stale-input 检查。
- 提示词明确：事实已经由用户确认选择，不得改写或补造；只能使用允许的规则族、
  事实类型、闭合角色；每个候选必须同时引用事实证据和 mapping 证据。

### 3.2 候选可见前的失败关闭

- 服务端把 AI 的字段绑定与当前 mapping 的 `(domain, source_field)` 精确匹配。
- DSL 字段角色必须等于服务端提供的 `rule_role`，防止字段存在但语义错绑。
- 服务端注入 `raw_listing_field` lineage，并把临时事实状态设为
  `medically_confirmed` 后调用真实 `compile_monitoring_rule_template`。
- 编译后再次按冻结 capability snapshot 校验所需能力。
- 无效 DSL 只进入既有的一次受控修复；修复后仍失败则作业
  `invalid_ai_output`，不保存、不展示候选。
- 1 至 3 个候选按最终物化 DSL 哈希去重；仅标题或措辞差异不能形成多个候选。

### 3.3 正式选择与 CAS

- 新增独立 recommendation service/router，未扩写方案准备 service。
- 接受/驳回使用仓库级互斥、幂等决定：
  - 同一决定重试复用；
  - 一组候选最多接受一个；
  - 相反决定冲突；
  - 接受一个候选时其他仍为 proposed 的同组候选被原子驳回。
- 接受后复用 `confirm_fact_and_compile` 再次编译并 CAS 转换事实状态。
- 若事实状态并发变化，返回 409；已经记录的同一接受决定可在条件恢复后重试。
- 对已经成功选择的请求，幂等重放仍重新核对实时方案来源哈希、方案版本、mapping
  revision、mapping 内容哈希和 capability snapshot，漂移即停止。

### 3.4 API

- `POST .../rule-template-recommendations/facts/{fact_revision_id}/start`
- `GET .../rule-template-recommendations/facts/{fact_revision_id}/status`
- `POST .../rule-template-recommendations/facts/{fact_revision_id}/candidates/{candidate_id}/decision`

路由已接入应用装配，但本切片没有重启或修改当前真实运行态。

## 4. 关键审阅发现与修复

1. 映射能力快照是 dataclass，通用 capability guard 接收公开字典快照。初版直接传入
   dataclass 会把全部能力误判为缺失。现统一使用 `to_dict()` 后校验。
2. 仅验证字段存在仍可能产生“日期字段绑定为术语角色”的可编译错误。现增加
   服务端确定性 `rule_role`，AI 角色键必须与其完全一致。
3. active mapping 内容哈希不能只信任状态表。现对不可变 revision 重新计算内容哈希，
   与 activation snapshot 不一致即失败关闭。
4. 已确认选择的幂等重放不能绕过实时源文件检查。事实校验新增仅供重放使用的
   `allow_superseded`，仍要求原接受候选、来源原文、定位、方案版本和实时文件哈希一致。
5. 集成审阅怀疑 manual transition 分支重复传递错误消息。当前源码没有重复参数；
   新增了候选生成后 capability 转为 blocked 的真实分支回归，确认返回业务 409，
   不会发生 `TypeError`。

## 5. 变更文件

- `services/api/app/monitoring_ai_contracts.py`
- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_capability_guard.py`
- `services/api/app/monitoring_rule_templates.py`
- `services/api/app/monitoring_rule_authoring_service.py`
- `services/api/app/monitoring_rule_template_recommendation_service.py`（新增）
- `services/api/app/monitoring_rule_template_recommendation_router.py`（新增）
- `services/api/app/main.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_rule_template_recommendation.py`（新增）

工作区同时存在其他字段映射和方案准备文件的并发修改；本切片未修改、未回退这些改动。
工作区不是 Git 仓库，因此以上清单及本文件记录代替 Git diff 边界。

## 6. 验证

### 6.1 聚焦闭环

`15 passed`

覆盖：

- 可编译候选在可见前完成真实预编译；
- 新任务映射到既有产品 AI gateway 合同；
- 无支持 family 不创建 AI 作业；
- mapping capability blocked 不创建 AI 作业；
- 候选产生后能力转为 manual review 时 `decide` 返回业务 409；
- 无效 AI DSL 经一次受控修复后仍失败且没有候选；
- 方案来源哈希漂移失败关闭；
- mapping 内容哈希漂移在候选可见前失败关闭；
- 接受选择 CAS、幂等和相反决定冲突；
- 驳回选择幂等和反向接受冲突；
- 不创建规则包、不影子验证、不发布；
- API 不暴露 provider、prompt、job 内部键。

### 6.2 相邻回归

以下测试集合共 `220 passed, 2 warnings`：

- recommendation 新测试；
- Monitoring AI repository/service；
- rule authoring/templates；
- mapping activation；
- protocol rule API；
- protocol preparation。

### 6.3 静态验证

- 变更模块及测试 `ruff check`：通过；
- 变更模块、router、`main.py` 和测试 `compileall`：通过。
- 未对当前运行服务进行重启，未写入真实产品数据库。

## 7. 尚未完成与下一验收边界

- 当前任务明确禁止触碰前端；尚未把 recommendation start/status/decision 接入现有
  候选决定界面。
- 尚未在受控重启后的真实 OpenAPI 和真实项目中验收新路由。
- 真实项目验收需至少覆盖：
  1. 一条安全性事实和 AE 闭合字段映射；
  2. 一条明确无安全 family 的事实；
  3. 方案源文件或 mapping revision 漂移；
  4. 独立 AI 首次输出无效 DSL 后成功修复及修复仍失败两种路径；
  5. 用户接受后确认未自动产生规则包、影子验证或发布记录。
- 上述验收前不得宣称该闭环已在真实项目或前端上线。
