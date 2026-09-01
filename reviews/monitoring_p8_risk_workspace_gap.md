# 医学监查 P8 风险工作台与受试者视图只读差距盘点

## 1. 审阅结论

### 1.1 总体判断

当前 P8 不是“尚未开发”，也不能认定为“已经完成”。代码中已经存在以下实质能力：

- 七列医学风险 Checklist、逐列筛选与排序；
- 以同一风险实例打开的同页证据/处置工作区；
- 冻结证据片段、跨批次风险历史和旧证据不回填保护；
- 以真实访视日期为横轴的 Subject Timeline SVG；
- AE、试验药物、CM、病史、实验室、疗效、PD/Query 等事件泳道与类别样式；
- RUX、MG-K10、MY009 三个真实项目的受试者级事件聚合；
- 疗效和安全性趋势图、基线、参考范围、异常方向和 CTCAE 字段展示；
- CM 与试验药物给药/暂停/重启/剂量调整的独立数据域；
- 风险工作台内嵌 Subject Timeline、Patient Profile、AE/MH 核查、来源证据和批次历史。

但当前证据只能支持“部分实现，尚未完成 P8 生产验收”。主要原因是：

1. 本次只读盘点未完成当前运行页面的真实浏览器逐按钮复核，不能把源代码和测试存在等同于运行态可用。
2. Checklist 的风险类别仍包含前端文本启发式推断，不是完全由后端权威分类合同驱动。
3. 可读证据链已经具备，但“日期、访视/研究日、指标、值/单位、参考范围、异常方向、对应风险”的统一医学句式尚未在三个真实项目逐条证明。
4. Subject Timeline 已具备访视轴和泳道实现，但高密度碰撞、跨年长周期、部分日期、计划外访视和不同事件类别配色仍缺真实浏览器验收。
5. Patient Profile 当前主体仍是受试者级；“中心筛选/受试者树”不等于中心级疗效与安全性聚合。
6. Checklist 到 Timeline/Profile 的同页嵌入已经实现，但完整 Timeline/Profile 页面返回后恢复筛选、排序、滚动位置和证据工作区状态尚未得到运行态证明。
7. 医学监查业务服务总体独立，但前端仍集中在超大型 `App.jsx` 和全局 `styles.css`，与同步开发的医学写作存在高冲突面。

### 1.2 证据等级

| 等级 | 含义 |
|---|---|
| **代码已实现** | 已沿组件、API、模型、仓储或真实项目适配器找到实现 |
| **测试覆盖存在** | 找到针对性测试，但本次未重新运行，不代表当前运行态通过 |
| **运行态已验证** | 本次在真实服务和真实页面完成操作、数据和视觉核验 |
| **未核实** | 本次未取得足够证据；不以推测补齐 |

本报告没有把“测试文件名存在”作为完成证据。本次未修改产品代码、数据库或前端，也未重新运行自动化测试。

---

## 2. 审阅范围与来源

### 2.1 已读取的权威来源

- P8 只读盘点合同：`context/monitoring_p8_risk_workspace_gap_context.md`
- P7 任务记录：`records/active_slices/medical_monitoring_goal_p7_20260729/TASK_CONTEXT.md`
- 医学监查说明书：`/Users/smkzw/Documents/康哲项目资料/AI/说明书/医学监查子系统说明书.md`
- 全局与工作区 `AGENTS.md`
- 前端入口、医学监查组件、API 客户端、模型转换和样式
- 医学监查 API、统一风险快照、冻结证据、处置、历史和真实项目受试者适配器
- 相关单元/接口测试文件及其实际断言位置

### 2.2 未完成的核验

- **当前运行页面的真实浏览器逐按钮、逐状态和视觉验收：未核实。**
- **当前 API/前端端口的实时响应内容：未核实。**
- **用户提供的 Subject Timeline/Patient Profile 成品与当前页面的像素级并排比较：未完成。**
- **所有相关自动化测试在当前代码状态下重新执行：未执行。**
- **中心级聚合性能、超大风险清单性能和 1440px/1728px 多视口截图回归：未核实。**

因此，后文所有“代码已实现”均不得对外升级为“生产可用”。

---

## 3. 逐功能差距矩阵

## 3.1 项目医学风险 Checklist

### 当前真实状态

**代码已实现，运行态未核实。**

前端已经严格采用七列：

1. 受试者编号；
2. 中心编号；
3. 风险级别；
4. 风险类别；
5. 具体风险项；
6. 当前处置；
7. 更新时间。

各列均有排序按钮和列内筛选，支持重置排序/筛选。前端会以每页 200 条读取全部当前风险快照，并校验分页期间快照是否变化，避免把两个快照拼接为一张表。

### 证据路径/API

- 七列、排序、筛选：`frontend/src/App.jsx:2043-2153`
- 全量分页读取与快照一致性检查：`frontend/src/App.jsx:2156-2183`
- Checklist 实际挂载和风险点击打开工作区：`frontend/src/App.jsx:2771-2823`
- 前端风险模型映射：`frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs:157-229`
- 当前快照 API 客户端：`frontend/src/features/medical-monitoring/medicalMonitoringApi.mjs:200-235`
- 后端持久化快照读取、筛选、分页：`services/api/app/medical_monitoring_summary.py:280-414`
- HTTP 入口：`services/api/app/medical_monitoring_router.py:224-260`
- 相关测试存在：`tests/test_medical_monitoring_module_contract.py`、`tests/test_monitoring_risk_index_api.py`

