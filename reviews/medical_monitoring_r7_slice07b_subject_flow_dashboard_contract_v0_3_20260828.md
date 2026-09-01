# R7 Slice-07B 受试者阶段流向看板合同 v0.3（冻结修订）

日期：2026-08-28  
状态：`FROZEN_FOR_IMPLEMENTATION_REVIEW`

本文件与 v0.2 合并构成当前实现合同；若两者冲突，以本文件为准。v0.1 仅保留为审阅历史。

## 1. 已冻结的产品路线

- 采用 `path_throughput_sankey`：显示上游提供的规范阶段路径，不把当前状态人数伪装成流量。
- 当前规范路径按方案列序且没有回头边；退回、重新筛选或更正只在“阶段较上次”说明，已被
  更正而不在当前规范路径中的后续阶段不计入本次 `reached_count`。
- 页面说明固定为：“连线表示截至本次截止点的规范阶段路径；节点同时显示累计到达人数和
  当前停留人数。退回或重新筛选情况见阶段较上次。”
- 07B synthetic 阶段目录最多 6 个 `column_order`；本切删除 v0.2 中未定义的
  `display_group_ref` 与合并节点要求。真实项目超过 6 列时进入后续动态布局纵切，不在本切
  偷做不可对账的“其他阶段”。

## 2. 节点、连线与筛选集合

节点有两个明确集合：`current_subjects`（当前停留）和 `reached_subjects`（累计到达）。

- 点击节点或“当前”入口默认选择 `current`；节点双箭头风险人数、表格行和筛选后风险摘要
  均为 `current_subjects ∩ current_mid_high_risk_subjects`。
- 点击“到达”人数选择 `reached`；表格和风险摘要改为 `reached_subjects` 及其风险交集。
- 点击连线选择规范路径包含该相邻 stage 对的受试者；连线风险人数与该集合完全一致。
- 路由闭集新增 `flow_stage_ref`、`flow_node_metric=current|reached`、`flow_link_ref`、
  `flow_risk_band=""|mid_high`。默认 `flow_node_metric=current`。
- gate 6 分别对 current/reached/link 三类选择做集合、表格行和风险人数精确对账；全局覆盖条
  明确“不随图上筛选变化”。

## 3. 三种非正常展示

| 数据状态 | 投影合同 | 用户界面 |
|---|---|---|
| 未提供 | `availability=not_provided`；仅含中文 reason，`reconciliation` 可省略或为 `not_applicable` | “本次数据未提供研究状态”；无节点、无表、DOM 不出现“0 人” |
| 对账失败 | `availability=available`、`reconciliation.state=blocked`，含中文 gap；不得带互相矛盾的完整图表 | “阶段人数暂无法核对，请检查本次数据范围” |
| 真实空范围 | `availability=available`、`reconciliation.state=matched`、N=0 | “当前项目/中心在本次截止点暂无受试者”；无零值桑基图 |

新 packet 中 paths 无 stages、stages 无 paths 且范围受试者非空、缺员或引用不一致均为
`blocked`，不是 `not_provided`。旧 schema 缺少 flow 字段或两个字段同时为空才是
`not_provided`。

## 4. 路径连续性

规范路径不得跳过已声明的主链中间列。合法连线仅为：

- `main` 第 i 列 → `main` 第 i+1 列；
- `main` 第 i 列 → `branch_terminal` 第 i 或 i+1 列；
- 保留的 `missing` 入口“既往阶段数据未提供” → 第一个已知 main；
- 单步 `unknown|missing|not_applicable` 可同时为 entry 和 terminal。

已知知情同意和治疗、但筛选阶段缺失等中间断裂，必须进入唯一的 `unknown`“状态待核实”
路径并标记 `path_state=conflicted`，不得绘制知情同意直达治疗。覆盖桶必须把范围 N 分割为
互斥集合；带 missing 前缀且随后有已知阶段的记录计为“部分”，不得同时计入“数据未提供”。

入口节点不画入边，并满足 `reached = current + outbound`；终末节点可无出边。主链到同列或
下一列的终末分支合法。

## 5. Journey 跳转窗口

flow path 不复制 `spine_ref` 或窗口。overview 投影时：

1. 按 subject_ref 唯一连接同 packet 的 `R5SubjectRecord.spine_ref`；
2. 从该受试者同 packet 的 visits/events 计算最早和最晚可用日期，并受当前 cutoff 约束；
3. 得到 `jump_window_start/end` 后才启用“进入医学旅程”；
4. 无任何可用日期时该行仍显示，但按钮禁用并标注“时间窗待确认”，不得发送空
   `window_start/window_end`，也不阻断全图。

这属于 overview 到既有 Journey 的身份接线，不改变 Journey 时间轴或事件语义。

## 6. 视觉与表格补充

- 1280 宽度下 flow 标题和 SVG 总高度不超过 248px；表格默认折叠为一行摘要；无论 R7
  进度是空闲或运行中，中高风险区标题的上边缘必须位于 800px 视口内。
- 节点只放两行阶段名、“到达 n / 当前 n”和当前中高风险 n；风险新增/升高/持续作为一条
  范围级摘要置于 SVG 下，不塞进每个节点。
- 中心表最多增加两个关键分流计数列，不创建第二套桑基图。
- 表格“上一阶段”指规范路径倒数第二步；不存在则显示“—”，不得使用上一运行阶段。
- `flow_risk_band` 保留，用于从 Journey 返回时恢复风险筛选。
- 长阶段名最多两行，SVG `title` 保留完整中文；节点/连线仍有 24px 以上命中区。

## 7. 新增阻断性测试

- 节点默认 current、到达 reached、连线三类筛选分别与表格/风险数对账；
- legacy 未提供、available+blocked、available+matched+N=0 三态互不混淆；
- 中间缺段进入“状态待核实”，无跨列假连线；同列终末分支合法；
- 无日期行禁用 Journey；有日期行生成同 cutoff 的非空窗口并完成往返；
- synthetic 目录不超过 6 列，1280 不依赖合并节点；
- 12 人守恒示例：12 进入、筛选失败 2、治疗中 5、完成 3、永久停药 2；入口 12，
  当前停留合计 12，各节点 `reached=current+outbound`，图、表与风险集合一致。

## 8. 完成边界

除上述修订外继续执行 v0.2。合同冻结不等于实现完成；只有后端 typed authority、投影、前端
adapter、路由、SVG、表格、确定性测试、构建、ego(lite) 和独立视觉验收全部通过，才可形成
Slice-07B synthetic 范围受限接受。

## 9. 筛选身份与跳转勘误

本节与 §2、§5、§7 冲突时以本节为准。

1. 主选择互斥，三者只可居一：无筛选；或 `flow_stage_ref` + `flow_node_metric`
   （缺省 `current`）；或 `flow_link_ref`（此时忽略 metric）。Journey 返回若同时带 stage 与
   link，只保留最近一次选择，不得求交成空表。
2. `flow_risk_band=""|mid_high` 只与主选择求交，不是第三套主选择。
3. 节点双箭头徽标恒为该节点 `current ∩ 中高风险`，属于节点自身属性。筛选摘要和表格随
   主选择变化；切到“到达”后不得用节点徽标数字与到达表格对账。
4. §7“有日期行”是指同 packet 的 visits/events 经 cutoff 裁剪后得到非空
   `jump_window_start/end`。不得用路径 `entered_date` 或 `basis_date` 顶替；仅有路径日期的
   行保持禁用“时间窗待确认”，不得发送空 window 参数。
