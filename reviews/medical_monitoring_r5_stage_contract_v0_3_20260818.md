# 医学监查 R5 风险驾驶舱、中心图谱与 Subject Workspace 阶段合同 v0.3

日期：2026-08-18  
状态：`R5_CONTRACT_V0_3_FOR_ARTIFACT_FREEZE`  
上游：System Design v1.1、R0–R8 实施计划 v1.1、`ACCEPT_R4_STAGE`  
目标用户：懒惰、视觉敏感、数据敏感、风险敏感、中文原生且不熟悉计算机/AI 的资深医学监察员

## 1. 阶段目的与非目的

R5 把 R4 已接受的风险、中心模式、项目聚合、正反证、Query、来源和受试者时间投影，转换为能快速回答四个问题的桌面工作面：

1. 本次数据或分析相对可比基线发生了什么变化；
2. 当前仍需优先查看的中高风险在哪里，是否形成中心/项目模式；
3. 该风险落在哪个受试者、访视、实际日期、事件或区间；
4. 提醒的依据、反证、原始 listing、方案/IB 和 Query 是什么。

R5 不重新判断医学风险，不复制 R4 成为第二权威，不把浏览转成待办，不要求清空队列或显示“人工复核未完成”。Query 只展示/编辑结构化草稿；不发送、回复或关闭。安全性/PV 可作为同一医学风险的领域/协作标记，但本阶段不扩展系统安全设计或专项测试。

## 2. 权威与投影边界

- R4 risk/project/site/member/visibility/change/coverage/cutoff/denominator/Query/ensemble/adjudication 对象是只读输入权威。
- R5 只能创建 audience projection、视图状态、深链和返回上下文；不得回写或重算 R4 医学处置、风险等级、生命周期、分子、分母或裁决。
- 同一页面显示的项目、中心、受试者数字必须引用同一 `project_ref + run_ref + snapshot_ref + cutoff_ref + authority_hash`。
- R4 无值或 `not_evaluable/not_applicable/partial/truncated/failed` 必须按原义投影；不得用 0、空白、百分比或“暂无风险”替代。
- `query_count`、`clue_count`、`center_pattern_count`、`individual_risk_count`、`affected_subject_count`、`event_count` 必须分层显示，禁止相加为一个“风险总数”。
- evaluation set 与 projectable set 分离；隐藏成员/中心不能通过差额、率或 tooltip 被推断，且不得进入深链。

## 3. 资深医学监察员的默认路径

### 3.1 项目入口

默认进入“项目风险概览”，不是来源配置、运行日志、AI 候选、保障任务或 Checklist。首屏从上到下只保留：

1. 一行项目身份：项目、当前数据截止、当前/对照运行、覆盖状态；异常才展开说明。
2. 一行“本次变化”：新增、升级、持续、重开、降级、已解除、不可比较；初始全量明确写“首次全量”。
3. 主从分栏：左侧为当前全部高/中风险与风险簇，低风险折叠；右侧为当前选中风险的 Inspector。
4. “中心风险图谱 / 热点受试者”一级切换，不在同一首屏堆满所有统计。

从项目或中心某个风险进入正确 Subject Workspace 的操作不超过一次；从已定位的风险/事件到原始来源再不超过一次。返回后必须恢复项目/中心、筛选、排序、分组、滚动、选中风险、Inspector 宽度/展开和时间窗。

### 3.2 中心入口

默认显示中心风险图谱：领域×风险等级热图、当前/前次变化、重复模式、热点受试者和 coverage。受试者目录/统计为一级切换视图。中心按稳定中心身份或用户明确选择的可解释指标排列，不默认按风险率做红黑榜。

### 3.3 Subject Workspace

统一身份栏下固定三个一级子视图：

- `受试者医学旅程`：默认入口；访视/阶段轴、八域事件轨道和风险锚点。
- `指标趋势`：完整 Profile；疗效、安全、实验室、生命体征、PRO/PK/生物标志物等所有可用指标小多图和表格。
- `事件明细`：完整 Timeline；点/区间、重叠、顺序、关系和编号明细。

