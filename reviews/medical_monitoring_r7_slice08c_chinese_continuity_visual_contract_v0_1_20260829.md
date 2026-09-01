# R7 Slice-08C 中文连续性投影与视觉交互合同 v0.1

日期：2026-08-29  
状态：`DRAFT_FOR_INDEPENDENT_REVIEW`

## 1. 目标与范围

Slice-08C 只把 08A/08B 已验证的跨 Run 连续性事实转换为资深医学监察员可直接阅读的中文比较面，
并接入既有项目→中心→风险→Patient Journey→来源链路。它不新增医学事实、不改变 R2 风险生命周期，
不根据 UI 颜色、文案或缺行重新推导风险结论。

实现范围限定为：

1. 一个只读的公开连续性投影端点及前端严格校验；
2. 项目/中心结果页的“本轮变化”摘要与中高风险优先列表；
3. 风险/事件右侧详情抽屉，保持同一项目、中心、受试者、时间窗与来源语境；
4. Patient Journey 横向访视轴上的变化标记、事件类别图标和风险来源入口；
5. synthetic fixture、确定性测试和 ego(lite) 1280/1440/1920 视觉与交互验收。

## 2. 唯一权威与消费条件

1. 只消费 `status=published` 的 `CarryForwardPlan`，且它必须与当前 `available` ResultPublication 的
   project、mode、target run/snapshot/cutoff、R5 authority digest、R6 publication/receipt/output-set digest
   及成员闭包一致。
2. 只消费该 plan 中已通过 08A/08B dataclass、R5/R6 validator 与 R1 artifact member/byte verification 的
   `CarryForwardItem`；前端不接收 caller 提供的“已验证”布尔值作为事实。
3. R2 `RiskLifecycleState/RiskTransitionType` 仍是唯一生命周期；08C 只展示冻结的 `RiskChangeKind`。
4. 任一计划、成员、摘要、项目、模式、快照、截止点或公开上下文身份不一致时，连续性投影整体 fail closed；
   既有结果看板仍可独立显示，但不得用旧 run、fixture 或前端推测补齐比较内容。

## 3. 公开端点与响应闭集

新增只读 GET：

`/projects/{project_id}/medical-monitoring/r7/results/{result_context_token}/continuity`

不接受 request body；允许 query 仅为既有 `site_ref`。端点复用现有 `_load_public_result_context`，因此必须先通过
result context、project、publication available、R5 adapter 与 site scope 门。它不扩展既有 result envelope 的
严格字段集，避免连续性局部不可用时破坏结果主体。

响应顶层字段必须恰好为：

```text
result_context_token
identity
comparison
response_digest
```

`identity` 必须恰好为：

```text
project_ref, public_run_token, snapshot_token, data_cutoff_text,
mode_text, site_scope_text[, site_ref]
```

`comparison` 必须恰好为：

```text
available, basis_text, comparison_text, source_run_text,
change_counts, rows, shown_count, total_count, truncated
```

- `available` 在成功响应中恒为 `true`；不可用走稳定错误 `continuity_unavailable`，不返回半成品。
- `basis_text` 只允许“全量分析”或“增量分析”。
- `comparison_text` 只允许“已与上次监查结果比较”或“本轮为首次全面分析，无比较基线”。
- `source_run_text` 是面向用户的上次监查批次名称/日期，不得是内部 `run_id`、digest 或 artifact id；无法形成
  合法中文名称时为空，并使用首次分析文案，不暴露 public token 作为界面文字。
- `response_digest` 由服务端对 `identity+comparison` 计算；前端必须验证但不得显示。

## 4. 条目公开字段

每个 `rows[]` 必须恰好包含：

```text
row_ref, object_type, object_type_text, ordinal,
change_kind, change_text, disposition, disposition_text,
data_change_kind, data_change_text,
severity_before_text, severity_after_text,
title, reason_text, attention_text,
site_ref, site_label, subject_ref, subject_label,
date_label, window_start, window_end,
risk_ref, risk_instance_ref, risk_anchor_ref,
event_ref, source_locator_ref, source_count
```

