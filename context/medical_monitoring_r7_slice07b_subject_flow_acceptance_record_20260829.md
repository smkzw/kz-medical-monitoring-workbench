# R7 Slice-07B 受试者阶段流向看板接受记录

日期：2026-08-29  
状态：`ACCEPT_R7_SLICE_07B_SYNTHETIC_LIMITED`

## 1. 本切目标与结果

项目/中心默认页已加入同源受试者阶段流向看板：按知情同意、筛选、入组/治疗、随访/研究
结束从左向右展示主流程和关键分支；节点、连线、中高风险、下方受试者明细和 Patient Journey
入口均来自同一 `subject_flow` 投影。中心范围复用同一合同，不用风险或访视名称猜测研究状态。

流向图是首屏主对象，不再是平铺卡片。项目态与中心态在 1280×800 和 1920×800 宽屏无页面
横向溢出；零人数目录节点仍可见并明确说明“本截止点无人到达”。点击节点、连线或中高风险
筛选会更新同一份明细，再次点击或清除筛选恢复当前范围；受试者可一跳进入同一运行、截止点
和时间窗的 Patient Journey。

## 2. 权威合同与改动面

- 合同：`reviews/medical_monitoring_r7_slice07b_subject_flow_dashboard_contract_v0_2_20260828.md`
  加 `v0_3` §9 勘误，冲突时 §9 优先。
- 后端：`services/api/app/medical_monitoring_r5_product_adapter.py`。
- 前端：R5 adapter、route-state、`MedicalMonitoringR5Page.jsx`、
  `medicalMonitoringR5.css` 及对应测试。
- 合成验收夹具：`artifacts/mm_r7_slice07a_progress_ui_ego_fixture_20260828/synthetic_fixture.py`。
- 未修改或运行医学写作子系统、五个真实项目或 8911 产品服务。

## 3. 已证明的合同

1. 旧 packet 兼容；新 packet 提供 typed stage/path 与 `matched`、`blocked`、`not_provided`
   三态，项目/run/snapshot/cutoff/site 身份严格绑定。
2. 节点、连线、明细和风险计数守恒；对账不匹配时不渲染成正常图。
3. `flow_stage_ref` 与 `flow_link_ref` 互斥；节点支持“当前停留/累计到达”，并可与中高风险
   过滤求交；Journey 往返保留范围与选择上下文。
4. `row_order` 决定同列纵向位置；完成研究与永久停药不重叠；中心空主阶段不再覆盖空终点。
5. 中文两行标签、人数和风险提示在 68px 节点中使用独立基线；页面不显示模型、日志、ref、
   hash 或研发状态词。

## 4. 决定性证据

- Python focused/fixture：`69 passed in 2.10s`。
- 全部 49 个医学监查 Node 测试文件通过；其中 Subject Flow render `99 checks passed`。
- Vite：`1968 modules transformed`，构建成功；仅有既存大 bundle 提示。
- ego(lite)：项目态 7 节点/5 连线、中心态 7 节点/2 连线；节点、连线、风险筛选、明细展开、
  中心下钻和 Journey 跳转均实际操作。最终等待态 flow 为 526–654px、风险标题 top 799px；
  活动详情态风险标题 top 799px；1280/1920 页面横向溢出均为 0。
- 独立视觉会商：Round 1 `revise`，同一 Grok Build 会话修订复核后 advisory `accept`；Codex
  又关闭其指出的两行标签和中心空主阶段残余。
- 执行审计、会商 validate 和 review gate 均须为 `ok=true` 后本记录才生效。

## 5. 明确保留的不确定性

- 只使用合成数据，不证明任何真实项目阶段解析、人数、风险或医学正确性。
- 原生 `累计到达` select 的 ego 自动化操作结果不确定；其路由/渲染仅由确定性测试证明。
- 未补拍 12 人同列真实截图；该几何由 render contract 锁定。
- 未单独复核 1440px；1280 和 1920 通过不等于全部屏幕尺寸验收。
- 既存前端 bundle 大小提示未在本切处理。

## 6. 下一阶段计划

下一纵切定为 R7 Slice-07C：把“运行入口—后台进度—结果看板—Patient Journey”串成三模式
产品闭环，并验证全量运行与基于上一运行的增量更新在同一项目中的身份、截止点和结果回看。

步骤：

1. 先冻结三模式端到端 UI/路由/状态合同，明确全量、定期新增全量 listing、锁库后修订全量
   listing 三类输入及前次运行选择；不得把文件差异等同于医学变化。
2. 设计最少操作的中文启动向导：模式、数据批次、前次运行、特殊自然语义风险规则、模型配置
   状态；默认值必须可解释且不显示后端标识。
3. 将已接受的后台进度、恢复/停止与最终项目/中心看板接成一条可刷新、可离页、可回看的路径；
   终态入口保持同一 project/run/snapshot/cutoff 身份。
4. 用 synthetic 三模式矩阵验证首次全量、定期增量、锁库修订增量、失败恢复、重新进入和结果
   对账；继续使用 ego(lite)，不启动 8911，不运行真实项目。
5. 完成独立视觉/交互会商后再决定是否进入 R7 备份迁移或更宽的功能纵切。
