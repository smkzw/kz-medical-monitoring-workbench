# 医学监查 P10：能力感知型字段映射语义质量门独立审阅

## 1. 审阅目的与边界

本次审阅聚焦一个产品与架构问题：

> `capability_blocker` 是否应阻断整份正式字段映射的确认与激活？

审阅范围：

- `services/api/app/monitoring_mapping_semantic_quality.py`
- `services/api/app/monitoring_mapping_activation.py`
- `services/api/app/monitoring_mapping_draft_repository.py`
- `tests/test_monitoring_mapping_semantic_quality.py`
- `tests/test_monitoring_mapping_draft_repository.py`
- `tests/test_monitoring_mapping_activation.py`
- `context/monitoring_p10_v11_early_semantic_review_subagent_20260730.md`
- 相邻 API 与前端语义质量摘要的只读核对

本次未修改代码、数据库或运行状态。仅新增本设计报告。定向现状回归为
`81 passed`。

## 2. 结论

### 2.1 核心结论

`capability_blocker` **不应默认阻断整份正式映射**。

正式映射回答的是：

> 当前项目字段、来源、角色、血缘和未映射边界是否形成了一份真实、确定、可追溯的
> 项目级解释。

能力启用回答的是：

> 在这份正式映射之上，哪些医学监查能力已具备充分前置条件，可以生成确定性结果或
> 风险判断。

两者必须分层。某个 MedDRA 版本血缘缺失、某个量表尚不可复算或部分日期无法支持精确
访视窗判断，不应使以下能力同时停摆：

- 原始 listing 查阅与溯源；
- 不依赖标准编码的 Subject Timeline；
- Patient Profile 中的来源值和原始趋势；
- 不依赖缺失编码链的确定性规则；
- 其他已满足前置条件的风险识别能力。

但能力级放行不能演变为通用 override。正确合同是：

1. 正式映射在无全局阻断项时可以确认；
2. 受影响能力由服务端确定性标记为不可用或受限；
3. 激活时固化本次有效能力集合；
4. 运行相关能力前再次进行服务端门禁；
5. 不提供“忽略全部并继续”；
6. 修复证据后重新评估，能力不得仅凭用户文字声明恢复。

### 2.2 例外

若一个问题实际破坏了映射本身的真实性、身份关联或互斥语义，就不应继续称为
`capability_blocker`，而应提升为 `global_blocker`。

因此，判断标准不是“该字段是否重要”，而是：

- **映射事实本身是否虚假或不确定**：全局阻断；
- **映射事实可安全保留，但不足以支撑某项推断**：能力限制。

## 3. 当前实现的事实与缺口

### 3.1 已有可靠基础

当前实现已具备以下可复用基础：

- 完整字段覆盖、重复、遗漏和越界检查；
- 角色目录、技术元数据一致性、CM/IP 边界、编码与派生血缘检查；
- 确认时服务端重新评估；
- 正式 revision 固化质量报告正文与 SHA-256；
- 激活时重新计算并核对报告正文、哈希和不可变 draft；
- 候选、来源、profile 和字段集合的完整链路校验；
- 正式 revision、激活历史、CAS 和幂等边界。

这些机制不需要推翻。

### 3.2 当前过度阻断的直接原因

`monitoring_mapping_semantic_quality.py:615-632` 将
`global_blocker_count > 0` 或 `capability_blocker_count > 0` 都折叠为
`status=blocked`。

随后：

- `monitoring_mapping_draft_repository.py:808-821` 在 `status=blocked` 时拒绝
  confirm；
- `monitoring_mapping_activation.py:981-995` 在重新评估为 `blocked` 时拒绝
  activate；
- 前端只识别一个 `semanticQualityBlocked` 布尔值，并直接禁用确认按钮。

因此，当前枚举中虽然存在 `CAPABILITY_BLOCKER`，生命周期上却没有能力级语义；
它实际仍是全局阻断的别名。

### 3.3 当前报告缺少的关键合同

现有报告只有：

- 全局阻断数量；
- 能力阻断数量；
- 警告数量；
- 问题组与字段引用。

尚无：

- 问题影响的 `capability_id`；
- 项目本次拟启用能力清单；
- 每项能力的有效状态；
- 正式映射是完整激活还是受限激活；
- 运行时可查询的有效能力集合；
- 能力恢复时的新版本与重检合同。