### 缺口

1. 风险类别由 `riskChecklistCategoryTags()` 对标题、来源、类型和标签做文本匹配，存在“显示分类”与后端权威医学分类不一致的可能。
2. 筛选和排序主要在前端对已拉取的完整快照执行；超大风险项目的内存、网络和交互性能未核实。
3. 当前组件未见“保存视图”和 CSV/Excel 导出入口，低于说明书 §27.2。
4. 当前更新时间来自前端风险模型转换字段；不同来源的时间语义是否统一为“最后医学/数据状态更新时间”未核实。
5. 当前处置列以单一标签显示，用户已确认后的状态是否在所有项目中立即替换“待医学复核”未完成运行态验证。

### 医学风险

- 文本启发式分类可能把“AE 已记录但严重度需复核”错误归为“AE 漏报”，影响风险优先级和医学判断。
- 列表只看当前拉取快照而无明确数据量边界时，可能在大项目中出现漏加载或前端冻结。
- 更新时间口径不清会干扰增量监查中“本批次新发生/改值/重开”的判断。

### 建议编码分片

**P8-A1：权威风险分类合同**

- 后端输出稳定的 `risk_category_code`、`risk_category_label`、`safety_pv_flag`；
- 前端只显示后端分类，不再依据标题推断；
- 保留 `other`，但必须携带医学可读说明。

**P8-A2：Checklist 查询与视图状态**

- 服务端增加稳定排序字段和筛选参数；
- 前端 URL/路由保存筛选、排序、滚动位置和选中风险；
- 增加“保存视图”和按当前筛选导出。

### 真实验收方式

1. 分别用 RUX、MG-K10、MY009 当前真实风险快照打开 Checklist。
2. 每列分别执行升序、降序、筛选、清除和组合筛选。
3. 逐条核对至少 10 类风险：AE 漏报、MH 漏报、CS/NCS 判定、禁限用药 PD、方案执行 PD、试验药物给药、剂量调整/停药/重启、依从性、访视窗口、实验室/CTCAE 趋势。
4. 验证 Safety/PV 只作为附加标签，不替代主风险类别。
5. 在读取分页期间生成新快照，必须明确提示刷新，不能混合两个快照。
6. 用户完成处置后，列表状态和更新时间立即更新，不再显示第二层“待医学批准”。

---

## 3.2 风险类别与 Safety/PV 标记

### 当前真实状态

**部分实现。**

数据模型支持 `primary_category` 和 `tags`；Checklist 会将 `safety_pv` 额外显示为 Safety/PV 标签。风险工作区的 AE/MH 页签也明确说明 Safety/PV 是同一风险的协作投影。

### 证据路径/API

- 风险类别映射和 Safety/PV 附加标签：`frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs:68-90`
- Checklist 标签展示：`frontend/src/App.jsx:2141`
- AE/MH 与 Safety/PV 同一风险说明：`frontend/src/App.jsx:3160-3164`
- 说明书统一风险边界：`医学监查子系统说明书.md:1767-1817`

### 缺口

- 前端仍存在基于文字的分类推断。
- 未找到独立、版本化的风险类别字典接口及跨项目迁移规则。
- “CS/NCS 判定不合理”“禁用药 PD”“试验药物依从性”等细粒度类别是否都由真实规则稳定输出，未核实。

### 医学风险

错误分类会导致 Safety/PV、医学监查和核查前自查出现不同口径，破坏同一风险实例的单一事实源。

### 建议编码分片

纳入 **P8-A1**：建立后端版本化类别字典，禁止前端根据自然语言重新分类。

### 真实验收方式

- 同一风险从 Checklist、AE/MH 页签、Safety/PV 投影、受试者时间线打开时，`risk_instance_id`、主类别和附加标签完全一致。
- 修改风险标题不得改变主类别；规则版本迁移必须产生可审计的类别变化记录。

---

## 3.3 可读风险证据正文

### 当前真实状态

**部分实现，核心链路存在，统一医学句式未完成真实验证。**

系统不是只显示定位符。风险工作区会优先读取冻结证据片段的 `primary_summary`，随后显示关联风险，定位符放在底部作为次级溯源。历史快照也优先显示冻结正文，不会用当前文件内容替代旧证据。

### 证据路径/API

- 证据分组：`frontend/src/App.jsx:2833-2853`
- 可读正文优先、locator 次要：`frontend/src/App.jsx:2860-2880`
- 同一风险自动预读证据：`frontend/src/App.jsx:3069-3107`
- 来源证据页签：`frontend/src/App.jsx:3166` 起
- 冻结证据捕获与公开投影：`services/api/app/monitoring_risk_evidence.py:12-88`
- 证据片段 API 对风险实例和 locator 做强绑定校验：`services/api/app/main.py:3489-3536`
- 旧证据未冻结时返回 409，不以当前来源替代：`services/api/app/main.py:3512-3525`
- 批次历史正文优先：`frontend/src/App.jsx:2971-2992`
- 相关测试存在：`tests/test_monitoring_risk_index_api.py:87-140`

