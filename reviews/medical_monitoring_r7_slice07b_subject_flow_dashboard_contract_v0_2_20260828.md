# R7 Slice-07B 项目/中心受试者阶段流向看板合同 v0.2

日期：2026-08-28  
状态：`REVISED_FOR_GOVERNED_REVIEW`

本版取代 v0.1 作为实现依据。修订依据为用户需求、当前 R5 源码和独立视觉合同会商；不把
会商意见视为最终接受。

## 1. 产品对象与范围

本切实现真正可重建的“受试者阶段路径流向”，而不是把当前阶段人数伪装成桑基流。项目或
中心默认页用于回答：受试者经过哪些研究阶段、当前停留在哪里、关键分流发生在哪里、各流向
包含多少人、这些人中有多少当前伴随中高风险，以及如何落到逐例明细和医学旅程。

本切不从访视名、`phase_ref`、事件标签或风险类别推断阶段；不重构 Patient Journey，不运行
真实项目，不进行医学风险算法重算，不修改医学写作子系统。

## 2. 权威数据模型

### 2.1 阶段目录 `R5FlowStageRecord`

每项包含：

- `stage_ref`、中文 `stage_label`、`column_order`、同列 `row_order`；
- `stage_kind`：`main`、`branch_terminal`、`unknown`、`missing`、`not_applicable`；
- `is_entry`、`is_terminal`；
- `source_locator_refs`。

目录由上游方案/数据解构工作流按项目生成。产品只接收、验证和显示，代码不固定某一研究的
“知情同意—筛选—治疗”阶段集合。`unknown`、`missing`、`not_applicable` 必须分别保留。

### 2.2 受试者路径 `R5SubjectFlowPathRecord`

每名当前范围内受试者恰有一条规范路径记录：

- `subject_ref`、`site_ref`；`spine_ref` 从同一 packet 的 `R5SubjectRecord` 按
  `subject_ref` 唯一连接，不复制第二份；
- `steps`：一个或多个按顺序排列的 `R5SubjectFlowStep`；
- 每个 step 包含 `stage_ref`、可空的 `entered_date`、`basis_date`、`date_state`、中文
  `transition_reason`、`source_locator_refs`；
- `date_state` 只可为当前 R5 枚举 `exact|partial|conflicted|missing`；
- `path_state`：`complete|partial|conflicted`；
- 可空的 `prior_run_current_stage_ref` 和 `stage_change_kind`：`initial|new|advanced|returned|`
  `corrected|unchanged|not_comparable`。

最后一个 step 是当前阶段。当前有效路径由上游裁决：更正替换旧路径但保留
`stage_change_kind=corrected`；未裁决的多条当前路径必须形成唯一的“状态待核实”路径，不能
任选一条。当前展示路径中 stage 不得重复，主链 `column_order` 不得倒退；重新筛选或退回由
当前规范路径及“阶段较上次”说明表达，不绘制破坏横向布局的循环边。

### 2.3 路径缺口

- 已知当前状态但缺少此前阶段时，路径从系统保留的 `missing` 阶段“既往阶段数据未提供”
  开始；不伪造知情同意或筛选经历。
- 现有数据相互冲突时进入 `unknown` 阶段“状态待核实”。
- 方案明确不适用时进入 `not_applicable` 阶段“本研究不适用”。
- 一个新 flow packet 若有受试者但没有可投影路径，属于阻断，不显示 0 人。

## 3. 桑基计算与守恒

`subject_flow.subjects` 是唯一成员事实；节点、连线、明细表和风险徽标均由它确定性聚合，
不得分别维护第二份受试者集合。

- 节点 `reached_count`：规范路径中包含该 stage 的唯一受试者数。
- 节点 `current_count`：最后一步为该 stage 的唯一受试者数。
- 连线 `count`：规范路径中相邻两个 step 等于该 from/to 的唯一受试者数。
- 节点保留量：`current_count`；它解释已流入但尚未流出的受试者。
- 对非入口节点，流入人数等于到达人数；对非终末节点，流出人数加当前停留人数等于到达人数。
- 每名受试者从唯一入口进入，并以当前阶段作为本次截止点路径终点；因此项目总人数、入口流量
  和所有当前停留人数之和相等。