### 3.4 V11 早期审阅对该问题的直接证据

V11 早期样本中，MedDRA 术语、代码和版本字段可作为来源值保留，但跨分块编码链尚未
完整组装。当前 `G-CODE-002` 将此标为能力阻断是合理的；把整份映射阻断则不合理。

同理：

- 来源总分可展示，但在计分规则不足时不得声称已复算；
- 部分日期可进入带精度边界的时间线，但不得执行精确天数/窗口结论；
- 原始 AE 措施文本可展示，但若尚未拆解停药、重启等值级动作，则不得启用依赖该拆解
  的试验药物动作风险规则。

## 4. 最小可落地的双层合同

### 4.1 层 1：正式映射有效性

正式映射有效性只判断以下不变量：

1. 来源和字段集合完整、当前、无篡改；
2. 每个来源字段恰好具有一个明确处置：安全角色或显式未映射；
3. 主体、来源记录和关键技术身份不会被错误关联；
4. CM 与试验药物不会被混为同一事实；
5. 已声明的标准编码和确定性派生不是虚假声明；
6. 同一事实链不存在互相冲突的体系、版本、字段性质或公式。

只要上述不变量成立，即可形成正式 mapping revision。

正式映射允许包含：

- `source_collected`；
- `source_metadata`；
- 证据充分的 `standardized_coded`；
- 可复算的 `deterministic_derived`；
- 明确的 `unmapped`。

“正式”不等于“所有字段都已标准化”，也不等于“所有能力均可运行”。

### 4.2 层 2：能力可用性

语义质量门基于正式映射和能力依赖目录，生成确定性的能力状态：

```text
ready
limited
blocked_by_quality
disabled_by_design
```

- `ready`：前置角色、血缘、精度和来源均满足，可完整运行；
- `limited`：可运行安全子集，输出必须受限，例如部分日期只表达区间关系；
- `blocked_by_quality`：前置条件不足，运行时不得执行该能力；
- `disabled_by_design`：本研究不适用或项目明确不启用，不属于质量缺陷。

最小正式映射激活结论：

```text
activation_disposition =
  reject
  activate_restricted
  activate_full
```

- 存在任何 `global_blocker`：`reject`；
- 无全局阻断但存在 `blocked_by_quality` 或 `limited`：
  `activate_restricted`；
- 所有拟启用能力均 `ready`：`activate_full`。

## 5. 哪些问题必须全局阻断

### 5.1 来源与结构不完整

必须全局阻断：

- 输入字段重复、遗漏、越界；
- draft、候选、profile、来源哈希或规则身份失配；
- 正式 revision 与不可变 draft 不一致；
- 同一来源字段出现多个无法确定的正式处置。

原因：无法证明正式映射对应完整、唯一、当前的来源事实。

### 5.2 主体与记录身份错误

必须全局阻断：

- 已映射的 subject/site/visit/form/record 标识发生互相冒用；
- 相同技术键跨域被赋予互斥身份；
- 一个技术键被错误用于拼接不同受试者或不同记录。

注意：

- “缺少受试者标识”不必阻断原始表格查阅，但会阻断所有受试者级能力；
- “把中心号映射成受试者号”是虚假映射，必须全局阻断。

### 5.3 CM/IP 事实混淆

必须全局阻断：

- CM 字段被正式声明为试验药物实际给药或变更；
- 试验药物字段被正式声明为非试验用药；
- 发放/回收被声明为实际给药；
- 一个正式角色同时声称剂量调整、暂时停药、永久停药、重启等互斥动作。

若来源值本身是复合文本，可安全保留为原始来源事实；此时不得错误拆分，相关动作识别
能力应被限制，而不是把复合文本强行映射为某一个动作。

### 5.4 虚假标准化与虚假派生

必须全局阻断：

- 字段声明为 `standardized_coded`，却没有明确编码体系和适用版本；
- 同一标准编码链存在冲突体系、版本或字段性质；
- 字段声明为 `deterministic_derived`，却没有有效源字段、公式、复算条件或确认血缘；
- 部分日期被声明为完整日期；
- 来源总分被声明为工作台复算结果。

安全降级方式是把字段修订为 `source_collected` 或 `unmapped`，然后由能力门控制下游
用途；不能保留虚假声明后继续激活。

### 5.5 能力问题无法定位影响范围

