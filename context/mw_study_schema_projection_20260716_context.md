# Task Context: mw_study_schema_projection_20260716

Created: 2026-07-16 22:10:17
Objective: 补齐医学写作研究流程图受治理工作副本投影、Word SVG加PNG回退导出、前端插入更新和双真实项目端到端验收
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/Documents/康哲项目资料/CMS-D017/4.方案/PNH/方案摘要/CMS-D017-PNH-方案摘要_v0.2.docx`
- `/Users/smkzw/Documents/康哲项目资料/CMS-D017/4.方案/CMS-D017Ⅰ期方案-v1.1-20260209-clean.docx`
- `/Users/smkzw/Documents/指导原则及临床试验规范合集/ICH指导原则/M11模板中文版.pdf`，仅作为结构语义依据。
- 当前隔离运行态中由上述两个真实项目从原始文件建立的StudyDefinition、工作副本、浏览器交互及DOCX导出产物。
- RA仅作为从零构建的合成反例，不得作为真实项目语料或外部事实来源。

## Scope

- In scope: 受治理研究流程图投影、工作副本防篡改、确定性SVG、PNG兼容回退、Word图编号/书签/横纵向分节、专用桌面编辑器、双真实项目端到端验收和RA反例。
- Out of scope: 自由绘图、通过拖动改变医学事实、自动补全未确认剂量、研究流程表、稳定端口真实项目数据写入，以及本切片之外的医学写作功能。

## Success Criteria

- 当前确认StudyDefinition与布局可插入并更新M11 1.2工作副本；通用保存不能新增、篡改或静默删除受治理图对象。
- 相同语义输入得到确定性、安全的SVG；Word包同时含SVG主图和PNG回退，图编号、书签和图目录元数据稳定。
- 简单PNH图保持纵向；复杂D017 SAD/MAD图自动使用横向页面并在图后恢复纵向正文。
- PNH和D017浏览器新增、编辑、保存、删除、全屏、重载与投影均通过，运行时异常和控制台错误为0。
- RA反例锁定开放不等于单臂、剂量探索不等于递增、队列启用依赖不等于受试者流转。
- 聚焦和广回归、前端生产构建、DOCX/PDF中文字体及像素可见性检查通过。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-16 22:10:17: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-16: 守卫选择`codex/codex-main`直接执行；根据最新全局AGENTS，本条连贯主线不创建Codex SubAgent，也不启动不必要的会商。
- 2026-07-16: 双真实项目浏览器QC通过；发现并修复匿名ProseMirror插件键冲突、异步等待竞态和复杂图边标签遮挡。
- 2026-07-16: Word实物QC发现D017双面板在纵向页过小；改为基于SVG画布宽度/节点数自动插入A4横向分节，图后恢复A4纵向正文。PNH仍保持纵向。
- 2026-07-16: 双项目DOCX/PDF、RA合成反例、124项广回归及Vite生产构建通过，进入Codex评审收口。