若阶段目录含汇合分支，仍要求同一受试者对同一节点只有一个流入和一个流出；不满足者
`reconciliation.state=blocked`。图上节点同时标示“到达 n / 当前 n”，避免把累计到达误读为
当前人数。页面中文说明：“连线表示受试者实际阶段路径；节点同时显示累计到达人数和当前
停留人数，数据截至本次监查截止点。”

## 4. 风险与前次运行变化

中高风险集合固定为 `critical|high|medium`；低风险只聚合，不进入流向徽标。

- 节点风险人数 = 当前停留于该节点、且当前有至少一项中高风险的唯一受试者数。
- 连线风险人数 = 经过该连线、且当前有至少一项中高风险的唯一受试者数；可见文案明确为
  “该流向受试者中当前伴随中高风险 n 人”，不暗示风险发生在该转移时。
- 风险徽标沿用 R5 已冻结的双箭头形状和文字/人数，不新增菱形，不用流向颜色代表风险。
- “阶段较上次”来自 `stage_change_kind`；“中高风险较上次”来自现有 risk `change_kind`，
  两者在表格分列，不混写。图上风险变化仅显示新增、升高、持续等风险变化。

## 5. 投影与四向对账

R5 overview 增加嵌套 `projection.subject_flow`，不复用顶层 `subjects` 或 `coverage`：

- `availability=available|not_provided`；
- `visual_kind=path_throughput_sankey`；
- `scope`：project/run/snapshot/cutoff/site；
- `stages`：目录、`reached_count`、`current_count`、当前中高风险人数；
- `links`：稳定 `link_ref`、from/to、count、当前中高风险人数；
- `subjects`：明细行和筛选所需字段；
- `coverage`：路径完整、部分、冲突、数据未提供、不适用人数；
- `reconciliation`：总人数、入口人数、当前停留人数、明细人数、节点/连线守恒结果与
  `state=matched|blocked`。

必须全部通过：

1. 范围受试者集合 = 路径记录集合 = 明细行集合；
2. 每名受试者只属于一个当前节点；所有当前节点人数之和 = 范围总人数；
3. 每个节点、连线人数等于从路径重新计算的唯一受试者数；逐节点守恒成立；
4. 节点/连线中高风险人数等于其受试者集合与当前中高风险集合求交；
5. 中心范围内所有 subject/site/risk/source 均属于该中心；项目集合等于各中心不重叠并集；
6. 选择节点或连线后，表格行集合与选择集合完全相等，筛选风险人数也完全相等；
7. 全局覆盖/对账条明确标注“当前项目/中心范围，不随图上筛选变化”。

失败时只显示“阶段人数暂无法核对，请检查本次数据范围”和可理解的缺口说明；不并行展示
互相矛盾的图表。

## 6. API、版本与旧数据

- 继续使用既有 overview GET；中心沿用 `site_ref`，不新增写接口。
- 新 flow packet 使用新的 authority contract schema/version，其 hash payload 包含
  `flow_stages` 与 `subject_flow_paths`。旧 v0.3.1 packet 按旧字段验证原 hash，不将空 flow
  字段补入旧 hash。
- 旧 packet 缺少两个 flow 字段，或两个字段同时为空时，返回 `not_provided`，页面显示
  “本次数据未提供研究状态”，绝不显示 0 人。
- 新 packet 有 stages、有范围受试者但路径为空/缺员/引用不一致时必须 `blocked`。
- 前端只对 `subject_flow` 子树严格校验枚举、引用、身份和对账；不得因响应中无关扩展字段
  破坏现有 R5/R7 共存。
- Slice-07B 的生产者仅为 synthetic typed records；协议 NLP 和真实 listing 阶段抽取留在
  后续上游纵切，不得用 `visits.phase_ref` 临时补数。

## 7. 页面信息架构与宽屏布局

默认顺序：运行状态摘要 → 四项风险/覆盖摘要 → 受试者阶段流向 → 当前中高风险 → 中心覆盖。
流向图为全宽摘要区；明细表在图下可展开，默认显示紧凑前若干行，使 1280×800 首屏仍能
看见完整主流向和中高风险区标题，不要求首屏同时展示完整表格。

### 7.1 横向流向图

- 原生语义化 SVG，无重型图表依赖；主链从左到右，终末分支置于第二行。
- 1280 内容宽度按约 1220px 设计：默认最多显示 6 个可读阶段列；更多阶段按目录定义的
  `display_group_ref` 合并为“其他阶段（n）”，可原位展开。合并只影响视觉，不改变明细和
  对账。