任何标为 `capability_blocker` 的问题，如果规则目录没有给出非空、闭合、已登记的
`affected_capability_ids`，应失败关闭并提升为全局阻断。

这是防止“名义上局部、实际上不知道会影响哪里”的关键边界。

## 6. 哪些问题只应禁用相关能力

以下前提是字段仍以真实的来源性质保留，且不存在虚假标准化/派生声明。

| 质量缺口 | 不应受影响 | 应限制的能力 |
|---|---|---|
| MedDRA/药品词典体系或版本血缘不足 | 原始 term/code 展示、时间线/Profile、非编码规则 | 标准编码归并、编码层级检索、依赖标准编码的 AESI/SMQ 等规则 |
| code-term 配对尚未核验 | 原始同行值展示 | 按标准术语聚合、跨批次标准编码比较 |
| 日期仅有年月、年份或未知组件 | 原始日期展示、区间型时间线 | 精确持续时间、洗脱期、访视窗和要求天数阈值的规则 |
| 量表规则/版本/分支/缺失计分不足 | 来源条目和来源总分展示 | 工作台复算、基于复算值的变化或异常判断 |
| 实验室结果缺单位/参考范围/CTCAE 规则 | 原始结果与来源异常标志展示 | 统一单位阈值、CTCAE 自动分级和等级上升预警 |
| AE/MH 关键配对或日期前提不足 | AE、MH 原始事件展示 | AE/MH 漏报与跨表一致性判断 |
| IP 动作值级拆解不足 | 原始 AE 措施、给药和药物管理记录展示 | 剂量调整、停药、重启、依从性和相关 PD 风险判断 |
| 发放、回收、计划剂量缺少复算公式 | 发放/回收原始记录 | 依从性、实际暴露和漏服/多服结论 |
| 量表或实验室只有部分组件 | 已存在组件的原始趋势 | 需要完整组件集合的总分或复合指标能力 |

## 7. 最小能力目录

首版不应一次拆成大量细粒度开关。建议先固定以下 10 个稳定能力：

1. `raw_source_review`：原始 listing 查阅与溯源；
2. `subject_timeline`：受试者级来源事件时间线；
3. `patient_profile`：受试者/中心级来源值和趋势；
4. `ae_mh_reconciliation`：AE/MH 漏报与一致性；
5. `standard_coding_rules`：依赖标准医学/药品编码的归并与规则；
6. `precise_temporal_rules`：访视窗、洗脱期、持续时间等精确时间规则；
7. `lab_ctcae_rules`：实验室阈值、CTCAE 分级及变化预警；
8. `protocol_medication_rules`：禁用药、限制用药和方案用药规则；
9. `ip_exposure_adherence`：实际给药、剂量变更、停药/重启与依从性；
10. `scale_recalculation`：量表复算及基于复算值的趋势判断。

其中 `raw_source_review` 不依赖语义映射完成度；只要来源通过基本信息与内容校验，就应
可用。其他能力按规则依赖关系决定状态。

`subject_timeline` 和 `patient_profile` 应进一步区分：

- 来源值展示子集；
- 需要标准编码、精确日期、CTCAE 或量表复算的增强子集。

这样，某个增强子集受限时，不会让整个页面不可进入。

## 8. 报告与持久化合同

### 8.1 `MappingSemanticQualityReport` v2

在现有报告基础上最小新增：

```text
schema_version = monitoring_mapping_semantic_quality_v2
activation_disposition
capability_manifest_sha256
capability_states[]
```

每个 finding group 最小新增：

```text
affected_capability_ids[]
```

每个能力状态：

```text
capability_id
state
blocking_finding_group_ids[]
limitation_codes[]
```

不要在质量报告中长期保存受试者级敏感原始值；只保存字段级、规则级和能力级证据摘要
与 locator。

### 8.2 capability manifest

`capability manifest` 是版本化的服务端目录，不由前端自由传入，至少包含：

```text
manifest_version
capability_id
required_role_concepts[]
required_lineage_contracts[]
allowed_limited_modes[]
dependent_rule_ids[]
```

报告输入哈希必须包含 manifest 版本和内容哈希。任何能力依赖变化都会使旧报告需要
重检。

### 8.3 mapping revision

继续保留现有：

- `semantic_quality_report`
- `semantic_quality_report_sha256`