三者共享相同 temporal spine、轴模式、时间窗、缩放、选中事件/风险、交叉高亮和来源抽屉；切换不得重置上下文或重新推断时间。

## 4. 项目风险驾驶舱合同

- “变化优先”与“当前全量”同时存在：增量不能隐藏长期持续的中高风险；已解除只进入变化/历史，不冒充当前风险。
- 变化原因至少分为数据录入/修订/撤回、知识/方案/IB、规则、mapping/canonical fact、模型/执行配置、方法/分母/覆盖、用户实际决定、不可比较。
- 临床/数据变化与分析管线变化分栏或标签区分；不能把规则/模型变化写成受试者状况变化。
- 风险列表默认顺序：高风险 → 中风险 → 低风险聚合；同级按新发/升级/重开、证据充分度、受试者/中心稳定序，不按“未读/待行动”。
- 风险簇只折叠相同稳定风险类型/领域/中心模式关系；展开后保留每个 risk instance 身份。
- 普通用户面不显示 risk key、instance id、snapshot id、provider/model/attempt/backend/hash；这些只作为深链/审计的隐式身份。

## 5. 中心风险图谱与数量合同

每项可比较指标同时显示：

- 受影响受试者数；
- 事件/机会数（若适用）；
- 明确的分母和比例/暴露调整率；
- cutoff、coverage、排除规则与计算版本；
- 小样本、短随访、覆盖不足、不同招募阶段或不可比较提示。

分母为零、未知、未闭合或 coverage 不足时只显示“暂无法计算”及原因，不显示 0%。点击数量/率可展开合法的分子和分母成员；不得暴露 hidden set。中心模式与个体风险分开；单例不能被命名为“中心系统性风险”。不生成黑箱综合评分或惩罚性排名。

## 6. Risk Inspector 合同

桌面主从分栏右侧至少按以下顺序展示：

1. 医学风险标题、领域、等级、当前/变化状态、受试者/中心；
2. “为什么提醒”：依据、发现、建议核实；
3. 支持证据与排除/反证；
4. 既有基座条目及各模型独立结论；
5. 确定性核对与独立裁决；
6. 原始事实、listing 行/单元格、方案/IB/知识条款；
7. Query 草稿和风险/补录历史；
8. “在受试者医学旅程中查看”深链。

多模型一致只叫“多个分析结果一致”，不叫医学真值；单模型独有发现不被隐藏。高风险即使裁决支持/反对也持续可见。普通首层不显示模型厂商或技术运行标识；需要比较时按“分析一/分析二/独立核对”展示，详细运行身份仅在审计层。

## 7. Subject Temporal Spine 与 Patient Journey

- 默认连续实际日期轴；研究日为可切换投影；名义访视、实际访视、非计划访视、治疗阶段、首次/末次给药和 cutoff 叠加在同一轴。
- 不能把访视间事件吸附到名义访视；研究日锚点缺失时不伪造研究日。
- 日期完整的点/区间进入主轴；部分日期显示不确定区间，冲突日期显示冲突范围，日期缺失进入独立“日期待核对”区域。
- 八个主轨道：AE、MH、CM、IP 给药、检验与检查、住院与操作、症状与疗效、方案符合性。`症状与疗效` 是一个主域，内部用 `症状/疗效/量表/结局/趋势` subtype 区分事件与纵向变化，不再创建第九条疗效轨道。轨道由方案与数据自适应；不适用与未提供分开解释。
- `background treatment`、`non-drug treatment` 等旧输入只有在冻结的项目映射明确成立时，才分别进入 CM 或相应治疗 subtype；没有可接受映射时按 unknown fail-closed，进入“领域待确认”，不得塞入 `OTHER`，也不得凭文件名、项目名或测试夹具决定归类。
- 每个轨道支持点/区间、折叠、语义缩放、时间 brush 和风险优先；长文字不塞入轨道，使用稳定编号短块并与下方明细对应。
- 首屏始终优先保留全部中高风险、关键给药变化、严重/重要 AE、关键疗效/检查变化；低风险/普通事件可按域聚合。
- AE/MH 漏报同时投影到风险、相应临床事件/线索、Profile 异常点和 Timeline；补录后保留“原疑似漏报—后续已补录记录”的匹配历史，不删除原提醒历史。