- SVG 摘要区高度不超过约 220px；节点中文最小 13px，人数最小 16px，使用等宽数字。
- 连线最小可见宽度 8px，另有至少 24px 的透明点击区域；颜色克制，终末分支有文字/线型，
  信息不只靠颜色。
- 1280、1440、1920 均不得出现页面或看板横向滚动；更窄页面才允许看板内部受控滚动。
- 用户界面不出现 “Sankey”、provider、model、agent、ref、hash、receipt、projection、
  availability、reconciliation、not_provided、日志、正式事实、候选信号、只读等词。

### 7.2 筛选和表格

节点/连线点击切换筛选；再次点击或“清除筛选”恢复。图旁提供原生中文 chip/select 作为
主要键盘等价入口。表格列：受试者、中心、当前阶段、上一阶段、状态变化日期及依据日期、
关键原因、中高风险摘要、阶段较上次、中高风险较上次、数据完整性。

默认排序：中高风险优先 → 日期待核实 → 阶段列序 → 受试者号。中高风险单元显示最高等级和
主要类型摘要，不显示布尔值。原始 locator 不直接展示；用户经医学旅程继续核查来源。

### 7.3 键盘

- 图/筛选区内方向键在节点与连线间移动，Enter/Space 选择，Escape 清除；焦点样式清晰。
- 现有文档级风险列表快捷键在焦点位于 flow 图、筛选、表格或表单控件时不得触发。
- `aria-label` 示例：“筛选失败，到达 12 人，当前 12 人，其中中高风险 3 人”。

## 8. 中心范围与比较

项目页默认显示全部中心并集；中心选择沿用已有 `site_ref` overview 路由。项目页的中心比较
继续由下方中心表承担，增加各中心关键阶段/分流人数，不在同一 1280 图中叠加多套流向。
项目 = 各中心无重复并集是后端阻断性不变量，不只是视觉声明。

## 9. 医学旅程跳转与返回

- flow 明细按 `subject_ref` 连接既有 `R5SubjectRecord.spine_ref`；缺失或不唯一则阻断该行
  跳转。
- 进入 Journey 沿用既有截止点约束和受试者时间轴默认窗口规则，不创建 flow 专属窗口，
  不传空窗口。
- 路由闭集增加 `flow_stage_ref`、`flow_link_ref`、可空 `flow_risk_band`；它们是显示上下文，
  不进入权威 identity 或 authority hash。
- Journey 导航保留这些键、`return_context_key` 和 `site_ref`；返回 overview 后在同一
  subject_flow 投影重放筛选。表格滚动位置只在当前页面会话内恢复，不承诺刷新后保留。

## 10. 验收矩阵

### 10.1 确定性测试

- 44 人示例主链与分支守恒；主链进行中受试者形成节点保留量；
- 筛选失败、已入组未治疗、治疗中、永久停药、仍在研究、完成、退出、失访；
- 缺失前史、冲突、不适用、空范围、小样本、重复 stage、倒序/循环、路径缺员；
- 新旧 schema/hash、旧 packet `not_provided` 且页面无“0 人”；
- 项目/中心集合、节点/连线/表格/风险四向对账；筛选后对账；
- 阶段更正/回退与风险新增/升高分列；`conflicted` 中文往返；
- 修改 visits.phase_ref 不影响 subject_flow；
- flow 路由键闭集、Journey 完整 identity、同截止点返回筛选；
- 键盘事件隔离和现有 R5/R7 前后端回归。

### 10.2 ego(lite) 验收

- 项目、中心、旧数据未提供、对账阻断四种页面；
- 1280/1440/1920 完整主流向、无页面/看板横向溢出，首屏可见风险区标题；
- 节点/连线/chip 筛选、清除、表格展开、Journey 往返、键盘与焦点；
- 逐项把可见图、表、风险数与同一 API 投影核对；
- 中文医学语义、风险重点、视觉层级与既有 Patient Journey 风格一致；
- 独立视觉角色给出 accept/revise/reject，Codex 复核实际页面与数据后才可接受。

## 11. 非范围与完成边界

不运行五个真实项目；不声明真实医学正确性；不实现真实方案/listing 阶段抽取；不重构
Patient Journey；不做报告导出、写操作、安全功能、R7 总体或 R8 验收。只有 synthetic
权威路径、守恒对账、项目/中心页面、筛选/跳转、回归和 ego(lite) 全部通过，才可形成
Slice-07B 范围受限接受。