并确保报告内包含 capability manifest 哈希和有效能力快照。无需另建一套可变
“审批表”。

mapping revision ID 继续纳入质量报告哈希；因此修订字段或能力证据后必须形成新
revision，不能原地改写。

### 8.4 activation state

项目活动映射最小增加：

```text
semantic_quality_report_sha256
capability_manifest_sha256
activation_disposition
effective_capabilities_sha256
effective_capabilities[]
```

`effective_capabilities[]` 是正式运行合同，不是界面提示。所有医学规则入口必须读取
该状态。

## 9. 确认、激活与运行时门禁

### 9.1 confirm

确认时服务端重新计算报告：

- `global_blocker_count > 0`：拒绝确认；
- 无全局阻断：允许形成不可变 revision；
- capability blocker 存在：revision 的
  `activation_disposition=activate_restricted`。

不要求医学经理逐个技术能力再次“批准”。用户确认当前映射时，同时确认界面已明确
展示的有效能力摘要；这不是第二层“待医学批准”。

### 9.2 activate

激活时继续执行现有来源、draft、revision、报告正文和哈希核验，并新增：

1. capability manifest 哈希必须当前；
2. 每个 capability blocker 必须映射到已登记能力；
3. 受阻能力不得出现在有效能力集合中；
4. 全局阻断仍直接拒绝；
5. 受限激活必须原子写入正式能力快照。

### 9.3 runtime guard

增加统一服务端门禁：

```text
require_monitoring_capability(project_id, capability_id)
```

所有需要语义前置条件的规则、批处理和 API 必须调用该门禁。前端隐藏按钮不是安全或
科学性保障。

当能力为 `blocked_by_quality` 时：

- 不执行规则；
- 不生成空结果伪装成“未发现风险”；
- 返回明确的能力不可用状态与一条简洁原因；
- 原始数据和不依赖该能力的模块继续可用。

## 10. 前端最小呈现

主界面只呈现一条状态摘要：

### 完整激活

```text
字段映射可启用
10 项医学监查能力可用
```

### 受限激活

```text
字段映射可启用 · 3 项能力暂不可用
标准编码规则、精确时间窗、量表复算
```

主按钮：

```text
确认并启用可用能力
```

不得显示：

- 大批字段级技术日志；
- 哈希、内部规则版本和 locator；
- “忽略全部并继续”；
- 用户已确认后仍显示“待医学批准”。

点击摘要后打开轻量详情，只展示：

- 能力名称；
- 一句话原因；
- 会缺少什么结果；
- “修订映射/补充定义”入口。

原始字段、证据定位和技术细节放入二级抽屉。

## 11. 后续重检与能力恢复

### 11.1 必须重检的事件

- draft 字段、角色、field kind 或血缘变化；
- 来源/profile/input revision 变化；
- 角色目录、语义规则或 capability manifest 版本变化；
- 项目研究设计导致拟启用能力变化；
- 新增词典版本、量表规则、日期语义或复算公式。

### 11.2 不自动扩大能力

重检可以自动收紧能力，但不能在无人确认的新证据下自动扩大正式能力集合。

推荐合同：

- 新规则发现新增 blocker：现有能力立即进入 `revalidation_required` 或更严格状态，
  不继续生成新结论；
- 修复证据后评估为 ready：生成新的 mapping revision 并重新激活；
- 历史运行结果继续绑定原 mapping revision 与当时的能力快照，不被新状态改写。

### 11.3 禁止的恢复方式

- 修改数据库状态；
- 前端传入 `override=true`；
- 填写自由文本“已确认”；
- 只把 finding 标记为已读；
- 只隐藏前端警告；
- 复用旧报告哈希。

## 12. 当前规则的建议调整

| 当前规则 | 当前分级 | 建议 |
|---|---|---|
| `G-COVER-001` | 全局阻断 | 保持 |
| `G-ROLE-001` 技术元数据不一致 | 全局阻断 | 身份/连接键冲突保持全局；纯显示标签差异降为能力/警告 |
| `G-ROLE-002` 未进入闭合目录 | 全局阻断 | 核心身份、CM/IP 等保持全局；非核心字段允许安全 `unmapped` |
| `G-CMIP-001` CM/IP 混用 | 全局阻断 | 保持 |
| `G-CMIP-002` IP 动作未分离 | 全局阻断 | 正式角色虚假合并时保持；来源复合文本安全保留时改为相关能力限制 |
| `G-CODE-001` 编码链冲突 | 全局阻断 | 声称标准化时保持；均为来源值时改为标准编码能力限制 |
| `G-CODE-002` 编码体系/版本不足 | 能力阻断 | `source_collected` 时保持能力阻断；`standardized_coded` 时提升为全局阻断 |
| `G-DERIVE-001` 派生不可复算 | 全局阻断 | `deterministic_derived` 声明存在时保持；来源总分不得触发 |