## 8. 事件与风险的非颜色编码

先区分“已记录事件”和“风险提醒”，再区分临床域，最后表达等级：已记录事件使用域形状/区间线；风险覆盖层唯一固定为任何事件域都禁用的“双折角徽标＋外圈”，并直接写“域内风险类型·等级”。事件形状不得使用双折角徽标，方案符合性事件继续使用单旗标，因此不会与风险覆盖层混淆。每个域再有稳定的 2–4 字中文短标签和线型；颜色仅辅助等级：

普通受众层风险等级 closed enum 为 `critical/high/medium/low`，原生中文固定显示为 `紧急/高/中/低`。只有 R4 权威投影明确给出 `critical` 时才显示“紧急”，R5 不得把 `high` 自行升级为 `critical`；旧 `severe/moderate/mild` 仅可经冻结映射转为 `高/中/低`，缺映射即 fail-closed。页面、导出和深链使用同一词汇表。

| 域 | 事件短标签 | 基础形状/线型 | 风险示例 |
|---|---|---|---|
| AE | `AE` | 圆角矩形点；持续事件为实线区间 | `AE漏报·中`、`严重性核查·高` |
| MH | `MH` | 书签形；既往持续为点划区间 | `既往史漏报·中`、`入排相关·高` |
| CM | `合并用药` | 胶囊形；疗程为细实线区间 | `禁用药·高`、`适应证不一致·中` |
| IP 给药 | `试验药` | 六边形；给药/暂停/恢复为阶梯线 | `给药偏离·高`、`暴露缺口·中` |
| 检验与检查 | `检验/检查` | 方形点；趋势为折线 | `异常未解释·中`、`漏报AE线索·高` |
| 住院与操作 | `住院/操作` | 门框形；住院为粗区间 | `住院未关联AE·高` |
| 症状与疗效 | `症状/疗效` | 圆点；纵向变化仅用趋势线型表达 | `疗效评估矛盾·中`、`症状漏报AE·中` |
| 方案符合性 | `方案符合` | 旗标形；访视窗为括号区间 | `入排不符合·高`、`访视窗偏离·中` |

不得使用“已记录事项”“正式事实”“候选信号”“通用风险点”“只读xx”“Checklist”“待行动”“未读”等作为医学监查普通页面的结构标签。`信号`仅用于确指药物警戒/安全性信号。

## 9. 深链与返回上下文

`R5DeepLinkState` 至少绑定：project、run、snapshot、cutoff、site、subject、risk instance、view、spine、axis mode、start/end、visit/event/risk anchor、source locator、return-context key。所有身份在目标 projection 内逐项核验；任一不一致、不可投影成员或 artifact 缺失即 fail-closed，显示中文修复路径，不回退到相邻受试者或“最接近”记录。

`R5ReturnContext` 分成两层：可复制 URL 的 canonical state 保存权威身份、目标 view、axis/window 与 anchor；只在当前客户端恢复的 ephemeral state 保存滚动、Inspector 宽度/折叠、临时展开。验收比较 canonical hash 与声明的 ephemeral fields，不要求 URL 字节完全相同。返回只恢复浏览状态，不写入风险或用户决定。

## 10. Typed projection exact contract

R5 第一纵切至少定义不可变对象：

