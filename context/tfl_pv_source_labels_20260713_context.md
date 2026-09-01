# Task Context: tfl_pv_source_labels_20260713

Created: 2026-07-13 02:52:01
Objective: 审查TFL与安全/PV来源准入前端新增中文标签及提示是否符合国内临床试验医学经理语境。
Task type: `chinese_label_sentence_review`
Risk: `medium`
Selected agent route: `buddy` / `deepseek-v4-pro` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- 用户边界：只做文件技术可读性和内容一致性核验；warning/mismatch可由资深医学用户逐项确认沿用；确认后原状态不改为匹配。
- 待审标签：`来源内容核验`、`当前TFL审阅存在待确认来源`、`当前安全信号审阅与PV协同存在待确认来源`、`暂不可晋级`、`可进行医学审阅`、`确认该来源`、`确认沿用`、`已确认沿用`、`来源已就绪`。
- 待审提示：`以下信息尚未通过自动核验。请逐项对照原始资料；确认沿用不会把原状态改为匹配。`
- 待审提示：`确认只改变使用状态；原提示、确认理由、操作者和来源版本继续保留。`
- 待审提示：`写作引用候选需要来源已准入、已配对数据集，并基于当前来源版本完成医学审阅。`
- 待审提示：`标记PV协同确认前，需要来源已准入，并基于当前来源版本保存医学意见形成“医学已复核”状态。`

## Scope

- In scope: 判断上述短标签和提示是否自然、专业、边界准确；仅提出必要的逐条替换建议。
- Out of scope: 改代码、改产品逻辑、改临床或PV专业结论、引入安全扫描概念。

## Success Criteria

- 避免“系统自动批准/放行/判定匹配”的误导。
- TFL与PV语境边界明确，中文自然且不冗长。
- 每条建议给出保留或替换结论及理由。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-13 02:52:01: Task initialized by `tools/hermes_workflow_guard.py init-task`.