### 缺口

1. 前端仅将 `docx:` 和 `listing:` 前缀视为可直接打开来源；其他合法来源定位格式是否被遗漏，未核实。
2. 实验室证据能否在三个真实项目稳定形成“日期｜访视/研究日｜指标｜数值/单位｜参考范围｜异常方向｜对应风险”的一句话格式，未取得运行态证据。
3. 方案原文、原始数据和系统规则目前在“风险处置”中合并展示，但三类证据的完整性门、缺失原因和重试状态未完成真实页面验收。
4. 系统规则正文仍以 `risk.rationale` 为主；确定性计算输入、公式、阈值版本和中间值是否完整可读，未核实。

### 医学风险

- 只有 locator 没有源事实，会迫使医学经理反复打开原文件，降低复核效率并增加误读。
- 实验室值、单位或参考范围跨记录错配，会直接改变异常方向和 CTCAE 判断。
- 用当前来源替换旧快照会污染批次历史；当前后端已阻断，但必须验证前端能正确解释 409。

### 建议编码分片

**P8-B1：证据呈现合同**

- 定义 `EvidenceDisplayFragment`：`source_type`、`event_date`、`visit_code`、`study_day`、`fact_text`、`value`、`unit`、`reference_range`、`abnormal_direction`、`risk_link_text`、`locator`；
- 后端按领域生成医学可读正文，前端不拼接医学含义；
- 明确 `missing_reason` 和 `capture_status`。

**P8-B2：规则推导可读化**

- 返回规则条款原文、参数版本、输入事实、计算过程、输出和限制条件；
- locator/hash 保留在折叠式“溯源详情”。

### 真实验收方式

- 从三个真实项目各选 10 条风险，其中至少 5 条实验室风险、2 条 CM/禁限用药风险、2 条试验药物变化风险、1 条访视窗口风险。
- 用户不打开原文时即可回答“发生了什么、何时发生、依据什么、为什么提示”。
- 再点击“查看原文”，定位必须指向该风险冻结时的原始记录。
- 人为制造旧证据未冻结场景，页面必须明确显示不可用原因，不得回显当前来源。

---

## 3.4 风险医学处置与“待医学批准”语义

### 当前真实状态

**部分实现。**

医学监查风险存在“待医学复核”候选状态和处置动作；代码中未发现医学监查专属页面把用户已经确认的内容继续标为“待医学批准”。`App.jsx` 中仍有其他子系统的“待医学批准”文字，不能据此认定医学监查违反边界。

### 证据路径/API

- 风险工作区默认页签为风险处置：`frontend/src/App.jsx:3024-3157`
- 处置写入口：`services/api/app/main.py:3562` 起
- 风险状态映射含 `待医学复核 -> pending_review`：`services/api/app/medical_monitoring_summary.py:684`
- P7 记录明确 authoring API 不出现“待医学批准”：`records/active_slices/medical_monitoring_goal_p7_20260729/TASK_CONTEXT.md:331-350`
- AI 合同明确用户采纳后不再增加第二层批准：`services/api/app/monitoring_ai_service.py:1164-1166`

### 缺口

- 用户点击“确认/采纳/已复核”后，所有页面是否同步离开“待医学复核”，未完成运行态验证。
- 内部 Query 审批策略与用户本人的医学确认是两个不同状态，但当前页面是否足够清楚地区分，未核实。
- 全局审批中心仍包含医学监查处置对象；其显示语言是否会造成“医学经理已确认后仍待医学批准”的误解，未核实。

### 医学风险

把“医学风险已确认”和“Query 是否经内部流程正式发出”混为一谈，会重复审批并导致状态死锁。

### 建议编码分片

**P8-C1：处置状态语义收口**

- `AI/规则候选 -> 用户确认/驳回/需补充资料` 是医学判断；
- `Query 草稿 -> 内部审批 -> 外部发送` 是组织流程；
- 两条状态轴独立，不再以“待医学批准”概括。

### 真实验收方式

完成以下动作并逐页面核对：

1. 用户确认风险；
2. 用户驳回风险；
3. 用户要求补充资料；
4. 用户生成 Query 草稿但不送审；
5. 用户提交 Query 内部审批。

步骤 1 后，Checklist、证据工作区、Timeline、Profile 和批次历史均显示“已医学复核/已确认”的同一状态，不再出现“待医学批准”。

---

## 3.5 Subject Timeline：访视轴、泳道与信息密度

### 当前真实状态

**代码已形成真实访视轴和事件泳道；视觉与高密度运行态未核实。**

Timeline 以 `visit_anchors.actual_date` 为主轴；无锚点时从实际事件生成访视轴。事件按 AE、试验药物、背景治疗、CM、非药物治疗、病史、实验室、疗效、PD/Query 分泳道。SVG 根据日期跨度动态计算宽度，并对同泳道重叠事件分轨。

### 证据路径/API