- `R5AuthorityReceipt`：逐项绑定 public projection kind/id/content hash、evaluation content identity、visibility decision id/hash、project/run/snapshot/cutoff、source revision-content pairs 与 audience contract；禁止用一个模糊总 hash 代替。R4 未设置 cutoff 时保留 `null`，不得编码为空字符串、占位词或推定日期。
- `R5ProjectionInstance`：分开保存 opaque run/snapshot 审计身份与 replay-stable content identity。
- `R5ChangeBand`：closed kind 至少包含 `initial_current/new/upgraded/continued/downgraded/resolved/reopened/superseded/not_evaluable/not_comparable`；原因平面分开 data、knowledge、rule、mapping、model、method、coverage、denominator、user decision。
- `R5CurrentRiskSet`：当前高/中全量与低风险聚合；resolved/closed 只进变化/历史，展开仍保留每个 risk identity。
- `R5QuantitativeMeasure`：authoritative value ref、numerator kind/member refs/value、denominator kind/member refs/exclusions/value/state、unit/rate state、coverage/cutoff/evaluation limits 与合法成员展开 refs；R5 不重算。
- `R5ProjectCockpitProjection`；`R5CenterMapProjection/Cell` 明确 pattern/individual 两层、stable order，schema 不允许 score/rank/top-N 红黑榜字段。
- `R5RiskInspectorProjection`：显式引用 `ReferenceBaselineItem/BaselineAssessment/AnalysisAttempt/WorkerAnalysisOutput/EvidenceVerification/ConflictVisibility/AdjudicationBinding` 及 D10 `ModelEvidence` provenance；基座不是 gold，单模型没有 consensus。
- `R5DeepLinkState`、`R5ReturnContext`：canonical URL state 与 ephemeral client state 分离。
- `R5SubjectWorkspaceState`、`R5TemporalSpineProjection`、`R5VisitNode`、`R5JourneyTrack`、`R5JourneyEvent`、`R5RiskAnchor`、`R5PendingDateItem`：共用 spine/axis/window/selection；域 enum 固定八类，unknown 不静默塞入 OTHER。
- `R5AEMHMatchHistory`：candidate ref、later fact ref、`exact/ambiguous/rejected` match state、identity evidence 和 snapshot transition；补录不删历史、不自动关闭。
- `R5AudienceEncodingRegistry`：一级区分 event/risk，二级使用 domain shape/短标签/线型，三级表达 closed severity `critical/high/medium/low`；注册表必须恰好覆盖八域且每域唯一，`症状与疗效` 固定 `circle + trend line_style`，不允许第二事件形状；`R5AudienceLexicon` 固定 `紧急/高/中/低`、八域中文标签与禁词，并保存 `症状与疗效` subtype 及旧治疗域的冻结映射规则。

上述 Markdown 是用户/工程审阅视图；唯一机器权威为 `artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json`。该文件逐对象冻结 exact keys、type、cardinality、nullability、全部 closed enums、跨字段/引用/哈希 invariant、风险覆盖层、unknown/legacy-domain policy、性能口径及覆盖每个 R5 leaf 的唯一 mapping。mapping 明确区分 `r4_direct/derived/canonical_derived/ui_state/contract_constant/deferred`：`canonical_derived` 仅用于由同一 R5 对象非哈希字段计算 canonical SHA-256，不接受客户端提供值；R4 direct/derived 的每条 `module:Class.field[.nested_field]` 必须在当前冻结 R4 dataclass 中逐段可解析。尚无足量上游 public contract 的当前风险集、中心语义格、逐成员定量度量、Inspector 证据叶、Subject Temporal 与 AE/MH history 必须诚实标记具名 deferred contract，不得用计数字段或泛称 source path 伪造可推导性。Authority Receipt 的 projection kind 由具体 adapter variant 绑定，不允许全局固定为 D10。Deep Link 的项目/运行/快照/中心/受试者身份来自并核对 R4 target，不能以 UI state 作为权威。嵌套状态必须使用有 exact keys 的命名对象，不允许裸 `json`；具有业务闭集的字段不允许裸 `str`。字段多一个、少一个、类型/基数/nullability 不同、映射缺叶、source 不可解析、invariant 缺失或 enum 外值均拒绝；不得以 Markdown 概述替代机器合同。

所有对象须 canonical serialization、确定性 content hash、closed vocabularies、重复身份/引用检查和 exact authority receipt。R5 adapter 只能读取 R4 公开字段。