规则：

1. `row_ref` 是本响应内稳定公开行引用，不得等于或包含内部 object/artifact/digest/run identity。
2. 公开对象闭集：`risk / query_draft / monitoring_output`，中文分别为“风险”“Query 草稿”“监查结果项”。
   `evidence_binding` 不独立成行，只能形成 `source_locator_ref/source_count`。
3. `reason_text` 只能来自已验证、面向用户的 R2/08A reason；服务端必须通过公开文本门，禁止直接透传
   `evidence_summary`、内部枚举、路径、摘要、token、异常或日志文本。
4. `title/site_label/subject_label/date_label` 必须来自当前 R5 audience projection；08C 不从 internal ref 造中文标题。
5. 无精确来源时 `source_locator_ref=""`、`source_count=0`，来源按钮禁用并显示“原始记录位置待确认”；禁止空跳转。

## 5. 中文语义闭集

### 5.1 风险变化（唯一公开闭集）

| 值 | 中文 |
|---|---|
| `new` | 新增 |
| `upgraded` | 升级 |
| `continued` | 持续 |
| `downgraded` | 降级 |
| `closed` | 关闭 |
| `reopened` | 重开 |
| `needs_rejudgment` | 需重新判断 |

旧 flow 别名“升高/降低/解除/重新出现/暂不可评估”只在输入 adapter 中一次性归一化，不再出现在新界面。
“关闭”只能来自 R2 合法关闭及明确证据，绝不能由本轮缺行、覆盖不全或基线不合格生成。

### 5.2 处置

| 值 | 中文 |
|---|---|
| `reuse_unchanged` | 沿用不变 |
| `re_evaluate_changed_data` | 数据变化，已重新分析 |
| `re_evaluate_rule_change` | 规则变化，已重新分析 |
| `re_evaluate_prior_uncertain` | 上轮依据不足，本轮重新分析 |
| `close_with_evidence` | 已有证据支持关闭 |
| `blocked_incompatible` | 前后版本不可直接比较 |

### 5.3 数据变化

`unchanged/added/revised/deleted/cannot_compare/missing` 分别显示“无变化/新增数据/数据修订/数据删除/
无法直接比较/本轮未见对应记录”。最后一项必须同时显示：“未见记录不代表风险已解除”。

### 5.4 风险等级

仅显示当前 R5 audience projection 已提供的“高/中/低”；前后任一等级缺失时不拼接箭头、不自行赋级，显示
“等级变化待确认”。

## 6. 排序、筛选与首屏

服务端给出唯一稳定顺序，前端只能过滤，不得重排：

1. 当前高风险且 `upgraded/new/reopened/needs_rejudgment`；
2. 当前中风险且上述变化；
3. 其余高/中风险；
4. 低风险；
5. Query 草稿；
6. 监查结果项；
7. 同组按 `ordinal` 升序。

默认首屏：

- 显示“新增、升级、重开、需重新判断”四个变化计数与中高风险总数；
- 列表默认只勾选“中高风险”，但用户可查看全部；
- 不限制为 3–5 条；1280 首屏至少看见摘要与前 6 行，1440/1920 至少 8 行；
- 服务端最多返回 200 行，超出按权威顺序截断并明确“共 N 条，当前显示前 200 条”；不做无限滚动。

筛选只允许：风险等级、七类变化、对象类别、中心、受试者与“仅看需重新判断”。筛选为页面本地状态，
不扩展 R5 公开 URL identity 闭集；项目/中心/受试者下钻仍由既有 canonical route state 管理。

## 7. 同一身份下钻与返回

1. 项目页 → 中心页：保留 project/result context，增加既有 `site_ref`。
2. 中心/风险行 → Patient Journey：必须携带既有 `subject_ref + spine_ref + window_start + window_end`；缺任一
   必要身份则按钮禁用并显示“受试者时间范围待确认”。
