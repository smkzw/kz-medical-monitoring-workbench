# R7 Slice-07B 项目/中心受试者阶段流向看板合同 v0.1

日期：2026-08-28  
状态：`DRAFT_FOR_GOVERNED_REVIEW`

## 1. 范围和接受目标

本切在 R5 项目/中心默认页增加受试者阶段流向看板及同源明细表。它回答“人现在在哪里、
怎样流转、关键分流在哪里、哪些人伴随中高风险、依据是什么”，不替代 Patient Journey、
医学风险判定、任务待办或真实项目验收。

接受必须同时满足：权威数据可重建、图表双向对账、项目/中心身份不串线、宽屏完整、中文
易读、键盘可达、跳转上下文可恢复。任何一项失败均不得以“图能显示”代替。

## 2. 权威数据合同

### 2.1 阶段目录 `R5FlowStageRecord`

每个阶段包含：`stage_ref`、中文 `stage_label`、`stage_order`、`stage_kind`、是否终末状态、
是否主链、来源定位。`stage_kind` 仅用于确定性计算，可取 `main`、`branch`、`unknown`、
`not_applicable`、`missing`。项目层必须接收上游根据方案与 listing 结构解析出的阶段目录，
不得在产品代码中固定某一研究的阶段。

### 2.2 受试者阶段记录 `R5SubjectFlowRecord`

每名受试者恰有一条当前范围内的记录：

- `subject_ref`、`site_ref`、`current_stage_ref`、可空的 `previous_stage_ref`；
- 可空的 `transition_date` 与 `date_state`：`exact`、`partial`、`missing`、`conflict`；
- 中文 `transition_reason`，以及 `completeness_state`：`complete`、`partial`、`unknown`；
- `source_locator_refs`；
- 可空的 `prior_stage_ref` 与 `change_kind`：`initial`、`new`、`advanced`、`returned`、
  `corrected`、`unchanged`、`not_comparable`。

产品层只验证和聚合这些记录，不根据事件标签、风险类别、访视名或模型输出补造阶段。

### 2.3 确定性归属规则

1. 当前节点按 `current_stage_ref` 计数，每名受试者一次；连线按
   `previous_stage_ref -> current_stage_ref` 计数。没有上一阶段者从专用“进入当前范围”起点
   流入，不伪造知情同意。
2. 更正后的有效记录覆盖旧值，但 `change_kind=corrected` 和来源仍保留；同一受试者出现两条
   未裁决当前记录时进入“状态待核实”，不得任选其一。
3. `unknown`（已有数据但无法判断）、`missing`（所需数据未提供）和 `not_applicable`
   （方案不适用）分开显示和计数。
4. 退回、重新筛选等非单向变化使用明确连线和中文原因，不强行塞入主链；图形布局不得因
   逆向连线破坏从左到右的总体阅读顺序。
5. 风险是受试者集合上的独立叠加。节点/连线的中高风险人数由当前 risk set 与其受试者集合
   求交得到，不能用流向颜色暗示风险等级。

## 3. 投影与对账合同

R5 overview 新增 `subject_flow`，至少包含：

- `availability`：`available` 或 `not_provided`；后者显示“本次数据未提供研究状态”，不能
  显示 0 人；
- `scope`：当前 `project_ref/run_ref/snapshot_ref/cutoff_ref/site_ref`；
- `stages`：阶段显示顺序、节点人数、中高风险人数和变化摘要；
- `links`：起止阶段、人数、中高风险人数、受试者引用；
- `subjects`：明细行所需全部中文展示字段和来源定位；
- `coverage`：已判断、状态待核实、数据未提供、不适用人数；
- `reconciliation`：总受试者数、节点去重人数、明细人数、连线可解释人数及
  `state=matched|blocked`。

不把内部 receipt/hash/ref 暴露到可见文案，但保留在响应身份与测试中。正常展示的阻断门槛：

1. `scope subject set = stage node union = detail row set`；
2. 每条 link 的 count 等于其 subject set 大小；
3. 节点中高风险人数不大于节点人数，且等于风险集合求交；
4. 指定中心时所有受试者、风险和来源均属于该中心；
5. 项目节点按中心分组后的受试者集合并集与项目集合一致且无重复。