- 访视轴优先使用真实 `visit_anchors`：`frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs:175-200`
- 泳道定义：`frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs:1-21`
- 泳道聚合：`frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs:225-243`
- 日期比例尺、访视线、事件块和分轨：`frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx:82-238`
- 完整页面、缩放、图例和明细：`frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx:484-634`
- 真实受试者 API：`GET /api/projects/{project_id}/subjects/{subject_id}/monitoring`
- API 挂载：`services/api/app/main.py:9111-9124`
- 三个真实项目聚合入口：
  - `services/api/app/rux_monitoring_service.py:220-269`
  - `services/api/app/mgk10_sar_monitoring_service.py:213-245`
  - `services/api/app/my009_monitoring_service.py:333-381`
- 受试者页面路由：`frontend/src/App.jsx:15530-15540`
- 相关测试存在：`tests/test_rux_monitoring_service.py`、`tests/test_mgk10_sar_monitoring_service.py`、`tests/test_my009_monitoring_service.py`

### 缺口

1. 未完成与用户提供的参考成品在真实桌面视口下的并排视觉验收。
2. 高密度事件、同日多事件、持续事件、部分日期、访视过密和长周期研究的碰撞未核实。
3. 当前 SVG 的最小宽度为 1500px，并按日期跨度增加；极长研究可能产生很宽画布，导航和定位体验未核实。
4. 风险聚焦依赖 `related_risk_ids`；当前风险是否能在三个项目所有事件域稳定关联，未核实。
5. 完整页面下方仍为每泳道明细卡片，是否造成纵向信息重复和过载，需要真实用户验收。

### 医学风险

- 访视锚点或事件日期错误会使事件落在错误研究阶段，进而误判洗脱期、访视窗、给药调整与 AE 时序。
- 高密度碰撞会隐藏持续事件或同日多事件，造成漏看。
- 用计划日替代实际日期会掩盖方案执行 PD；当前代码优先实际日期，但需真实数据验证。

### 建议编码分片

**P8-D1：时间轴布局引擎回归**

- 建立高密度、长周期、同日多事件、部分日期和计划外访视的布局样例；
- 增加时间范围缩放、风险聚焦和“跳到事件”；
- 只保留一套权威 Timeline 组件，清理 `App.jsx` 中旧版/重复实现。

**P8-D2：事件—风险关联**

- 由后端返回事件和风险的稳定关联对象，而不是只靠 locator 或前端推断；
- 每个事件可打开同一风险证据工作区。

### 真实验收方式

- 三个真实项目各选：
  - 1 名事件密集受试者；
  - 1 名数据稀疏受试者；
  - 1 名含计划外访视/部分日期/持续用药的受试者。
- 在 1440×900、1728×1000 桌面视口检查：无重叠、无文字越界、类别可辨、事件可点击、风险聚焦准确。
- 与用户参考成品逐项比较：访视轴、日期比例、泳道顺序、事件密度、持续事件、风险卡和原始事实可读性。

---

## 3.6 各泳道事件类别配色

### 当前真实状态

**类别映射和 CSS 类已实现，实际颜色区分未完成浏览器核验。**

事件类别不仅按泳道着色，还细分试验药物暂停/恢复、AE 记录/AE 复核、CM/禁限用药风险、血常规/血生化异常等。

### 证据路径/API

- 事件类别和 class 映射：`frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs:23-103`
- 图例生成：`frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs:106-121`
- 事件块同时应用泳道、类别、严重度和风险焦点 class：`frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx:196-229`
- Timeline 图例：`frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx:544-575`
- CSS 区域：`frontend/src/styles.css:5816-5903`

### 缺口

- 未核实所有类别是否在实际主题下有视觉上明显且可访问的不同颜色。
- 泳道色、事件类别色、严重度色和当前风险橙色外框可能同时出现，视觉优先级是否冲突未核实。
- 未完成色觉缺陷和打印/灰阶可辨性检查。

### 医学风险

如果颜色同时承担“事件类别”和“风险严重度”而无图形/文字冗余编码，用户可能把类别差异误读为严重度差异。

### 建议编码分片

**P8-D3：颜色语义收口**

- 颜色主要表达事件类别；
- 严重度使用边框/图标/标签冗余表达；
- 当前风险使用统一焦点外框；
- 图例始终显示文字。

### 真实验收方式

- 构造包含全部事件类别的真实来源派生视图；
- 使用视觉截图检查、灰阶检查和对比度检查；
- 不看图例时仍能通过标签识别，不能只靠颜色。

---

## 3.7 Patient Profile：个例趋势与中心级能力

### 当前真实状态

**受试者级图形已实现；中心级聚合未实现或未找到证据。**

完整页面包含基本信息、疗效指标历时变化、安全性历时变化、PD/Query、风险提示和关联事件索引。趋势图显示测量值、基线、参考范围、异常方向、CTCAE、风险关联和原始点明细。页面有中心筛选和中心/受试者树，但主体内容仍是当前受试者。

### 证据路径/API

- 趋势图、参考范围、基线、异常和 CTCAE：`frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx:241-371`
- Patient Profile 页面：`frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx:638-815`
- 中心筛选/受试者树：`frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx:375-472`
- 受试者级疗效与安全性图：`frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx:731-745`
- 路由挂载：`frontend/src/App.jsx:15542-15552`
- 三个真实项目均返回 `efficacy_trends`、`safety_trends`：
  - `services/api/app/rux_monitoring_service.py:245-263`
  - `services/api/app/mgk10_sar_monitoring_service.py:230-241`
  - `services/api/app/my009_monitoring_service.py:358-376`