3. 风险/事件 → 来源：必须携带成对的 `risk_ref+risk_instance_ref`（适用时）、`source_locator_ref` 及当前
   project/site/subject/window；非法半身份 fail closed 为“当前定位无法确认，请返回上一级”。
4. 来源页返回 Patient Journey，恢复相同轴窗、访视/事件/风险选择；不得返回到另一个受试者或默认项目页。
5. IdentityStrip 是唯一的身份面包屑，使用“项目概览 / 中心概览 / 受试者医学旅程 / 原始记录”中文；
   不显示内部 token、run、snapshot、digest 或 schema 名。

## 8. Patient Journey 与详情抽屉

1. 保持一条横向访视/实际日期轴，默认宽屏可理解完整先后关系；calendar/study_day 只切换刻度，不改变事实。
2. 事件类别沿用现有 Lucide 图标闭集并以图标+短中文双编码：AE、MH、CM、试验用药、检验检查、诊疗操作、
   疗效/症状、方案执行。未知类别使用问号图标与“类别待确认”，不归入相邻类别。
3. 事件几何为 point/interval/pending；日期缺失/冲突不得吸附到轴，必须在轴下“日期待确认”区域列示。
4. 变化使用图标+中文+语义色三通道；风险等级始终另有“高/中/低”文字，不以颜色代替。
5. 点击风险或事件打开路由驱动右侧抽屉，复用既有 `risk_instance_ref/event_ref`，不新增 URL 键：
   - 1280 为不超过 480px 的 overlay；1440/1920 在剩余宽度足够时为并排；
   - 标题、事件类别、风险等级、变化、日期、前后依据、关联记录、Query 草稿和来源入口按固定顺序；
   - Query 草稿继续显示“依据 + 发现 + 行动项”，不提供处理待办或人工复核状态；
   - Esc 关闭并把焦点还给触发元素；打开时焦点进入抽屉标题，Tab 不越出抽屉，关闭后路由选择被清除。
6. 轴内不叠加两条完整历史 timeline；跨轮差异通过节点变化标记、摘要和抽屉前后依据展示，避免时间轴与版本轴混淆。

## 9. 视觉系统

1. 继承当前产品布局和康哲品牌，不重做壳层；正文使用 PingFang SC/Microsoft YaHei/Noto Sans SC 中文优先栈，
   数字与日期启用 tabular nums。实现时移除医学监查新增区域对 Inter 的优先依赖，但不在本 Slice 全站改字体。
2. 品牌橙只用于主要操作与选中态；风险红、警示琥珀、信息蓝、成功绿只承载对应语义。图表以灰阶为主体，
   关键洞见用一处语义强调；不得彩虹配色、3D 数据图形、装饰性渐变或毛玻璃。
3. 暖灰页面、白色卡片、轻边框与多层克制阴影；卡片/按钮允许 160–220ms 微动效，但数据图形不得为“酷炫”
   牺牲读数。`prefers-reduced-motion` 下所有动效瞬时完成。
4. 字号：页面标题 25–34px、二级标题 18–20px、正文 14px、辅助 12px；正文行高不少于 1.5。表格默认行高
   40px，紧凑模式 36px，表头 12px/700；所有中文避免单字孤行和不美观跨行。
5. 4px 间距基数；页面/卡片/抽屉/表格使用一致的 8/12/16/24/32 间距。不得以堆叠卡片代替时间关系。
6. 图表标题直接表达结论；优先直接标签，只有空间不足才使用图例。Sankey/流向带宽仅表示人数，必须同时显示
   数字与同源表格；Journey 时间轴必须提供可读的事件列表/抽屉作为非图形取证路径。

## 10. 可访问交互

1. 正文对比度目标 ≥4.5:1，图标/边界/大字 ≥3:1；必须用实际计算验证，不接受目测。
2. 可交互目标最小 24×24 CSS px；风险行、流向节点/连线、时间轴事件可 Tab 到达并有 2px 可见焦点。
3. 风险列表支持 ↑/↓，时间轴事件支持 ←/→，Enter/Space 打开详情；键盘顺序与视觉顺序一致。
4. 抽屉使用 dialog 语义、可访问标题、焦点锁定与返回；状态变化通过文字/aria-live 简短通知，不连续播报。
5. 1280/1440/1920 不允许整页横向溢出。复杂时间轴可在自身区域横向移动，但必须保留轴标题、当前窗与返回入口。