## 13. 最小实施顺序

### Slice 1：修正生命周期语义

1. 报告 v2 增加 `activation_disposition`、`affected_capability_ids` 和
   `capability_states`；
2. 首批建立上述 10 项 capability manifest；
3. `status=blocked` 只由全局阻断产生；
4. capability blocker 产生 `activate_restricted`；
5. confirm/activate 支持受限正式映射；
6. 激活状态固化有效能力集合。

### Slice 2：运行时强制执行

1. 建立统一 capability guard；
2. 标准编码、精确时间、CTCAE、量表复算、AE/MH、IP/依从性规则分别接入；
3. 对受阻能力返回“不可运行”，不得返回空风险列表；
4. Timeline/Profile 使用可用子集，不因增强能力缺失整页停摆。

### Slice 3：轻量前端

1. 将当前单一“暂不可启用”改为完整/受限/拒绝三态；
2. 仅显示受影响能力和一句原因；
3. 提供修订入口，不提供 override；
4. 点击确认后直接激活当前可用能力。

## 14. 必须新增的回归测试

### 14.1 纯质量门

- 只有 `G-CODE-002` 且字段为 `source_collected`：
  `activate_restricted`，不是全局 blocked；
- `standardized_coded` 缺编码体系/版本：全局 blocked；
- 来源总分缺复算规则：仅阻断 `scale_recalculation`；
- 部分日期：Timeline 可 limited，`precise_temporal_rules` blocked；
- capability blocker 没有已登记受影响能力：全局 blocked；
- CM/IP 虚假映射仍全局 blocked。

### 14.2 confirm/activate

- capability-only revision 可以 confirm 和受限 activate；
- revision 固化报告、manifest 和有效能力哈希；
- 受阻能力绝不进入 effective capabilities；
- 报告、manifest、有效能力集合任一篡改均拒绝激活；
- 全局 blocker 仍不能 confirm；
- 旧规则或旧 manifest 报告不能直接激活。

### 14.3 运行时

- 标准编码能力受阻时，原始 AE/CM 展示正常；
- Timeline/Profile 使用来源值正常；
- 调用受阻的标准编码规则时明确失败，不返回“0 个风险”；
- 与编码无关的规则继续运行；
- 修复血缘、形成新 revision 并重新激活后，能力才恢复。

### 14.4 前端

- 受限状态不禁用正式确认按钮；
- 按钮文案为“确认并启用可用能力”；
- 页面只显示受影响能力，不常驻技术 finding 列表；
- 不存在通用 override；
- 已确认后不出现第二层“待医学批准”。

## 15. 验收标准

本合同完成的最低标准：

1. 全局真实性错误仍无法确认或激活；
2. 单个编码链、量表、日期或实验室能力缺口不再阻断整份正式映射；
3. 受影响能力在服务端运行时确实不可执行；
4. 原始数据、Timeline、Profile 和无关规则可继续工作；
5. 不能通过前端参数、自由文本或直接已读状态绕过；
6. 能力快照、质量报告、mapping revision 和激活历史保持不可变哈希链；
7. 能力修复后通过新 revision 恢复，不改写历史；
8. RUX 与另一个不同 EDC 结构的真实项目完成从原始 listing 到受限/完整激活的回归。

## 16. 最终判断

当前实现的不可变 revision、报告哈希和激活复核方向正确，但
`capability_blocker -> status=blocked -> confirm/activate 全拒绝` 是一个产品与架构
层面的过度耦合。

最小正确修订不是增加 override，也不是降低医学语义门，而是把门拆成：

```text
正式映射真实性门
  +
能力依赖门
  +
运行时能力门
```

这样既能保持“错误事实绝不进入正式映射”的严格性，也能保证系统在局部血缘不足时
仍真正可用，并且不会把受限能力误包装为已经支持。
