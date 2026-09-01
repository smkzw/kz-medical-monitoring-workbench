# Task Context: mw_blank_section_ai_release_20260720

Created: 2026-07-20 01:57:34
Objective: 闭环医学写作空白章节真实DeepSeek起草：保持空白锚点审计身份，禁止空来源伪证据，生成3至5个实质正文候选并完成确定性、真实AI、浏览器和持久化验收
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_writing_frontend_kimi_progressive_20260719/TASK_RECORD.md`
- `records/active_slices/medical_writing_frontend_kimi_progressive_20260719/blank_section_ai_task_evidence/blank_section_ai_task_state.json`
- `frontend/src/App.jsx`
- `services/api/app/medical_writing.py`
- `services/api/app/ai_task_runner.py`
- `services/api/app/medical_writing_revision_prompts.py`
- `tests/test_ai_task_runner.py`
- `tests/test_medical_writing_greenfield_runtime.py`
- 当前隔离运行时必须与当前源码指纹一致，并直接使用工作台配置的
  `deepseek/deepseek-v4-pro`；稳定`5174/8911`及稳定数据库不作为写入目标。

## Scope

- In scope:
  - 保留空白greenfield正文锚点的`source_id/source_entry_id/locator`审计身份；
  - 医学写作输出归一化时删除对空文本来源的evidence span及候选引用；
  - 真实非空StudyDefinition、竞品证据和参考语料继续执行严格quote/locator校验；
  - 增加空来源、混合真实来源、候选引用清理和非空来源失败关闭的测试；
  - 当前源码隔离API/前端下执行真实DeepSeek空白章节3至5候选、浏览器展示、
    采用、保存、刷新及重启读取。
- Out of scope:
  - 不修改AI-first prefill合同、ClinicalTrials.gov检索、DOCX导出器或稳定运行数据；
  - 不放宽真实来源的证据校验，不把模型生成文本当作来源；
  - 不新增第二医学批准门，不修改组织级正式放行。

## Success Criteria

- 空白章节请求保持`selected_text=""`、`anchor_type=section`和精确body locator。
- 任何`text_preview=""`的锚点来源都不能形成evidence span或候选
  `evidence_span_ids`，但仍保留在线程和AI run输入来源审计中。
- 非空来源的quote缺失、错引或locator错误继续失败关闭。
- 真实DeepSeek返回3至5个实质正文候选，不重复章节标题，无TBD/占位符，
  项目事实与StudyDefinition一致；候选证据仅引用非空真实来源。
- 用户采用候选后工作副本保存成功，刷新及隔离前后端重启后仍可读取，
  并保持来源和revision thread审计链。
- 聚焦测试、相关回归、前端合同、构建和真实浏览器证据全部通过。

## Risk Boundaries

- 允许写入`services/api/app/ai_task_runner.py`、直接相关测试、隔离证据与本任务记录。
- 修改前读取当前文件，保留并行用户/Agent改动；不触碰DOCX后端和稳定运行数据。
- 只删除无法承载事实的空来源证据引用；不得以此容忍模型漏引任何非空来源。
- Codex直接执行并负责最终源码、测试、真实AI、浏览器和持久化验收。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-20 01:57:34: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-20 02:00: 初始事实复核：前端任务路由已正确；真实DeepSeek到达
  `/revision-threads`后因空greenfield锚点来源被模型错误生成为无quote
  evidence span而409。根因位于AI输出归一化/证据校验边界，不是按钮、
  provider连通性或章节定位。