## 11. ego(lite) 验收矩阵

实现后必须用同一隔离任务空间、synthetic 数据和真实界面逐步捕获并检查当前运行截图；旧截图只能作历史参考，
不得替代本轮证据。

三视口均检查：

1. 项目结果首屏：摘要→中高风险变化→Sankey/表格层级，关键计数同源；
2. 中心下钻：中心身份、筛选与返回不漂移；
3. 风险筛选：服务端顺序不变，默认中高风险，七类变化中文闭集；
4. Patient Journey：单条横向轴、访视顺序、八类事件、风险标记、pending 区；
5. 抽屉：内容顺序、来源按钮、Esc、焦点进入/归还、overlay/push 行为；
6. 来源下钻与返回：项目/中心/受试者/时间窗保持一致；
7. 首次全面分析、可比增量、不可比/覆盖不全、本轮缺行、关闭有证据、规则变化、篡改阻断七个状态；
8. 1280/1440/1920 的字体、断行、间距、卡片边缘、表格列、图标、对比度、页面溢出与信息密度；
9. reduced-motion、键盘、焦点、可访问名称；
10. DOM/屏幕不得出现内部字段、工程标签、日志文案、英文裸状态或医学写作内容。

每个步骤保存当前截图、DOM/snapshot、视口/溢出/对比度结构化结果和网络请求证据；截图必须先打开检查再接受。

## 12. 确定性与失败矩阵

至少覆盖：

- 三模式：日常、锁库前、锁库后—CFDI 前；全量/增量及锁库修订增量；
- 七类风险变化、六类处置、六类数据变化与三种对象类型；
- 高危缺行、覆盖不全、基线不合格、身份/谱系变化不自动关闭；
- 规则 A 变化只影响适用对象，规则 B 无关对象继续沿用；
- 来源丢失/篡改/跨项目/非 publication 成员、摘要/CAS/迟到回调全部阻断；
- 响应字段精确闭集、内部词扫描、digest 校验、稳定排序、截断、SQLite 重开与相同请求重放；
- 前端纯函数、组件渲染、路由、Vite build、相邻 R5/R7/产品路由回归；
- 8911/5174 最终停止，医学写作保护面不变。

## 13. 实施顺序

1. 08C-1：公开 continuity endpoint、严格 DTO/摘要、中文闭集、排序/失败关闭与 Python/Node 测试；不改布局。
2. 08C-2：项目/中心摘要、风险变化列表、筛选与同一身份路由；不改 Journey 几何。
3. 08C-3：Journey 变化标记、事件图标、右侧抽屉、键盘/焦点/reduced-motion。
4. 08C-4：视觉专项收口、synthetic fixture、ego(lite) 三视口全流程与独立视觉会商。
5. 全部通过后才可进入 08D 三模式综合回归。

## 14. 非目标与停止条件

- 不运行五个真实项目，不调用真实模型，不证明医学正确性、泛化或真实端到端。
- 不引入 ECharts/Carbon 等新运行依赖；当前 SVG/React/Lucide 足以完成 08C。后续若确有复杂图表需求，必须
  另做 Apache-2.0/NOTICE 与 bundle/performance 决策。
- 不统一全站 token、不重构医学写作、不设计或测试安全功能、不做移动端/暗色主题。
- 合同冻结和 08C-1 后端阶段保持 8911/5174 停止；只有 08C-4 的隔离 synthetic 浏览器验收可启动专用夹具端口，
  完成即停止，不挂载真实产品服务或真实数据。

本 v0.1 需经独立会商挑战并形成明确 ACCEPT/REVISE 后方可冻结；任何修订以新版本附录记录，不静默改写。
