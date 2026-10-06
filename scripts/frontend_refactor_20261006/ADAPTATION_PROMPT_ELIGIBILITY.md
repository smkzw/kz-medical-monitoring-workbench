# 给入排审核子系统 Agent 的适配指令（转发原文）

> 背景：任务所有者已重构工作台默认首页的「新建项目」流程（commit a05a62ef，仓库 kz-medical-monitoring-workbench）。首页不再收集项目信息，改为**子系统多选**：用户勾选要启用的子系统（医学写作/医学监查/入排审核）后，直接跳转到**首个选中子系统**，项目信息在**该子系统页面上的统一配置面板**中填写并创建。只选入排时，用户会直接落到**入排审核页（`eligibility`）**并在那里配置项目信息。

## 你们需要适配的内容（入排审核侧）

1. **接收建项交接（contract）**：
   - 首页选择含入排的子系统组合后会导航到 `eligibility` 页（仅当入排是首个选中子系统——即用户没同时选写作/监查，顺序为 写作→监查→入排），并在 **sessionStorage** 写入一次性交接：key = `workbench:new-project-handoff`，value = `{"modules":["eligibility_review", ...]}`。
   - URL 可能带 `?new_project=1`。
   - **当前共享实现**：App 根组件会自动消费交接并弹出共享 `NewProjectConfigPanel`（基本信息表单：项目名称/试验药物/适应症/研究分期），创建时 `POST /api/projects` 的 `modules` 会传**交接完整列表**，创建成功后按用户选择路由——仅选入排时落到 `eligibility` 页。
   - **适配选项 A（最小）**：无需改动——共享面板已承接；只需回归验证入排页在新项目（空状态）下可正常开始配置。
   - **适配选项 B（推荐）**：在入排页内渲染你们自己的建项/配置引导（替换共享面板）：检测 handoff（读 sessionStorage `workbench:new-project-handoff` 并删除，或 URL `?new_project=1`），展示你们的专属表单（可加入排特有字段，如筛选标准来源），创建时 `modules` 必须传交接完整列表，创建后留在入排页进入你们的配置流程。

2. **后端合同不变**：`POST /api/projects` 支持 `modules: ["eligibility_review", ...]`（枚举已含 eligibility_review）。注意后端会补齐 dashboard/approvals/medical_writing 等默认模块——**判定"用户意图"请用 handoff 里的 modules，不要用后端返回值**。

3. **多选场景**：入排与写作/监查同选时，创建发生在首个子系统（写作或监查）；你们的页面需在"项目已存在、入排未配置"时从总看板模块矩阵正常进入（现状已有，回归即可）。

4. **设计语言**：对齐 kangzhe-design（Liquid Glass：玻璃卡、无彩色边条、统一圆角、字号层级）——功能优先、美观统一其次。参考 `.subsystem-select-card` / `.new-project-config-panel` 样式。

5. **不要动的东西**：首页对话框、`SUBSYSTEM_OPTIONS`、handoff key、intent 路由——三子系统共享契约，找任务所有者（监查侧 Agent）协调变更。

## 回归清单（最小）
- [ ] 首页只选「入排审核」→ 直跳入排页 → 配置面板出现 → 建项成功 → 留在入排页可开始配置
- [ ] 首页选「入排+监查」→ 跳监查页（首个）建项 → 横幅提示还需配置入排 → 总看板矩阵能进入排
- [ ] 已有入排项目流程零改动
