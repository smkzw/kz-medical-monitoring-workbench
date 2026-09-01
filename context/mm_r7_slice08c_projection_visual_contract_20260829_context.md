# R7 Slice-08C 中文连续性投影与视觉合同工作上下文

日期：2026-08-29  
状态：`CONTRACT_DRAFTING_ONLY`

## 目标

为已接受的 08A/08B 跨 Run 连续性事实建立最窄的中文受众投影与交互合同，并冻结 synthetic/ego(lite)
验收矩阵。当前只形成合同，不修改产品源码、不启动服务、不运行真实项目或模型。

## 唯一上游权威

- `reviews/medical_monitoring_r7_slice08_three_mode_carry_forward_contract_v0_1_20260829.md`
- `reviews/medical_monitoring_r7_slice08_three_mode_carry_forward_contract_v0_2_20260829.md`
- `context/medical_monitoring_r7_slice08a_continuity_acceptance_record_20260829.md`
- `reviews/medical_monitoring_r7_slice08b_authority_artifact_bridge_contract_v0_1_20260829.md`
- `reviews/medical_monitoring_r7_slice08b_authority_artifact_bridge_contract_v0_2_20260829.md`
- `context/medical_monitoring_r7_slice08b_authority_artifact_bridge_acceptance_record_20260829.md`
- 当前 R5/R7 前端投影、Patient Journey/访视轴、项目/中心 flow 看板源码与测试。

## 用户与界面约束

- 用户是懒惰、视觉敏感、数据敏感、风险敏感、中文原生、不熟悉计算机和 AI 的资深医学监察员。
- 默认首屏中高风险优先，必须同时回答“本轮变了什么、为什么变、影响谁、从哪里核对”。
- 不出现“正式事实、候选信号、只读、artifact、digest、token、CAS”等后端语言。
- Patient Journey 仍是一条横向访视/日期轴；AE/MH/CM/IP/PD/检验等事件与风险使用明确类别图标/标签，
  在轴下按时间定位，点击后显示事件、前后轮变化、风险依据和精确来源。
- 项目/中心默认页保留同源 Sankey/流向看板及表格；跨轮筛选与下钻不得改变项目/中心/受试者/日期语境。
- 08C 不改变 R2 生命周期，不把“本轮未出现”翻译成关闭，也不允许 UI 根据颜色或文案重新推导医学状态。

## 有边界的外部设计调研结论

1. IBM Data Visualization 建议“overview first, zoom/filter, details on demand”，同时重要信息不可只藏在交互后；
   标题应直接表达洞见，标签优先于冗长图例，颜色只用于有意义的强调。
   来源：https://www.ibm.com/design/language/data-visualization/design/basics/
2. Michelin dashboard 原则要求最重要视图位于顶部/左上，减少颜色与装饰，避免旋转标签，并用结构化布局、
   自解释标题和有意义图例降低阅读成本。
   来源：https://designsystem.michelin.com/data-visualization/design-guidelines/principles-of-a-dashboard
3. Apache ECharts 支持 SVG/Canvas、响应式和 ARIA/decal；Apache-2.0 可用于后续需要的复杂图表，但 08C
   应优先复用当前实现，不为视觉效果引入新依赖。若采用需保留 LICENSE/NOTICE。
   来源：https://echarts.apache.org/zh/index.html；https://apache.github.io/echarts-handbook/en/best-practices/aria/
4. IBM 可访问性要求数据图形与背景至少有可辨识的非文本对比，并支持放大后的 reflow；表格/图表可保留
   必要的局部横向滚动，但不得让整页双向迷失。
   来源：https://www.ibm.com/able/toolkit/design/visual/
5. 本项目继续使用康哲暖色、单品牌橙与克制语义色；动效用于状态/层级反馈，不用于装饰或延缓取证。

## 合同必须冻结的决策

1. 后端/公开 DTO 的最小连续性字段，及其与 08B publication/plan/item 身份的一一绑定。
2. 公开中文闭集、排序、默认筛选、严重度/变化双编码、缺证据/不可比较/需重新评估的 fail-closed 呈现。
3. 项目→中心→风险→Journey→来源的路由状态、返回路径、同一语境条与跨轮比较入口。
4. Journey 上事件类别图标、风险标记、时间定位、重叠/同日/区间事件与详情抽屉的可访问交互。
5. 1280/1440/1920 首屏密度、文字/间距/表格/图表/弹窗/动效/焦点/键盘/降动效验收矩阵。
6. synthetic fixture 至少覆盖三模式、全部公开变化、规则变化、覆盖不全、缺行不关闭、跨项目/篡改阻断。

## 明确非目标

- 不运行五个真实项目，不调用真实模型，不证明医学质量或泛化。
- 不进入 08D 三模式综合回归，不接受 R7/R8 总体。
- 不设计或测试安全功能，不修改医学写作子系统。
- 合同阶段不启动 8911/5174，不做浏览器验收；ego(lite) 只在实现后的视觉验收使用。