### 10.1 R4 → R5 字段映射

| R5 只读投影 | 唯一上游字段/对象 | 禁止行为 |
|---|---|---|
| authority receipt | D09/D10 typed project/run/snapshot/cutoff、public projection identity/hash、visibility、source revision-content pairs | 只绑总 hash；从 UI 行反推 |
| current risk set | R4 public risk identity、priority、R2 lifecycle/current state、visibility projectable set | 由未读/待办推断当前；把 resolved 当当前 |
| change band | D09/D10 change decision/ledger、R2 lineage | 由前端两次计数相减；把模型/规则变化写成临床变化 |
| quantitative measure | D09/D10 numerator ledger、denominator、coverage、cutoff、evaluation limits | R5 重算分子/分母/率；混加 query/clue/pattern/risk |
| center cells/patterns | D09 site pattern unit、D10 project/cross-site projection、stable site identity | 单例升级为中心模式；中心 score/rank |
| Inspector baseline/models | ensemble reference/baseline/attempt/output/verification/conflict/adjudication 与 D10 model evidence provenance | 基座当 gold；单模型造 consensus；多数票隐藏 |
| subject workspace | R4 Journey/Profile/Timeline public projection、shared spine、risk/member/source refs | 另建时间权威；nearest subject/source fallback |
| Query | R4 typed three-part Query projection | 发送、回复、关闭或任务化 |

R5 只引用上游已验证值和 member refs，不自行计算医学数值。机械证明须逐字段确认：R5 value/content identity 可追到唯一上游 receipt；改变任一上游 identity/hash 后旧 R5 projection 必须拒绝；R4 文件 SHA 在 S1 前后完全不变。

### 10.2 禁止的语义分支

- 不得按 project/case/fixture/test id、文件名、synthetic sentinel、oracle、index、mutation class 或 hash 命名约定决定语义。
- 不得复制或重算 R4 风险、分子、分母、裁决；不得以渲染行数推断 coverage。
- 不得把 hidden/unknown/缺失当 0，不得 nearest subject/site/risk/source fallback。
- 不得以多数票隐藏高风险，不得把 reference baseline 当真值。
- 不得建立中心 score/rank/top-N 红黑榜，不得限制中高风险为 3–5 项。
- 不得访视吸附、用计划访视伪造实际日期、把 unknown domain 静默归入 OTHER。
- 不得由点击、筛选、缩放、切换、返回写入风险/用户决定，不得发送/回复/关闭 Query 或生成待办。
- 不得让 Profile/Timeline 各自维护第二时间状态，不得用移动端限制削减桌面专业内容。
- 不得在浏览器验收片之前启动 8911；不得触碰 R4、医学写作、真实项目/模型、生产或安全专项。

## 11. 分片顺序与完成证据

| 片段 | 范围 | Done 的非 LLM 锚点 |
|---|---|---|
| S0 | 合同冻结 | exact-key/closed-enum validator、挑战 registry 配额机械核验、canonical SHA、fresh reviewer `ACCEPT_R5_CONTRACT` |
| S1 | R4→R5 authority adapter | 每个 leaf exact receipt；project/run/snapshot/cutoff/visibility tamper fail-closed；重放/顺序同 content identity；R4 SHA 不变 |
| S2 | 第一条薄纵切 | 1 个项目风险→1 个中心模式→Inspector→正确 Subject Workspace 时间锚点→来源；1+1 操作；return canonical-equivalent；无临床写回 |
| S3 | 项目驾驶舱＋中心图谱完整化 | 分子/分母成员重建、计数层守恒、hidden 不泄露、stable-id 排列、无 score/rank |
| S4 | Risk Inspector/ensemble | 0/1/N、输入隔离、基座 source recheck、worker≠adjudicator、高风险/相互否定/baseline miss 不可隐藏 |
| S5 | Subject Workspace/Journey | 同一 spine/window/selection hash；日期不伪造；八域 unknown fail-closed；三视图同 anchor；match history append-only |
| S6 | 深链、返回、密度、可访问性 | 全身份逐项验证、不可用不邻近回退、键盘/非颜色编码、百/千事件与数十指标性能基准 |
| S7 | 产品最小接入＋真实浏览器 | 仅此片临时启动 8911；Playwright、1440×900/1600×1000 截图、console/network、点击/时长；验收后停止 |
| S8 | 阶段关闭 | focused＋R4 adjacent＋frontend build＋禁词＋浏览器任务＋独立视觉/医学 review 无 P0–P4 |

