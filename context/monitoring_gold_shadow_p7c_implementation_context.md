# P7C Gold Case、不可判定诊断集与影子运行发布门禁实现合同

## 目标

在不伪造任何真实项目证据、不写入生产运行库的前提下，补齐规则生命周期的发布级覆盖门：

1. 布尔型 gold case 明确表达正例、反例和关键边界覆盖；
2. 缺失、冲突或无法确定的输入以独立诊断用例表达，绝不伪装为阴性；
3. 影子运行必须覆盖规则包中每条规则的完整、冻结用例集；
4. 发布前逐规则验证正例、反例、边界例和不可判定诊断例；
5. 首批风险类别需在至少两个权威真实项目中完成泛化验证。

## 来源与现状

- 只读盘点：`reviews/monitoring_gold_shadow_p7c_inventory.md`
- 当前模型：`services/api/app/monitoring_protocol_rules.py`
- 当前仓库：`services/api/app/monitoring_protocol_rule_repository.py`
- 当前服务：`services/api/app/monitoring_protocol_rule_service.py`
- 当前来源权威校验：`services/api/app/monitoring_gold_case_authority.py`

当前生产规则、gold case 和 shadow run 数量均为 0。现有真实行派生测试候选不得直接升级为正式证据。

## 数据合同

### 布尔型 Gold Case

- 保持 `expected_match: bool`。
- 新增不可为空的封闭覆盖标签，至少支持：
  - `positive`
  - `negative`
  - `boundary`
- 一个用例可同时具有多个标签，例如阈值等于边界的正常结果可同时标记
  `negative` 和 `boundary`。
- `positive` 与 `negative` 不得同时存在。
- `expected_match=true` 必须含 `positive`；`expected_match=false` 必须含
  `negative`。
- `boundary` 只表示临界条件覆盖，不改变期望布尔结果。
- 标签参与稳定 ID 和内容哈希；不可变存储；兼容迁移不得把旧用例静默推断为发布级
  `boundary`。

### 不可判定诊断用例

- 建立独立模型、表和不可变存储，不复用 `RuleGoldStandardCase.expected_match`。
- 至少绑定：
  - 精确项目、规则键、规则修订；
  - 权威方案来源、原始 listing 来源、批次修订、映射修订；
  - 当前/历史/相关记录、业务键、行指纹、字段级来源；
  - 期望诊断代码或封闭诊断类别；
  - 医学理由和可读证据定位。
- 复用与布尔 gold case 相同强度的来源权威校验。
- 影子执行结果必须验证实际状态为 `indeterminate`，且实际诊断代码符合冻结预期。
- 诊断例和其执行结果分别进入内容哈希；不得计入布尔 passed/failed 数量。

## 发布覆盖门

对规则包中的每个精确 `rule_revision_id`，发布前必须满足：

```text
positive >= 1
negative >= 1
boundary >= 1
diagnostic_indeterminate >= 1
authoritative_projects >= 1
```

其中正例、反例、边界例可以由 2 至 3 个用例组合完成，但每个标签必须真实存在。

对首批风险类别，以规则的封闭 `rule_family` 作为类别身份，发布前必须满足：

```text
authoritative_projects >= 2
```

跨项目覆盖只能统计已通过来源权威校验、映射确认和批次冻结的真实项目；测试夹具、恢复过渡
来源和人工提升来源类别均不得计入。若第二项目客观不适用，应记录“不适用”，不能构造阳性；
该类别继续保持未达到首批发布门。

首批类别范围：

- `ae_mh_missing_review`
- `cs_ncs_review`
- `concomitant_medication_policy`
- `study_treatment_change` / `study_treatment_adherence`
- `visit_window_and_order`
- 实验室异常、CTCAE 纵向加重所属的明确规则类别

若现有 `rule_family` 无法唯一表达实验室/CTCAE 类别，应先给出最小、封闭、向后兼容的分类
调整，不得借用自由文本标题进行统计。

## 影子运行合同

- 影子运行冻结：
  - 完整布尔 gold case set 及 SHA-256；
  - 完整不可判定诊断 case set 及 SHA-256；
  - 每个精确规则修订的覆盖计数；
  - 每个风险类别的权威项目集合。
- 影子运行缺少任何已登记用例、结果身份不匹配、规则修订漂移或来源权威失效时关闭失败。
- 发布事务重新计算并核对覆盖，不接受仅由调用方提交的计数。
- 旧 schema 迁移需幂等、可回读；旧数据不得自动取得新发布资格。

## 医学边界

- `CM` 仅代表非试验用合并用药/治疗。
- `EX/EC/DA/IP` 代表试验药物暴露、给药和剂量变化。
- 试验药物剂量增加、降低、暂停、永久停药、重启、漏用、频次/途径改变及多域冲突需可作为
  独立边界用例。
- 疫苗分类不能仅依据 `J07` 自动升级为活疫苗或减毒活疫苗。
- 不得使用既有 Subject Timeline、Patient Profile 或 skill 后半段产物替代从方案原文和原始
  listing 建立的证据。

## 写范围

允许：

- `services/api/app/monitoring_protocol_rules.py`
- `services/api/app/monitoring_protocol_rule_repository.py`
- `services/api/app/monitoring_protocol_rule_service.py`
- `services/api/app/monitoring_gold_case_authority.py`
- P7C 对应测试文件
- P7C handoff / metrics / review 记录

禁止：

- 医学写作子系统；
- 共享 AI 配置；
- 前端；
- 当前运行中的 API 进程；
- 真实生产运行库；
- P7B 正在修改的记录级解析文件。

## 验收

- 新增模型不变量、幂等迁移、不可变存储、完整集合哈希、来源权威、影子执行、覆盖门和发布
  事务测试。
- 必须含：
  - 每条规则只有一个通过用例时发布失败；
  - 正例/反例齐全但无边界时失败；
  - 布尔用例齐全但无不可判定诊断例时失败；
  - 诊断例实际返回 false 而非 indeterminate 时失败；
  - 第二项目来源不权威时不计跨项目覆盖；
  - CM 与 EX/EC/DA/IP 边界错误时失败；
  - 旧数据库幂等迁移与旧用例不自动取得发布资格。
- 聚焦测试、相邻规则生命周期测试和医学监查组合回归全部通过。
- Codex 只接受真实文件、测试结果和运行行为，不以执行者信心作为验收证据。