任一条件失败时返回或呈现 `reconciliation.state=blocked`，用户文案为“阶段人数暂无法核对，
请检查本次数据范围”，图和表不得各自继续显示互相矛盾的数字。

## 4. API 和兼容策略

- 继续使用 `GET /medical-monitoring/r5/projects/{project_ref}/overview`，中心范围沿用
  `site_ref`；不新增写接口。
- `R5AuthorityPacket` 增加有类型的 `flow_stages` 和 `subject_flow_records`。历史 packet 可不
  提供，投影返回 `availability=not_provided`，禁止从旧字段推断。
- 同一响应中的风险、流向、表格和覆盖沿用完全相同的 project/run/snapshot/cutoff/site
  身份；不允许前端再次请求另一截止点拼接。
- 前端 adapter 严格校验字段、枚举、引用关系和对账状态；未知结构 fail closed。

## 5. 页面信息结构

默认顺序为：运行状态摘要 → 受试者阶段流向 → 当前中高风险 → 中心覆盖。流向看板使用全宽
区域，不挤进双栏卡片。

### 5.1 横向流向图

- 使用语义化 SVG 绘制，主阶段从左到右，桌面宽度 1280/1440/1920 默认完整显示；不引入
  重型图表依赖。
- 节点显示中文阶段、人数；连线宽度反映人数，但小样本仍有可点击最小宽度。分支以克制中性
  色区分，终末分流有文字标签，不只靠颜色。
- 节点或连线有中高风险时显示独立菱形/双箭头徽标及人数；低风险不逐条抢占首屏。
- 节点和连线均可聚焦、按 Enter/Space 选择，并有明确 `aria-label`；图下提供同等功能的
  中文筛选摘要，保证不依赖图形操作。

### 5.2 同源明细表

点击节点或连线后筛选同一 `subject_flow.subjects`；再次点击或“清除筛选”恢复当前范围全部
受试者。表格列为：受试者、中心、当前阶段、上一阶段、变化日期、关键原因、中高风险、
较上次变化、数据完整性。默认中高风险优先，其次日期待核实，再按阶段顺序和受试者号。

点击受试者进入同一 project/run/snapshot/cutoff 下的医学旅程。返回上下文至少保留
`site_ref`、所选节点/连线、风险筛选和表格位置；筛选状态使用前端明确允许的路由键或稳定
return context，不塞入未知 query 参数。

## 6. 中文、空态和异常态

- `not_provided`：本次数据未提供研究状态；说明需要补充何类数据，不显示 0。
- 无受试者：当前项目/中心在本次截止点暂无受试者。
- `unknown`：状态待核实；`missing`：研究状态数据未提供；`not_applicable`：本研究不适用。
- 页面禁止出现 provider、model、agent、ref、hash、receipt、projection、Sankey、正式事实、
  候选信号、只读、日志等用户无关词。页面名称使用“受试者阶段流向”。

## 7. 验收矩阵

### 7.1 确定性与回归

- 主链、筛选失败、已入组未治疗、永久停药、退出、失访、未知、缺失、不适用、小样本；
- 同一受试者重复输入、未裁决冲突、更正、回退、不可比较前次运行；
- 项目与各中心集合对账、节点/连线/表格/风险交叉对账；
- 旧 packet 明确 `not_provided`，不得假 0；
- R5 路由身份、adapter、页面、R7 产品路由和既有医学监查前端回归。

### 7.2 ego(lite) 视觉与交互

- 1280、1440、1920 宽屏主流程完整且页面无整体横向溢出；窄屏才允许看板内部受控滚动；
- 项目、中心、空态、阻断态各一次；节点/连线筛选、清除、键盘操作和返回恢复；
- 图表数字逐项与 API 投影和表格核对；中高风险显眼但不遮盖流向；中文无内部术语；
- 独立视觉角色审阅阶段顺序、医学语义、风险重点、易读性与美学一致性，Codex 以实际页面
  和数据作最终接受。

## 8. 非范围

真实项目、医学风险算法重算、Patient Journey 重构、报告导出、写操作、安全功能、R7 总体和
R8 均不在本切接受范围。

