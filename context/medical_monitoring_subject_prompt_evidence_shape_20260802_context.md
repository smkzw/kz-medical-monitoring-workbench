# Task Context: medical_monitoring_subject_prompt_evidence_shape_20260802

Created: 2026-08-02 17:29:31
Objective: 将 Subject/Profile 风险提示关联字段的 scalar/非字符串形状异常显式化，保留可用显式 ID，避免静默误读为未绑定或无风险，并完成离线验证与恢复记录
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

在继续审查 Subject Timeline / Patient Profile 的风险提示消费时发现：关联事件、指标、风险和证据字段若为 scalar，或数组混入非字符串值，原逻辑会静默丢弃并显示“未绑定关联事实”。这会让数据敏感、风险敏感的医学监查员无法区分“确实未提供”与“字段形状异常”。本轮是受限的前端模型/测试修补，不扩大到运行时或真实项目。

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`（只读确认消费路径）
- `frontend/AGENTS.md` 与工作区 `AGENTS.md`
- 当前 B6/C14 gate 文件、保护性 `App.jsx`/`styles.css` 哈希和停止端口状态

## Scope

- In scope: `riskPromptEvidenceSummary` 的显式字符串关联字段形状识别；保留可读的显式字符串 ID；新增 malformed/valid 状态和边界文案；补充模型断言；离线回归和证据记录。
- Out of scope: `App.jsx`、`styles.css`、API/backend、SQLite、权限、风险事实、严重度、处置、B6/C13/C14、aggregate/CAS、source-token、服务、浏览器、真实项目和任何写运行库。

## Success Criteria

- scalar 或混合非字符串关联字段不得再静默表现为“未绑定”；摘要明确显示 `关联证据形状异常`。
- 合法数组中的字符串及 malformed payload 中可读的显式字符串 ID 保留；不从标题、日期、计数、顺序或自由文本推断关联。
- Subject model、医学监查 Node、相关前端 Python 合同、Vite build、release gate 均通过；release 状态不得因本轮改变。
- 形成可复制的 active-slice、review、metrics 和 LOOP 4.15 记录。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 17:29:31: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: 核对中断补丁已落盘；发现 scalar 字符串虽应标记 malformed 但仍可安全保留为显式 ID，补强 `explicitStringList` 并增加断言。
- 2026-08-02: Subject model、医学监查 Node 22/22、相关 Python 合同 64、Vite 1925 modules、release-gate 7 均通过；错误尝试的不存在 `tests/test_frontend_contracts.py` 未运行测试且未改文件，随后使用四份既有合同文件正确重跑。
- 2026-08-02: 尚未启动服务/provider/API/browser/SQLite/真实项目；8911/5174 无监听；B6/C14 继续 fail-closed。