### 缺口

1. 中心筛选只限制受试者选择，不会生成中心层面疗效/安全性分布、异常聚集或受试者比较。
2. 未找到试验级/中心级 Patient Profile 聚合 API。
3. 当前图表为自定义 SVG，而说明书提到可采用成熟图表库；缩放、密集点、缺失值和多单位处理未核实。
4. AE、病史、CM 主要出现在关联事件索引/Timeline，不是完整的 Profile 纵向整合面板。
5. 盲态保护、不同参考范围、计划外访视和同日重复测量虽然适配器有设计记录，但未完成浏览器验收。
6. “疗效趋势属于 Patient Profile”已满足代码结构，但数据科学性未完成跨项目验证。

### 医学风险

- 把中心筛选树误认为中心级聚合会掩盖中心异常聚集。
- 不同实验室参考范围或单位被错误连成一条趋势线，可能产生虚假的恶化/改善。
- 基线规则错误会影响变化值、应答和疗效解释。

### 建议编码分片

**P8-E1：受试者 Profile 科学性收口**

- 指标身份包含检测项目、单位、方法/参考范围组；
- 明确基线规则、计划外访视、重复测量和缺失点；
- AE/MH/CM/IP/实验室/疗效共享同一事件和风险关联。

**P8-E2：中心级 Profile**

- 新增中心级聚合 API 和页面模式；
- 提供受试者分布、异常聚集、开放高风险、指标恶化人数和下钻；
- 不将中心统计偏离自动解释为违规。

### 真实验收方式

- 每项目至少选择 3 名受试者，逐点与原始 listing 对账。
- 检查数值、单位、参考范围、基线、变化值、异常方向、CTCAE 和风险链接。
- 中心模式必须展示中心聚合结果，并可下钻到贡献受试者；不能只是切换受试者。
- 盲态项目不得显示或推断真实治疗组。

---

## 3.8 CM 与试验药物边界

### 当前真实状态

**受试者视图层已明确实现；全规则链路仍需回归。**

前端泳道定义将 CM 标为“合并用药（非试验用药）”，试验药物给药、发放、依从性和剂量调整进入独立 IP 泳道。RUX、MG-K10、MY009 真实项目适配器也分别使用不同来源域。

### 证据路径/API

- 前端泳道边界：`frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs:1-20`
- 试验药物细分类别：`frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs:23-35`
- RUX：CM 与 ECB 独立，`services/api/app/rux_monitoring_service.py:755-825`
- MG-K10：CM 与 EX 独立，`services/api/app/mgk10_sar_monitoring_service.py:635-725`
- MY009：`CM/CM1` 与 `DA/EX/EX2/EX3` 独立，`services/api/app/my009_monitoring_service.py:45-46,836-948`
- 页面底部边界说明：`frontend/src/App.jsx:2824-2828`
- 相关测试存在：`tests/test_rux_monitoring_service.py:141-178`

### 缺口

- 本次未完整遍历所有规则模板、风险装配和独立 AI 输出，不能证明任何入口都不会把试验药物写入 CM。
- 不同 EDC 中“背景治疗”“救援治疗”“非试验用药”和“试验药物”字段可能命名相近，需要项目级映射确认。
- dose adjustment、暂停、重启、依从性在 Checklist 的主类别是否稳定独立，未核实。

### 医学风险

CM/IP 混用会直接破坏禁限用药、依从性、给药调整、AE 处理和 PD 判断，是 P8 的硬关闭项。

### 建议编码分片

**P8-F1：领域边界验证器**

- 任何 `concomitant_medication` 映射不得指向 IP 角色；
- 任何 dose adjustment/administration/adherence 不得进入 CM；
- 背景治疗、救援治疗和非药物治疗各自保留领域身份。

### 真实验收方式

- 三个项目分别抽取真实 CM、EX/EC/DA/IP 记录逐条对账。
- 在 Checklist、Timeline、Profile、证据弹层和导出中检查领域一致。
- 注入“药名相同但用途不同”的边界病例，系统必须按数据域和方案角色区分，而不是仅按药名。

---

## 3.9 同页叠加层与跨视图互开

### 当前真实状态

**从 Checklist 出发的同页工作区已实现；双向状态恢复未完成运行态证明。**

点击风险后，在 Checklist 同页打开 `RiskEvidenceDock`，包含风险处置、Subject Timeline、Patient Profile、AE/MH 核查、来源证据和批次历史。Timeline/Profile 在 Dock 内有嵌入视图，也可打开完整页面。

### 证据路径/API

- 同页 Dock 挂载：`frontend/src/App.jsx:2771-2823`
- Dock 六个页签：`frontend/src/App.jsx:3139-3166`
- 内嵌 Timeline：`frontend/src/App.jsx:2884-2912`
- 内嵌 Profile：`frontend/src/App.jsx:2915-2935`
- 完整视图打开与焦点风险传递：`frontend/src/App.jsx:3158-3159`
- 返回 Checklist 时保留风险 ID：`frontend/src/App.jsx:15448-15466`
- 深链合同：`services/api/app/medical_monitoring_summary.py:40-162`
- 路由状态测试存在：`frontend/src/features/medical-monitoring/medicalMonitoringRouteState.test.mjs`

