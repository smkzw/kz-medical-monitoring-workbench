# Task Context: mw_word_real_acceptance_20260719

Created: 2026-07-19 17:13:51
Objective: 生成修复后的真实医学写作项目DOCX，在Microsoft Word完成原生多级标题、可跳转目录、首页、字体、表格和页眉页脚实机验收，并修复发现的问题
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- 当前实现：
  - `services/api/app/medical_writing_document_exporter.py`
  - `services/api/app/medical_writing_table_exporter.py`
- 恢复记录：
  - `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TASK_RECORD.md`
  - `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/SOFT_PAUSE_RESUME.md`
- 首页/摘要最高参照：
  `/Users/smkzw/Documents/康哲项目资料/CMS-D017/4.方案/PNH/方案摘要/CMS-D017-PNH-方案摘要_v0.2.docx`
- 完整方案标题、编号、目录参照：
  `/Users/smkzw/Documents/康哲项目资料/模版/方案模版/CMS-D017Ⅰ期方案-v1.1-20260209-clean.docx`
- Microsoft Word 是最终版式、域更新和目录跳转的验收环境；LibreOffice
  仅用于预检。

## Scope

- In scope:
  - 用当前源码生成真实绿地项目DOCX；
  - 检查OOXML中的原生Heading 1～4、多级编号、TOC域、字体、颜色、
    页眉页脚、表格和引用结构；
  - 在Microsoft Word更新全部域并保存；
  - 验证目录父子编号、点击跳转、Word样式选择器中的原生标题样式、
    首页和正文/表格视觉；
  - 修复本轮验收直接发现的导出缺陷并回归。
- Out of scope:
  - 不改写临床内容；
  - 不把LibreOffice结果当作Word最终验收；
  - 不改动稳定运行时的数据；
  - 不在本任务内处理AD候选医学质量盲审。

## Success Criteria

- 修复后真实项目DOCX由Microsoft Word无修复提示打开、更新域并保存；
- 目录显示1～4级父子编号，目录项可点击跳转到对应标题；
- Heading 1～4作为Word原生可编辑样式存在并绑定同一原生多级列表；
- 首页、页眉页脚、正文、目录和实际表格没有非用户指定的蓝色文字或蓝色
  填充；
- 全文中文run使用宋体，英文与数字使用Times New Roman；
- PAGE/NUMPAGES、图表目录、参考文献链接和源文件保真路径无回归；
- 相关自动化测试、OOXML结构检查、Word保存后视觉检查均通过；
- 验收文件、PDF、截图和检查报告落入
  `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/docx_preflight_v3/`。

## Risk Boundaries

- 只写项目记录目录和隔离验收输出；不覆盖权威模板或用户源DOCX。
- 不触碰稳定SQLite数据；若需API，使用隔离运行时。
- Word自动化遇到普通兼容性/更新域确认弹窗可按用户既有授权确认；
  不处理密码、权限、付款或账号类弹窗。
- 模型输出仅作证据；Codex负责最终Word、OOXML和生产接受判断。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-19 17:13:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-19: 从无损暂停点恢复；发现稳定`8911`当前返回502，故不沿用暂停
  前健康状态。先走离线真实DOCX生成与Word验收，不写稳定运行时数据。
- 2026-07-19: Microsoft Word实机发现原多级编号缺少Word兼容元数据，二至
  四级标题错误继承父级数字。按权威完整方案的`nsid`、`tmpl`、
  `restartNumberingAfterBreak`和缩进定义修复后，真实D017-PNH候选在
  Word中正确显示`4 / 4.1 / 4.1.1`；34项定向回归通过，Word更新目录并
  保存后生成159个目录超链接和159个`_Toc`书签。
- 2026-07-19: 用户否决当前方案摘要及全文章节骨架。纠正后的权威规则：
  公司提供的最高优先级方案摘要和完整方案决定实际章节、内容与格式；
  竞品方案用于验证跨项目通用性；ICH M11不得再作为默认主骨架，仅在
  本地参考互相混乱/冲突、M11对该细节有更优规范、且竞品方案普遍包含
  该内容时作为裁决依据。当前编号修复保留，但基于错误M11主树生成的
  D017候选不得进入发布验收。