第一实现片固定为 S1：新建 `poc/medical_monitoring_ai_native_r5`，只读消费 R4 public projection，先完成权威 receipt/adapter；不得先修改产品 App 或医学写作。S1 接受后才实施 S2 薄纵切，S2 接受后才进入完整产品页面。

## 12. 挑战矩阵最低规模

冻结合同前最低 204 个独立 case，且每类最低配额逐项满足；不得用一个巨型 fixture 代替：

| 类别 | 最低例数 | 必测问题 |
|---|---:|---|
| authority receipt/project-run-snapshot-cutoff | 8 | 任一错配即拒绝 |
| R4 hash/version/visibility receipt | 8 | 缺失、过期、hidden 成员 |
| 首次全量/可比增量/不可比较 | 8 | 不伪造新增/解除 |
| 七类风险变化及原因平面 | 12 | 数据变化与规则/模型变化分开 |
| 风险计数层守恒 | 8 | risk/query/clue/pattern 不混算 |
| 分子/分母/率/单位 | 8 | 0/未知/未闭合不显示 0% |
| coverage/cutoff/small sample | 8 | partial/truncated/not evaluable |
| center pattern vs individual risk | 8 | 单例不冒充系统性模式 |
| center stable ordering/no ranking | 4 | 排序可见、非惩罚性 |
| Risk Inspector evidence order | 4 | 正反证、基座、模型、裁决、来源 |
| ensemble disagreement/high-risk visibility | 8 | 多数票不隐藏高风险 |
| deep link identity | 8 | project/run/site/subject/risk/spine 全核验 |
| return context | 8 | 筛选/排序/滚动/选择/时间窗恢复 |
| nominal/actual/unscheduled visit | 8 | 访视间事件不吸附 |
| calendar/study-day conversion | 8 | 缺锚点不伪造研究日 |
| partial/conflict/missing dates | 8 | 独立待核对区域 |
| eight-domain track adaptation | 16 | 不适用 vs 未提供；域内类型不混 |
| event/risk shape-label-line registry | 8 | 非颜色冗余编码 |
| AE/MH missed-reporting projections | 8 | 风险/事件/Profile/Timeline 一致 |
| later-recorded matching history | 8 | 历史保留、身份不重写 |
| source locator one-hop | 8 | 正确 row/cell/clause；错误不邻近回退 |
| audience lexicon forbidden terms | 8 | 普通页面禁内部/任务化/英语结构词 |
| interaction cannot mutate medical state | 8 | filter/zoom/click/back/replay 无副作用 |
| deterministic replay/order | 8 | 输入次序不改变内容或 identity |
| high density/performance | 8 | 百/千事件、数十指标、风险仍优先 |

25 类配额机械求和为 204；必须落成恰好 204 条独立 challenge registry 行和 204 条一一对应 quota ledger 实例。每行只属于一个 category，只含一个 mutation specification，并绑定唯一 `rule_id/planned_stage/test_locator/expected outcome/expected projection/required non-LLM anchor`；不得循环复用 case、用 `variant_index` 补数、跨类别重复记账或用一个巨型 fixture 代替独立测试。每行 exact keys 为 `case_id/category/precondition/single_mutation/expected_typed_outcome_or_error/forbidden_audience_output/stage_oracle_contract/severity`，`single_mutation` exact keys 为 `op/path/value`，`stage_oracle_contract` exact keys 为 `kind/planned_stage/rule_id/test_locator/expected_outcome/expected_projection/required_non_llm_anchor`。