### 缺口

1. 说明书要求关闭叠加层后恢复筛选、排序和滚动位置；当前 Checklist 的筛选/排序是组件本地状态，切换完整页面后组件是否重建并丢失状态，未核实。
2. 完整 Timeline/Profile 中未见可直接打开风险证据 Dock 的对称交互；主要依赖“返回医学监查”。
3. `onOpenSubjectView` 使用独立页面状态而非真正 overlay；用户可能仍需来回切页。
4. 风险变更或被新实例取代时，旧深链是否自动指向当前实例，未核实。

### 医学风险

上下文丢失会导致用户回到错误受试者、错误风险或错误筛选集，尤其在连续复核数十条风险时影响效率和判断一致性。

### 建议编码分片

**P8-G1：统一工作区状态**

- 将筛选、排序、滚动位置、选中风险和 Dock 页签写入监查路由状态；
- 完整 Timeline/Profile 也以同一 overlay controller 打开风险；
- 保持 `risk_instance_id` 为唯一焦点。

### 真实验收方式

按顺序执行：

1. 组合筛选 Checklist；
2. 滚动到中段并选择风险；
3. 切 Timeline；
4. 切 Profile；
5. 打开 AE/MH；
6. 打开来源原文；
7. 返回 Checklist。

必须保持项目、受试者、风险、筛选、排序、滚动位置和已读状态；不得新开浏览器页面。

---

## 3.10 未读、增量变化与批次历史

### 当前真实状态

**基础实现存在，P8 运行态未核实。**

Checklist 有未读点；点击风险时调用已读动作。后端风险快照支持 `batch_delta`，历史 API 返回每个实例的数据来源、规则和引擎变化，并保存冻结证据与当时处置。

### 证据路径/API

- 未读点：`frontend/src/App.jsx:2142-2147`
- 点击风险后标记已读：`frontend/src/App.jsx:2799-2805`
- `batch_delta` 排序与显示：`frontend/src/App.jsx:2031-2040`
- 风险历史 UI：`frontend/src/App.jsx:2938-3015`
- 风险历史 API：`services/api/app/main.py:3418-3486`
- 统一风险快照与 rollup：`services/api/app/medical_monitoring_summary.py:280-414,717-793`

### 缺口

- “已读”是否绑定风险来源版本并在改值/重开后重新变为未读，未完成运行态验证。
- 风险状态迁移在全批次中的 `risk_key` 匹配、取代、重开和无法匹配仍是说明书列出的缺口。
- 历史冻结证据对所有真实项目是否完整，未核实。

### 医学风险

风险更新后未重新标未读可能导致医学经理漏看关键改值；已读后风险直接消失则会破坏工作连续性。

### 建议编码分片

**P8-H1：风险身份与未读回归**

- 用来源版本 CAS 管理已读；
- 新增、变化、重开和需重审均产生新未读版本；
- 已读仅改变展示状态，不删除风险。

### 真实验收方式

使用两个连续真实 listing 快照制造：新增、改值、删除、持续、解除、重开。逐项验证风险身份、未读、历史和处置迁移。

---

## 3.11 桌面端优先、信息密度与视觉层级

### 当前真实状态

**代码以桌面布局为主，同时保留移动响应式；真实视觉验收未完成。**

Checklist、风险 Dock、Timeline 和 Profile 均有专属桌面布局。Timeline 画布保留较大固定宽度，Profile 使用左侧受试者树和右侧主区。

### 证据路径

- 风险工作区布局：`frontend/src/styles.css:4175` 起
- Checklist：`frontend/src/styles.css:4212` 起
- 风险 Dock：`frontend/src/styles.css:4404` 起
- Timeline：`frontend/src/styles.css:5671-5903`
- Profile：`frontend/src/styles.css:6524-7001`
- 低于 900px 的响应式规则仍存在：`frontend/src/styles.css:18542` 起
- 说明书桌面优先要求：`医学监查子系统说明书.md:1981-1992`

### 缺口

- 本次没有完成 1440px 以上真实浏览器视觉 QC。
- 风险 Dock、Timeline 明细卡和 Profile 多段面板可能产生信息重复；是否符合“清爽、中等信息密度”未由真实用户验证。
- 全局移动端规则会把监查复杂布局降为单列；虽然没有删除功能，但可能增加 CSS 冲突面。
- 页面中仍有较多边界说明和技术失败文字，是否只在必要时出现未核实。

### 医学风险

视觉过载会降低高风险项识别速度；主次颠倒会让原始事实和医学处置被技术状态淹没。

### 建议编码分片

**P8-I1：桌面视觉验收与减法**

- 以 1440px、1728px 为验收视口；
- 首屏只回答“现在复核什么、为什么、下一步做什么”；
- 技术版本、哈希、队列和日志仅在审计详情；
- 移动规则不影响桌面组件结构。

### 真实验收方式

