# W4 AI推荐优先前端：只读代码地图与验收合同

## 结论

W4应复用现有`AuthoringPrefillPackage -> StudyDefinition`主链，不建立第二套状态机。当前前端
已有单字段候选、证据展示、富文本编辑、表格及全屏基础；发布阻断集中在：

1. 组合候选没有主界面，所谓批量采用仍循环调用单字段API；
2. framing/PICOS仍暴露大量空输入，用户承担从零撰写；
3. `pending_decision`没有专门交互；
4. 竞品方案完整处理入口过晚；
5. 编辑器顶部状态和运行信息继续挤压正文空间。

本轮为只读审阅，未改文件、未调用产品AI、未运行会改变运行时的浏览器测试。

## 当前代码地图

| 场景 | 主要入口 | 状态/API |
|---|---|---|
| 新建项目 | `frontend/src/App.jsx`的`AppShell` | `newProjectDraft/newProjectOpen/projects/activeProjectId`；`POST /api/projects` |
| 摘要建项 | `MedicalWritingSynopsisProjectIntake.jsx` | intake/job/imported/framing/picos；synopsis intake API |
| Framing/PICOS | `MedicalWritingAuthoringJourneySetup.jsx` | journey为服务端权威，本地为未提交草稿；stage draft/commit、prefill API |
| 竞品方案 | `WritingReferencePanel.jsx`，当前由CorpusGate渲染 | workspace、triage job、文档、解析、翻译、审核 |
| 写作编辑器 | `App.jsx`的`WritingPage`和`RichProtocolEditor` | section、working copy、AI thread/candidates、rail、版本和质量门 |
| 表格编辑 | `StructuredTableDesigner.jsx`、`TableCellRichEditor.jsx` | 表格本地草稿及单元格，随working copy保存 |
| AI后台任务 | `useDurableMwJob.js` | 持久locator、轮询、取消、重试、结果对账 |

前端没有集中API client或TypeScript合同层，多数业务组件直接`fetch`；W4必须以最终W2b/W3
Pydantic合同和真实API响应为准。

## 真实问题

- `FramingFields/PicosFields`仍含大量必填textarea、空列表和“新增规则”，高级微调仍需从零写。
- 摘要导入存在全局建项和项目内journey两套界面/API；已确认内容不得二次确认。
- `PrefillRecommendations`只有单字段候选；“低风险批量采用”是前端循环请求，必须删除。
- `pending_decision`应显示“需您选择/补全”，不能伪装成“采用推荐”。
- 竞品检索完成后仅显示数量摘要，完整处理面板到第三步才出现。
- CorpusGate的snapshot ID、过滤合同和处理链偏运行记录，应默认折叠，优先呈现研究和原文。
- 工作副本、保存状态、更新时间和警告条叠加，占用正文高度。
- `accepted_pending_medical_approval`只能保留为历史兼容状态；当前用户采用候选后直接成为
  医学决定。审批中心和翻译医学审核是其他业务，不做全局文本替换。

## W4最小改造面

1. 修改`MedicalWritingAuthoringJourneySetup.jsx`：组合候选比较、局部override、一次采纳；
   删除循环单字段批量采用。
2. 新建`AuthoringCandidatePackagePanel.jsx`：纯展示field/module/design_package，不自行
   请求API。
3. 新建`AuthoringCompetitorDrawer.jsx`：第一步检索完成后即可打开，并复用现有
   `WritingReferencePanel`。
4. `WritingReferencePanel.jsx`只增加embedded/drawer/compact展示参数，不复制业务状态。
5. `App.jsx`压缩编辑器状态栏；AI栏继续聚焦候选和证据，不改TipTap/表格实例边界。
6. 修改`styles.css`；不改`StructuredTableDesigner.jsx`和`TableCellRichEditor.jsx`。
7. 更新既有前端QC并新增组合候选原子采纳专项测试。

候选卡默认显示推荐方案、最多4个实质备选、临床取舍、证据原文、证据缺口和影响路径；
locator/catalog hash/AI run ID只进入“溯源详情”。`pending_decision`禁用整包采用，仅在用户
提供明确path override后提交。成功反馈完全使用W3回执，不由前端推测。

## 桌面端布局

- 建项：全宽主区，候选约70%，右侧仅证据摘要和后台任务状态。
- 编辑：正文`minmax(760px, 1fr)`，AI栏约380-420px；目录继续使用抽屉。
- 工作副本状态压成单行：版本、保存状态、保存、版本记录、Word导出。
- AI任务使用窄进度条，显示阶段、百分比、取消/重试；失败后保留locator。
- 开关AI栏/目录时不得重新挂载TipTap，不丢选区、未保存正文或全屏状态。
- 表格继续使用独立全屏设计器和同等文字/段落格式工具，不嵌入候选布局。

## P0验收

1. 最小三项建项后自动准备建议，不重复输入药物、适应症、分期。
2. Framing与四类PICOS组合包显示1个推荐及最多4个实质备选。
3. 候选优先显示来源原文，仅locator不能算证据展示。
4. pending不能整包采用；局部override后一次请求、一次revision。
5. applied/overridden/skipped/invalidated完全按W3回执反馈。
6. 第一步即可打开竞品抽屉，关闭不丢建项草稿。
7. 刷新、切项目、409、任务失败重试不重复采纳或丢locator。
8. 1920x1080、1600x1000、1366x768无横向溢出，正文仍是主区域。
9. 正文回车/格式/全屏保存和表格输入/格式/返回无回归。

## 回归入口

- `medical_writing_authoring_prefill_frontend_qc.mjs`
- `medical_writing_new_project_isolated_qc.mjs`
- `medical_writing_authoring_journey_qc.mjs`
- `medical_writing_reference_drawer_qc.mjs`
- `worker_02_desktop_editor_isolated_qc.mjs`
- `medical_writing_editor_formatting_qc.mjs`
- `medical_writing_table_sync_qc.mjs`
- `npm --prefix frontend run build`

## 不确定性

W2b/W3尚在冻结，因此持久AI任务响应和组合采纳回执字段必须在W4实现前再对照最终源码，
不能仅依据本审阅中的预期名称。