S0 只接受“挑战规范已冻结”，不宣称 204 个医学/运行行为已执行或通过；S0 的非 LLM 锚点是 pinned exact schema、真实可解析的 R4 source paths、204 条唯一 specification 与独立 reviewer。每条 case 必须在其 `planned_stage` 创建真实 typed fixture、调用真实 validator/evaluator，并以测试结果和 canonical projection hash 或浏览器测量 trace 关闭；对应 stage 未执行通过前不得引用 S0 registry 声称功能完成。等级、症状与疗效 subtype、background/non-drug mapping、unknown→OTHER 禁止分支、双折角风险覆盖层、确定性重放和性能数据集必须各有独立 specification。

## 13. P0–P4 阻断规则

- P0：可能造成项目/中心/受试者串扰、来源破坏、不可恢复状态、严重医学事实颠倒或系统级不可用；包括 R4 authority 改写、浏览写医学处置、医学写作/保护区被动。
- P1：可能静默漏掉或错误隐藏高风险、SAE/AESI/重要趋势，或使用错误版本/证据/分子/分母/coverage/cutoff；包括严重日期/访视错位和身份错深链。
- P2：首屏核心监查任务、Inspector、中心聚合、来源定位、Workspace/Journey/Profile/Timeline、返回恢复或 AE/MH 历史实质错误/不可完成。
- P3：明显影响专业判断效率、任务点击/时长、中文易读性、图表逻辑、密度、键盘/非颜色编码、交互一致性或非核心数据准确性。
- P4：仍可复现的轻微视觉、禁词、文案、边界或一致性缺陷。

合同、第一纵切或阶段验收中出现任何 P0–P4 均返回 `REVISE`，修复后由同一独立 reviewer 复验；worker 不拥有 done。

## 14. 当前实现复用与淘汰边界

### 复用

- `medicalMonitoringRiskProjection.mjs` 的 scope identity 和守恒检查思路；但需扩展为 R4 D09/D10 分层计数和 authority receipt。
- `medicalMonitoringRouteState.mjs` 的 URL 状态、筛选/滚动恢复；升级为 run/snapshot/cutoff/spine/time-window/return-context 合同。
- `MedicalMonitoringRiskChecklist` 的键盘选择、排序/筛选和 dense row；改名/重构为风险列表，去除任务化词汇和旧状态排序。
- `ReferenceTimelineSvg`、Profile 趋势、R1 Patient Journey 的实际日期轴、点/区间和同步交互；统一进入 Subject Workspace，补齐八域/访视/部分日期/补录历史。
- 既有来源定位、风险历史和三分句 Query 的 audience 片段。

### 淘汰或从普通首屏移出

- `项目医学风险 Checklist`、`待行动`、`未读`、`个例优先队列` 等任务化信息架构。
- `风险上下文` 中普通展示 risk instance/key/snapshot 等技术身份。
- `Safety/PV` 英文结构标签、`只读来源原文片段`、locator kind 等研发表达；改为中文医学/来源语义。
- 当前 `ScopeSummary` 只按风险/待行动/未读排序且缺分母、coverage、cutoff 的“集中度”展示。
- 独立 Profile/Timeline 路由重复维护时间逻辑；保留专业内容，但统一由 Subject Workspace/Temporal Spine 管理。

## 15. 浏览器验收任务（R5-F 执行）

至少捕获并检查 1440×900/1600×1000 的以下状态：项目初始全量、可比增量、不可比较、中心小样本/不可评估、split Inspector、模型分歧、项目→Subject 深链、Journey 八域高密度、Profile/Timeline 同步、部分/冲突/缺失日期、AE/MH 补录历史、来源抽屉、返回上下文。窄屏只做灾难性降级，不牺牲桌面功能。

资深医学监察员任务：

