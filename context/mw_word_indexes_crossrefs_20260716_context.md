# Task Context: mw_word_indexes_crossrefs_20260716

Created: 2026-07-16 23:31:02
Objective: 完成医学写作方案的目录、表目录、图目录、稳定编号书签和交叉引用闭环，并用两个真实项目完成Word/PDF实物验收
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/Documents/康哲项目资料/CMS-D017/4.方案/CMS-D017Ⅰ期方案-v1.1-20260209-clean.docx`：公司完整方案中TOC、图目录、表目录、SEQ、REF与书签的主要实现参照。
- `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/RUX-03-002-自查文件包-20260107/10-临床试验重要文件/1-临床试验方案/V1.3版-2024.8.14/磷酸芦可替尼乳膏-AD3期临床研究方案V1.3-clean-20240814.docx`：静态表格列表及正文表题/REF参照。
- 当前`ProtocolDocument`、工作副本、结构化表格、研究流程图和DOCX导出器。
- 用户已明确：首页排版表、研究摘要大表、正文可见表格必须分型；目录、表目录、图目录和交叉引用应形成终稿级Word输出。

## Scope

- In scope: 动态TOC/图目录/表目录、Word字段自动更新提示、正文表图稳定SEQ/书签、表图交叉引用、旧静态目录投影替换、双真实项目Word/PDF验收。
- Out of scope: 把页码或目录文本写回StudyDefinition、把首页/摘要/缩略语/修订记录等布局对象编号为正文表、自动猜测旧纯文本“见表X”指向、修改原始DOCX。

## Success Criteria

- 导出件含可更新的主目录、表目录和图目录；原导入件的静态旧页码列表不重复输出。
- 正文内容表和研究流程图使用稳定书签与SEQ字段；首页布局表、摘要表和缩略语表不进入表目录。
- 新插入交叉引用绑定稳定对象ID，目标删除/失效时导出失败关闭，不静默显示错误编号。
- PNH/D017或RUX/D001至少两个真实项目完成DOCX解包、Word字段、PDF页面和中文可见性检查。
- 相关单元/API/前端合同、生产构建和真实浏览器流程通过。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-16 23:31:02: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-16: 守卫选择Codex直接执行；本切片需要统一控制Word字段、表图对象身份和实物验收，不创建惯性Codex SubAgent，也不派发Hermes。
- 2026-07-16: OOXML审计确认D017使用`TOC \\o "1-3"`、`TOC \\c "图"`、`TOC \\c "表"`、`SEQ`、`REF`和书签；RUX导入后主TOC字段丢失且表格列表退化为静态旧页码，成为本轮首要修复对象。
