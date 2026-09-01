# Codex Review: mw_study_schema_projection_20260716

Date: 2026-07-16
Delegated-agent output: `runs/codex_mw_study_schema_projection_20260716.md`

## Verdict

Pass.

## Boundary Check

- 守卫选择Codex直接执行，没有外部执行模型的生产写入。
- 改动限定在研究流程图合同、工作副本投影、SVG/PNG/Word导出、专用前端交互、测试和本切片记录。
- 隔离SQLite/API/前端用于真实项目QC；稳定项目数据未被测试写入污染。

## Codex Verification

- PNH、D017原始文件事实与研究设计图已重新核对。
- 隔离浏览器双项目报告通过，运行时异常和控制台错误均为0；1920x1080普通/全屏状态无页面横向溢出。
- 124项研究流程图、投影、DOCX导出、API和前端合同测试通过；Vite生产构建通过。
- PNH与D017 DOCX均完成解包检查；D017分节为纵向/横向/纵向，PNH为纵向。
- 两份DOCX均转PDF并完成原分辨率视觉检查；D017图与图题同页、无裁切，后续正文恢复纵向。
- RA合成反例测试通过且明确标注为非真实项目。

## Delegated-Agent Output Review

没有 delegated-agent 输出。Codex直接核对了临床语义、浏览器运行态和文档实物。未把待确认剂量补成确定事实；未把RA合成场景纳入真实语料；未把队列启用关系误画为受试者流转。

## Hermes Route Decision

`hermes_workflow_guard.py init-task`将本切片路由为`codex/codex-main`。按最新全局AGENTS，本任务是一条需要统一临床语义、生产写入和最终浏览器/DOCX/PDF验收的连贯主线，不满足Execution Module的多独立执行项条件，也没有需要Conference挑战的未决观点，因此没有向Hermes派发任务。该未派发是守卫路由结果，不是遗漏会商。

## Residual Risk

- 既有Vite主包约1.29 MB，构建给出代码拆包提示；它是全局性能债务，不阻断本切片。
- LibreOffice渲染用于自动QC，最终生产还需持续保留Microsoft Word实机回归，但SVG+PNG双路径和Word包结构已验证。
