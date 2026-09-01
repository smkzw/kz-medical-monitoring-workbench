# 医学监查 P10：方案监查准备前端产品切片

日期：2026-07-30  
状态：实现、聚焦回归及真实浏览器排队态验收完成

## 1. 目标与产品边界

本切片将既有“方案监查准备”后端能力接入医学监查桌面端，服务对象为希望尽量少操作的
资深医学经理。入口保持低干扰，准备过程可关闭，独立 AI 在后台继续。

本切片明确不做以下事情：

- 不修改医学写作子系统；
- 不修改字段映射、daily run、risk export 后端；
- 不修改 `monitoring_protocol_preparation` 后端；
- 不把候选称为“待医学批准”；
- 不自动接受候选，不把候选伪装为已发布规则；
- 不展示 prompt、provider、job ID 或内部运行日志。

当前通用候选 decision API 只能改变候选状态，不能完整证明“接受候选后生成项目事实、
编译规则并发布”的产品闭环。因此本切片采用只读审核：候选明确显示“待用户确认”，
底部只提示下一步为“确认候选”。正式候选确认及规则生成留给后续完整链路。

## 2. 用户工作流

1. 用户在医学监查的“数据批次”面板标题区点击“准备方案规则”。
2. 系统读取当前项目已登记的 protocol versions，只展示 `confirmed` 版本。
3. 只有一个已确认版本时自动选中；存在多个版本时由用户选择本次监查适用版本。
4. 未启动时，系统先显示 8 个固定主题及来源准备状态，用户点击“一键准备全部主题”。
5. 启动后每 5 秒读取一次紧凑状态；排队或运行时可关闭抽屉，后台任务不受影响。
6. 重新打开时直接恢复当前项目、当前版本和各主题的真实状态，不重复提交 start。
7. 完成主题默认只显示主题名、候选数量和状态；用户展开后才查看结构化候选和原文。
8. 候选内容优先级固定为：
   - 条款正文；
   - 适用对象；
   - 条件；
   - 时间窗；
   - 阈值；
   - 例外；
   - 动作；
   - 方案原文 quote；
   - locator 作为次级溯源。

## 3. 交互与信息架构

- 入口：批次面板标题区的紧凑图标+文字按钮，不增加新的常驻大卡片。
- 容器：右侧固定抽屉，宽度上限 680px；背景保留上下文但降低视觉干扰。
- 进度：单一进度条和“已完成/总主题”计数，不展示运行日志。
- 主题：8 行折叠列表，状态使用统一的成功、待确认、运行、缺证据和异常语义。
- 候选：展开后采用线性信息区，不使用卡片嵌套。
- 来源：quote 使用左侧强调线；locator 使用小号等宽字体并置于 quote 之后。
- 底部边界：只保留一行“当前仅审核候选”的说明，不占据核心编辑区域。
- 错误：发生状态读取错误后停止自动轮询，只保留一次“重新读取”动作，避免密集重试。

## 4. 前端 API 合同

新增客户端方法：

- `listProtocolVersions(projectId)`
- `getProtocolPreparationStatus(projectId, protocolVersionId)`
- `startProtocolPreparation(projectId, protocolVersionId, { topicIds })`

全部项目和版本 ID 均逐段 URL 编码。启动默认发送 `topic_ids=[]`，表示由后端采用全部
标准主题。前端不会自动调用 start，也不会因轮询、关闭或重新打开而重复调用 start。

## 5. 代码变更

- `frontend/src/features/medical-monitoring/MedicalMonitoringBatchPanel.jsx`
  - 增加低干扰入口和抽屉挂载。
- `frontend/src/features/medical-monitoring/MedicalMonitoringProtocolPreparationPanel.jsx`
  - 新增方案版本选择、启动、5 秒轮询、主题列表、结构化候选及原文展示。
- `frontend/src/features/medical-monitoring/medicalMonitoringProtocolPreparation.mjs`
  - 新增已确认版本筛选、轮询判定、进度汇总、结构化字段投影和状态语义。
- `frontend/src/features/medical-monitoring/medicalMonitoringApi.mjs`
  - 新增 protocol versions 与 protocol preparation 客户端方法。
- `frontend/src/styles.css`
  - 新增 CMS 既有设计语言下的桌面端抽屉、主题列表、进度和证据样式。
- `frontend/src/features/medical-monitoring/medicalMonitoringApi.test.mjs`
  - 增加 8 项客户端路径、方法、编码与请求体断言。
- `frontend/src/features/medical-monitoring/medicalMonitoringProtocolPreparation.test.mjs`
  - 增加版本筛选、进度、轮询、字段投影和状态色语义断言。

## 6. 验证

### 前端 API 与状态模型

```text
node frontend/src/features/medical-monitoring/medicalMonitoringApi.test.mjs
medicalMonitoringApi: 94 passed

node frontend/src/features/medical-monitoring/medicalMonitoringProtocolPreparation.test.mjs
medicalMonitoringProtocolPreparation: 9 passed
```

### 后端合同复验

```text
.venv/bin/python -m pytest tests/test_monitoring_protocol_preparation.py -q
7 passed
```

后端合同覆盖：

- 8 个医学监查主题；
- 一键启动和幂等；
- 真实 span 去重和来源版本绑定；
- 候选保持 `proposed/pending_user_confirmation`；
- quote/locator 可追溯；
- 未确认、跨项目、来源修订不一致、未解析来源失败关闭。

### 生产构建

```text
cd frontend && npm run build
1905 modules transformed
build passed
```

Vite 仍提示已有主 bundle 超过 500kB。该提示不是本切片引入的运行错误，也未在本切片
中进行与目标无关的全应用拆包。

### 真实浏览器验收

真实页面：`http://127.0.0.1:8920/`

RUX-03-002：

- 唯一已确认版本 V1.3 自动选中；
- 8 个主题全部显示；
- 真实状态为 8 个 queued；
- start 按钮显示“已启动”且禁用，不会重复提交；
- 关闭抽屉后重新打开，仍恢复 0/8、8 个 queued；
- 入口、抽屉、主题列表无横向溢出；
- 控制台 error/warn 均为 0。

MG-K10-SAR：

- 唯一已确认版本 V2.1 自动选中；
- 8 个主题全部显示；
- 真实状态为 8 个 queued；
- start 按钮保持禁用；
- 控制台 error/warn 均为 0。

截图：

`runs/execution/medical_monitoring_p10_20260730/protocol_preparation_frontend/rux_protocol_preparation_queued.png`

截图 SHA-256：

`ecc20cd83e687623abf2028279c7772498ef58f819705bd787a0646fb3b4e9ea`

## 7. 当前真实边界与下一步

RUX 与 MG 的 16 个方案准备作业已进入产品独立 AI 持久队列，但当前仍受三个真实项目
字段映射队列占用，尚未返回真实候选。因此本切片已完成真实排队态、关闭/恢复、禁止
重复启动和无错误浏览器验收；真实候选展开的医学内容验收仍须在至少一个主题进入
`candidate_review` 后补做。

下一轮候选验收必须检查：

1. 结构化字段是否忠实于 quote；
2. 试验药物变更与非试验用 CM 是否保持边界；
3. 时间窗、阈值和例外是否完整；
4. quote 是否为主要可读内容，locator 是否保持次级；
5. 用户确认后是否存在完整的“候选 -> 项目事实 -> 规则编译 -> 发布”产品链路。

在第 5 项完整实现前，前端继续保持只读审核，不开放批量接受/拒绝。
