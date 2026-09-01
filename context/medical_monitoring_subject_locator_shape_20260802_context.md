# Task Context: medical_monitoring_subject_locator_shape_20260802

Created: 2026-08-02 17:37:23
Objective: 将 Subject Timeline/Profile 显式来源定位字段的 scalar/混合非字符串形状异常显式化，避免将错误值渲染为可信 locator，并在个例消费层给出克制的异常提示
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

上一切片只处理了风险提示关联字段的 malformed 形状。继续核对个例来源时发现 `explicitSourceLocator` 会把 locator 数组中的数字、对象等非字符串通过 `String(...)` 转成看似可信的来源定位，造成数据敏感用户无法区分可核对定位与异常字段。本轮只收紧来源定位消费边界。

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
- `frontend/AGENTS.md` 与工作区 `AGENTS.md`
- 当前 B6/C14 gate、release audit/coverage、保护性 App/styles 哈希和端口状态

## Scope

- In scope: 显式来源 locator 字段的字符串/数组形状识别；保留合法字符串；新增 `subjectSourceLocatorState`；Subject Timeline/Profile 显示 `来源定位形状异常`；谱系摘要不把 malformed locator 计作 bound；补充离线回归与记录。
- Out of scope: `App.jsx`、`styles.css`、API/backend、SQLite、权限、风险事实、处置、B6/C13/C14、aggregate/CAS、source-token、服务、浏览器、真实项目、医学写作和任何运行库写入。

## Success Criteria

- 非字符串 locator 不得被强制转成可疑来源文本；混合数组保留可读字符串但明确 malformed。
- 个例行显示异常提示，tooltip 说明不能据此证明来源真实性或无风险；合法 locator 显示保持不变。
- `subjectEvidenceLineageSummary` 只把 bound locator 计入 traced，malformed 进入未完整定位并可计数。
- Subject model、医学监查 Node、相关 Python 合同、Vite、release-gate 与 Hermes review-gate 通过；release 不得解锁。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 17:37:23: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: 发现 `String(item || "")` 会把非字符串 locator 变成可疑来源文本；改为字段形状感知的纯函数并在 Timeline 行 tooltip 公开异常边界。
- 2026-08-02: Subject model、Node 22/22、Python 合同 64、Vite 1925 modules、release-gate 7 均通过；未启动服务/provider/browser/真实项目。
