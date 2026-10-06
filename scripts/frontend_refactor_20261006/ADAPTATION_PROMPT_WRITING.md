# 给医学写作子系统 Agent 的适配指令（转发原文）

> 背景：任务所有者已重构工作台默认首页的「新建项目」流程（commit a05a62ef，仓库 kz-medical-monitoring-workbench）。首页不再收集项目信息，改为**子系统多选**：用户勾选要启用的子系统（医学写作/医学监查/入排审核）后，直接跳转到**首个选中子系统**，项目信息（名称/试验药物/适应症/研究分期）在**该子系统页面上的统一配置面板**中填写并创建。只选一个子系统时就只去那一个子系统配置。

## 你们需要适配的内容（医学写作侧）

1. **接收建项交接（contract）**：
   - 首页选择子系统后会导航到你的页面（`writing`），并在 **sessionStorage** 写入一次性交接：key = `workbench:new-project-handoff`，value = `{"modules":["medical_writing", ...]}`（可能含你之外的多选模块，如 `medical_monitoring`/`eligibility_review`）。
   - 同时 URL 可能带 `?new_project=1`（深链/刷新恢复用）。
   - **当前已有一层共享实现**：App 根组件会自动消费这个交接并弹出共享的 `NewProjectConfigPanel`（含基本信息表单；当写作被选中时会额外显示你们熟悉的两个入口「从零开始 / 导入方案摘要」，摘要导入仍走 `MedicalWritingSynopsisProjectIntake`）。创建成功后按用户选择路由到对应子系统工作区。
   - **你们的适配选项 A（最小）**：什么都不做——共享面板已能承接写作建项；只需回归验证你们的两个入口在面板里正常。
   - **适配选项 B（推荐）**：把建项配置内嵌进你们自己的写作工作区首屏（替换/接管共享面板），例如：检测到 handoff 后在写作页内渲染你们自己的引导（两阶段反问/摘要导入），创建后直接进入你们的章节流程。若你们接管，请调用 `consumeNewProjectHandoff()`（App.jsx 导出的辅助函数同款逻辑：读 sessionStorage key `workbench:new-project-handoff` 并删除）并自行调 `POST /api/projects`（modules 必须传**交接里完整的 modules 列表**，不要只传写作——多选场景下其他子系统依赖同一项目）。

2. **创建请求不变**：`POST /api/projects` 合同没动（project_name/product_name/indication/study_phase/modules/idempotency_key）。注意后端会自动补齐 dashboard/approvals 等默认模块——前端路由现在按"用户选择的 modules（intent）"而不是后端返回的 modules 判定落点，你们如有自己的落点逻辑也请按 intent 判定。

3. **多选场景**：用户同时选了写作+监查/入排时，首个子系统（按 写作→监查→入排 顺序）承担创建；创建成功横幅会提示"完成本子系统配置后，可回到项目总看板进入其余子系统"。请确保你们的页面在项目已存在但写作尚未配置时，能从总看板模块矩阵正常进入并开始配置（这一直是现状，回归即可）。

4. **设计语言**：若你们改面板样式，请对齐 kangzhe-design（Liquid Glass：玻璃卡、无彩色边条、统一圆角、字号层级）——功能优先、美观统一其次、不机械遵循。参考本次提交里 `.subsystem-select-card` / `.new-project-config-panel` 的样式写法。

5. **不要动的东西**：首页对话框（`.new-project-subsystem-select`）、`SUBSYSTEM_OPTIONS` 常量、handoff key、`handleProjectCreated` 的 intent 路由——这些是三子系统共享契约。有问题找任务所有者（监查侧 Agent）协调。

## 回归清单（最小）
- [ ] 首页只选「医学写作」→ 跳写作页 → 面板出现 → 「从零开始」建项成功 → 落写作工作区
- [ ] 面板里「导入方案摘要」上传 docx → 提取确认 → 创建成功 → 落写作工作区
- [ ] 首页选「写作+监查」→ 跳写作页（首个子系统）→ 建项成功后横幅提示还需配置监查 → 总看板模块矩阵能进监查
- [ ] 你们在写的项目不受影响（已有项目流程零改动）
