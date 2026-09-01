# 执行成员合同：W2a 确定性框架去猜测与完整 PICOS 组合骨架

你是 Hermes/aishuo/cms-model 的有界执行成员。首先完整读取并遵守
`/Users/smkzw/.hermes/SOUL.md`，最终报告说明是否读完。

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_w2a_deterministic_picos_packages_01.md`

不得自行写 runner 报告；在 final response 中返回完整报告，由 runner 持久化。

## Hard boundaries

- 工作目录仅为当前 workspace。
- 只允许修改：
  - `services/api/app/medical_writing_authoring_prefill.py`
  - `tests/test_medical_writing_authoring_prefill_picos_packages.py`（可新建）
  - `tests/test_medical_writing_authoring_prefill.py`（仅修订与本轮新语义直接冲突的断言）
- 不修改 AI adapter、合同模型、journey、main、repository、前端、数据库、配置或记录。
- 不进行工程安全、漏洞、后门工作。
- 不替代产品独立 AI，不在本轮生成真实项目临床结论。
- 本轮不实现组合采纳事务/API；只生成可审计候选合同。
- 精确剂量、终点、AESI、样本量、洗脱期、时间窗无证据时不得形成可采用事实。

## Read these files only

- `AGENTS.md`
- `/Users/smkzw/.hermes/SOUL.md`
- `context/plans/medical_writing_ai_first_candidate_packages_20260724.md`
- `runs/execution/mw_ai_first_candidate_packages_20260724/manager_plan_grok_02.md`
- `packages/contracts/workbench_contracts/models.py` 中
  `MedicalWritingPicosDefinition`、`AuthoringPrefill*` 合同
- `services/api/app/medical_writing_authoring_prefill.py`
- `tests/test_medical_writing_authoring_prefill.py`
- `tests/test_medical_writing_authoring_prefill_package_contract.py`

## 已确认的真实失败

干净项目只输入 `CMS-D017`、PNH、II期后，确定性生成器把以下内容当首选：

- 随机、双盲、安慰剂、平行组、多中心、DMC；
- `RDBPC parallel-group multicenter`；
- “成人”人群；
- 标题备选中加入“随机对照”；
- PICOS 只有 population/intervention/comparator 三个摘要，其他关键模块为空。

“提示小字说不构成结论”不能抵消主推荐按钮的误导。分期本身不能证明上述设计。

## 本轮目标

### A. 清除按分期硬编码的未确认事实

1. 方案标题：
   - 推荐标题只能由已确认的试验药物、适应症和分期组合；
   - 不得在未确认时加入随机、对照、成人/健康人、盲法、多中心、有效性等设计/人群事实；
   - 可提供 2–4 个纯措辞/命名备选，但不得改变研究事实。
2. 人群：
   - 不得凭适应症生成“成人/儿童/治疗线/严重度”；
   - 保守人群摘要只表达该适应症及“具体条件待项目证据确认”。
3. 正交设计维度：
   - 随机、盲法、对照、分组、中心、DMC/SRC、期中分析、I期 parts 等仍分别存在；
   - 没有当前项目来源时，不能把某一项标为 `recommended` 或 `batch_allowed`；
   - 首项应是明确的 `pending_decision` / `manual_only` 待决定卡，备选也是用户选择项；
   - I期允许 SAD、MAD、首次患者、食物影响、物质平衡、肝损伤、肾损伤、DDI 等多选设计，
     但不得默认 SAD+MAD 已确定。

### B. 扩展完整 PICOS 字段覆盖

在现有 PICOS 模型范围内，字段级高级编辑至少覆盖：

- population: `population_summary`, `inclusion_modules`, `exclusion_modules`,
  `washout_rules`
- intervention: `intervention_summary`, `intervention_dose_regimen`,
  `required_background_rules`, `allowed_concomitant_rules`,
  `prohibited_concomitant_rules`, `assessment_timing_restrictions`
- outcomes: `primary_objectives`, `secondary_objectives`,
  `exploratory_objectives`, `primary_endpoint`, `key_secondary_endpoints`,
  `other_secondary_endpoints`, `exploratory_endpoints`, `safety_endpoints`,
  `aesi_definitions`, `assessment_instruments`
- execution/statistics: `study_epochs`, `visit_strategy`, `estimand_strategy`,
  `sample_size_strategy`, `statistical_strategy`

非精确字段可进入 `SUPPORTED_STUDY_DEFINITION_PATHS`。`EXACT_FACT_PATHS` 在 W3
原子采纳及来源门接入前仍不得因本轮改动变成无保护的可采用路径。

### C. 四个组合候选包

在既有 `AuthoringPrefillPackage.field_candidates` 中加入：

- `package.population`
- `package.intervention`
- `package.outcomes`
- `package.statistics`

要求：

- `candidate_scope=module`（statistics 可用 module；不必发明新 scope）
- `target_paths` 与 `structured_value` key 精确一致
- 无足够来源时，生成一个清晰、中文、非空的 `pending_decision` 候选，说明需要竞品方案、
  IB、方案摘要或用户补充哪些最小信息；不得用假临床事实填空
- `adoption_mode=manual_only`
- `clinical_tradeoffs` 与 `evidence_gaps` 使用医学撰写人员可理解的中文
- 有当前已确认值时，组合包可以把这些值带入，但不能把空缺或推断伪装成已确认
- 不新建第二套事实状态机

### D. 候选责任与进度

- 扩展 `_candidate` 工厂以正确设置 W1 新字段。
- 身份类中真正由已确认最小事实机械组合的候选可为
  `recommendation_role=recommended`；只有服务端明确安全的身份字段才可
  `adoption_mode=batch_allowed`。
- 临床设计/精确事实缺证据时均为 pending/manual。
- package progress 应区分“已有安全推荐”与“缺证据待决定”，不得把 pending 计为可直接采用
  的推荐完成。

## 必须新增的反例测试

1. D017 最小三事实的所有标题候选不含随机、对照、成人、双盲、多中心。
2. II/III期最小事实不能产生随机、双盲、安慰剂、DMC 的 recommended 候选。
3. I期最小事实不能默认 SAD+MAD；可选 parts 集包含主要一期类型且支持多选语义。
4. 四个 `package.*` 均存在、scope/target/value 严格一致、无证据时
   pending/manual，不可 batch。
5. 完整 PICOS 字段覆盖清单没有遗漏；exact paths 仍处于证据保护边界。
6. pending 不计入可直接采用推荐数。
7. 既有 synopsis-confirmed 值保持 `user_confirmed`，不被 pending 覆盖。
8. 所有既有 prefill 测试零失败；只可修订固化“按分期猜设计”或“exact 永久禁止”旧语义的
   断言，不得放宽 stale/idempotency/adoption/invalidation 测试。

## 验收

```bash
pytest -q \
  tests/test_medical_writing_authoring_prefill_picos_packages.py \
  tests/test_medical_writing_authoring_prefill.py \
  tests/test_medical_writing_authoring_prefill_package_contract.py
python3 -m py_compile services/api/app/medical_writing_authoring_prefill.py
```

必须零失败。最终报告说明修改文件、关键函数、测试、仍留给 W2b/W3/W4 的事项及紧凑
loop trace。完成标记：

`HERMES_W2A_DETERMINISTIC_PICOS_PACKAGES_01_COMPLETE`