1. 找出本次新增/升级的全部中高风险，并说明变化原因；
2. 判断某中心是否存在重复模式，同时展开分子、分母和 coverage；
3. 从风险一跳进入正确受试者/时间窗，再一跳打开原始 listing/方案条款；
4. 在旅程、指标趋势、事件明细间切换，确认同一访视/风险/时间窗保持；
5. 找出疑似 AE/MH 漏报及后续补录匹配历史；
6. 返回项目页，确认筛选、排序、滚动、选中风险和 Inspector 状态恢复。

Done 需要：每项任务成功、身份/数字可重建、关键路径点击数达标、无禁词/内部标签、无桌面溢出/遮挡、截图和 Playwright evidence 完整、独立视觉与医学 reviewer 均无 P0–P4。

### 15.1 冻结的任务与性能预算

- 项目/中心风险卡 → 正确 Subject Workspace/风险时间锚点：最多 1 次主要操作；已定位风险 → 原始 listing 行/单元格或方案/IB 条款：最多再 1 次主要操作。
- 同一受试者在旅程/指标趋势/事件明细切换：1 次操作，时间窗/选择不可丢失。
- 返回项目/中心来源页：1 次操作，canonical return state 100% 恢复；ephemeral state 中滚动偏差不超过 24 px，Inspector 宽度偏差不超过 8 px。
- 1440×900 首屏 10 秒内可辨识项目身份/cutoff/coverage、变化摘要、全部当前高风险入口和中风险入口；不把中高风险截成 3–5 项。
- synthetic 基准：1,000 个事件、40 个指标、300 个风险锚点。S7 使用 frontend lockfile 固定的 Playwright/Chromium、production build、1440×900；记录硬件型号、OS、逻辑 CPU、内存、Playwright/Chromium/commit。cold=新 context 且无 HTTP cache，warm=同 context 第二次导航；每模式 7 次，nearest-rank p95。`navigationStart` 到风险列表/中心图谱/Inspector/Journey 控件均启用的 cold p95 ≤2.5 秒、warm p95 ≤1.5 秒；可信 pointer/keyboard event 到下一帧 canonical selection 更新的 brush/zoom/select p95 ≤100 ms；连续平移帧率 p05 ≥30 fps。超出时必须显示真实加载/降级状态且不隐藏中高风险，不得虚报性能通过。
- 所有浏览器任务均记录开始/结束时间、主要操作数、最终 project/run/snapshot/site/subject/risk/spine/source identity、截图与 console/network 结果。

## 16. S0/S1 写入边界、回滚与接受门

`ACCEPT_R5_CONTRACT` 前不得写实现。S0 只允许写：本合同、challenge registry/quota ledger/verifier、stage context/plan/review/metrics/acceptance record。S1 接受后唯一实现写域为 `poc/medical_monitoring_ai_native_r5/**`。

S1 只读 import `poc/medical_monitoring_ai_native_r4/**` public objects；禁止修改 `frontend/**`、`services/**`、`packages/**`、`runtime/**`、既有 R1–R4、所有 medical-writing 路径和真实项目资料；离线验证，不启动 8911。S1 独立接受后另开 product-integration allowlist，优先新建 `frontend/src/features/medical-monitoring/r5/**`，仅允许最小修改 `frontend/src/App.jsx`、`medicalMonitoringRouteState.mjs`、`medicalMonitoringApi.mjs` 及对应只读 API/测试；任何扩张先修订片合同。

回滚只移除未接入产品的 `medical_monitoring_ai_native_r5` 投影和新路由，不迁移/回写 canonical facts 或 R4 风险。浏览器验收后必须停止 8911。

`ACCEPT_R5_CONTRACT` 需要：v0.3 exact schema/enum/禁止分支；合同 canonical SHA；≥64 显式 registry 行与 204 配额 ledger 机械通过；D09/D10/ensemble→R5 字段映射可查询；编码/八域/unknown 处理无冲突；任务/性能预算冻结；写入边界闭合；fresh isolated reviewer 对同一 SHA 返回 `ACCEPT_R5_CONTRACT`。该状态只解锁 S1，不接受 R5 UI、真实项目/模型或生产。