- 使用真实项目完成最大化窗口逐屏截图和逐按钮检查；
- 检查文字溢出、卡片层级、横向滚动、Dock 尺寸、Timeline 密度和 Profile 图表可读性；
- 让资深医学经理在不看说明的情况下完成 10 条连续复核。

---

## 3.12 试验级、中心级和受试者级汇总

### 当前真实状态

**后端风险 rollup 有基础；中心级受试者视图不足。**

统一风险快照后端能够输出试验、中心和受试者 rollup；Checklist 可按中心和受试者筛选。Patient Profile 的中心能力仍停留在筛选和受试者树。

### 证据路径/API

- 风险 rollup：`services/api/app/medical_monitoring_summary.py:717-793`
- Checklist 中心/受试者筛选：`frontend/src/App.jsx:2043-2125`
- Profile 中心筛选树：`frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx:375-472`

### 缺口

- 缺中心级 Patient Profile 和中心级 Timeline 聚合。
- 缺从试验汇总到中心、再到受试者和风险证据的完整浏览器演练。
- 中心聚集信号不能自动等同于违规，当前 UI 的解释边界未核实。

### 医学风险

只提供受试者列表而无中心聚合，无法支持核查前中心风险聚集识别；反之，未经医学解释的统计偏离可能误伤中心。

### 建议编码分片

**P8-J1：三级只读投影**

- 统一试验/中心/受试者汇总 API；
- 中心聚合只作为线索，必须展示分母、覆盖率、贡献受试者和数据完整性；
- 所有下钻回到同一风险实例。

### 真实验收方式

从试验总览选择高风险中心，下钻到受试者，再打开风险、Timeline、Profile 和来源；各层计数必须可加总、可解释且不复制状态。

---

## 3.13 与医学写作子系统的接口与冲突

### 当前真实状态

**后端业务边界较清楚，前端共享文件冲突风险高。**

医学监查有独立的前端 feature 目录、API 客户端、真实项目服务、风险仓储和 AI 持久化库。医学写作与医学监查通过同一总壳层和共享合同运行，监查路由状态测试明确要求保留医学写作查询参数。

但是，医学监查主页面、风险 Checklist、证据 Dock 和总路由仍直接定义在超过 1.5 万行的 `frontend/src/App.jsx` 中；监查和写作样式共同存在于超过 2 万行的 `frontend/src/styles.css`。这是并行开发最主要的冲突面。

### 证据路径

- 独立监查组件：`frontend/src/features/medical-monitoring/`
- 监查主页面仍位于：`frontend/src/App.jsx:2043-3335`
- 总路由同时挂载监查和写作：`frontend/src/App.jsx:15510-15569`
- 全局样式：`frontend/src/styles.css`
- 监查 AI 仓储明确不复用医学写作表：`services/api/app/monitoring_ai_repository.py:46`
- 路由状态保留写作参数：`frontend/src/features/medical-monitoring/medicalMonitoringRouteState.test.mjs:77-104`
- 说明书写入所有权：`医学监查子系统说明书.md:2622-2725`

### 缺口

1. 监查主工作区尚未完全从 `App.jsx` 拆成独立模块。
2. CSS 缺少完整监查作用域；全局类名如 `.panel`、`.section-title`、`.tag` 可能被并行改动影响。
3. 共享 contracts 文件体积很大，新增字段时容易对医学写作造成破坏性校验变化。
4. 总系统来源、项目和方案事实共享接口存在设计，但实际消费者兼容性未在 P8 本轮核实。

### 医学风险

并行开发冲突可能使一次医学写作视觉修改破坏 Timeline/Profile，或使监查模型字段变更导致写作导出/编辑器回归。

### 建议编码分片

**P8-K1：前端模块隔离**

- 将 `MonitoringPage`、`RiskChecklistTable`、`RiskEvidenceDock` 迁入 `features/medical-monitoring/`；
- 使用 `.medical-monitoring-shell` 作用域或 CSS Modules；
- `App.jsx` 只负责路由和稳定 props。

**P8-K2：共享契约兼容层**

- 监查新增字段默认可选；
- 独立导出监查 DTO，不让写作模型承担监查校验；
- 对共享 `project_id`、Source Registry 和方案事实建立消费者契约测试。

### 真实验收方式

1. 构建医学监查前端和医学写作前端。
2. 运行两套各自核心测试。
3. 在同一项目中来回切换医学写作和医学监查，确认路由参数、项目身份和页面状态不互相覆盖。
4. 对共享文件生成变更清单，任何破坏性字段变更必须明确迁移两个消费者。

---

## 4. P8 建议实施分片与顺序

| 顺序 | 分片 | 目标 | 退出条件 |
|---|---|---|---|
| 1 | P8-A1/A2 | 权威风险分类、Checklist 查询和状态 | 七列、筛选、排序、导出、类别全部由后端合同驱动 |
| 2 | P8-B1/B2 | 可读证据正文与规则推导 | 三项目真实风险无需先开原文即可完成医学复核 |
| 3 | P8-C1 | 医学确认与组织审批状态分离 | 用户确认后不再出现第二层医学批准 |
| 4 | P8-F1 | CM/IP/背景治疗/救援治疗边界 | 所有入口和导出保持领域一致 |
| 5 | P8-D1/D2/D3 | Timeline 高密度布局、风险关联和配色 | 真实浏览器三项目高密度/稀疏/边界病例通过 |
| 6 | P8-E1/E2 | 受试者 Profile 科学性与中心级聚合 | 原始点对账通过，并有真实中心聚合而非筛选树 |
| 7 | P8-G1/H1 | 同页交互、未读、批次历史和状态恢复 | 完整连续复核流程不丢上下文 |
| 8 | P8-I1/J1 | 桌面体验和三级汇总 | 1440/1728 桌面验收与试验→中心→受试者下钻通过 |
| 9 | P8-K1/K2 | 与医学写作并行开发隔离 | 监查模块独立挂载，双子系统构建和回归通过 |

每个分片均应执行：

1. 读取真实来源和当前任务记录；
2. 编写最小实现；
3. 运行专属测试；
4. 运行相邻共享契约测试；
5. 打开真实页面逐按钮验收；
6. 以真实项目复核科学性；
7. 记录问题、修订、再测，直到退出条件通过。

---

## 5. P8 真实验收矩阵

### 5.1 项目矩阵

至少使用 RUX、MG-K10、MY009 三个真实研究。产品输入必须从各项目原始方案和原始 listing 重新生成，不得使用 Subject Timeline/Patient Profile 示例的过程数据冒充产品输入。

### 5.2 受试者矩阵

每项目至少覆盖：

- 事件密集受试者；
- 数据稀疏受试者；
- 计划外访视受试者；
- 部分日期或持续事件受试者；
- 有 AE/MH/实验室关联风险受试者；
- 有 CM 和试验药物变化同时存在的受试者；
- 有疗效和安全性多时间点的受试者。

### 5.3 功能矩阵

必须真实点击和验证：

- Checklist 七列排序和筛选；
- 未读、已读、新增、变化、重开；
- 风险证据正文、原文、系统规则；
- 医学确认、驳回、补资料、Query 草稿；
- Timeline 缩放、风险聚焦、泳道明细；
- Patient Profile 疗效/安全性图、原始点和风险焦点；
- AE/MH 核查；
- 批次历史；
- 试验→中心→受试者下钻；
- 同页切换与返回状态恢复；
- 医学写作与医学监查来回切换。

### 5.4 视觉矩阵

- 桌面优先：1440×900、1728×1000；
- 最大化浏览器窗口；
- 无文字溢出、元素重叠、错误换行和不可解释横向裁切；
- Timeline 所有事件类别颜色可辨，且不只依赖颜色；
- Profile 图表数值、单位、参考范围和标签可读；
- 技术日志、哈希、队列和泛化警告不占据医学主工作区。

### 5.5 医学关闭项

以下任一失败均不得宣称 P8 完成：

1. CM 与试验药物混用；
2. 实验室数值、单位、参考范围或日期错配；
3. 风险类别由标题变化而改变；
4. 用户确认后仍显示待医学批准；
5. Timeline 不以实际访视/日期为轴；
6. 高密度事件相互遮挡且无法展开；
7. Patient Profile 将不同单位或不同参考范围错误连线；
8. Safety/PV 复制风险状态或形成第二套台账；
9. 从 Timeline/Profile 返回后切换到错误受试者或风险；
10. 医学监查变更破坏医学写作核心流程。

---

## 6. 最终差距清单

### P0：编码前必须先解决

1. 后端权威风险类别替代前端文本启发式分类。
2. 可读证据统一合同和实验室医学句式。
3. CM/IP/背景治疗/救援治疗的全链路领域验证器。
4. 用户医学确认与组织 Query 审批状态分离。

### P1：P8 主体能力

1. Timeline 高密度和边界病例真实浏览器回归。
2. Patient Profile 原始点科学性核对。
3. 真正的中心级 Profile/风险聚合。
4. Checklist、Timeline、Profile、AE/MH、证据和历史的双向同页交互。
5. 未读、增量变化、重开和跨批次风险身份回归。

### P2：集成和发布前

1. 从 `App.jsx` 和全局 CSS 中隔离医学监查业务组件。
2. 补保存视图、导出和三级汇总交互。
3. 完成 1440/1728 桌面视觉验收。
4. 完成医学写作与医学监查并行回归。

---

## 7. 本次只读盘点的完成边界

本次已完成：

- 按前端、API、数据模型、真实项目适配器、测试和路由逐项核对；
- 将“代码存在”“测试存在”“真实运行验证”分开；
- 对 Checklist、证据、Timeline、配色、Patient Profile、CM/IP、同页交互、桌面体验、确认语义和医学写作冲突逐项给出编码分片与验收方式；
- 明确记录所有未核实项。

本次未完成且不得被视为已完成：

- 未修改任何产品代码、数据库或前端；
- 未重新执行自动化测试；
- 未完成当前运行页面的真实浏览器验收；
- 未证明 P8 已达到生产上线条件。

下一安全动作是按 §4 的顺序启动 P8-A1/A2，并以三个真实项目建立首轮 Checklist 与证据闭环；在此之前，不应继续以新增页面装饰替代风险分类和证据合同收口。
