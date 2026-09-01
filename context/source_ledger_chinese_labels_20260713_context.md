# Task Context: source_ledger_chinese_labels_20260713

Created: 2026-07-13 03:48:39
Objective: 审阅来源台账新增中文标签和override说明是否符合中国临床试验医学经理语境，不改业务逻辑
Task type: `chinese_label_sentence_review`
Risk: `medium`
Selected agent route: `buddy` / `deepseek-v4-pro` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- 以下为当前页面实际标签与提示，不需要另读生产文件：
  - 页面：`来源台账`、`项目级资料治理`
  - 统计：`当前登记来源`、`待确认沿用`、`已确认沿用`、`技术读取失败`
  - 状态：`技术可读`、`匹配`、`需确认`、`不一致`、`可使用`、`待确认`、`已确认沿用`、`技术失败阻断`
  - 控件：`模块`、`使用状态`、`包含历史版本`、`前往模块`
  - 角色：`安全性医学复核listing`、`安全性评估资料包`、`DSUR来源文档`、`数据集与TFL资料包清单`
  - 结构检查：`个体AE复核结构`、`安全性医学复核数据结构`、`病史`、`非试验用药（CM）`、`试验用药/剂量调整`、`实验室/生命体征/心电图`
  - override标题：`逐项核对后确认沿用`
  - override提示：`仅核验技术可读性、文件角色、项目/研究标识及当前任务所需内容结构。确认沿用只改变使用状态，不会把原警告或不一致改为匹配。`
  - 勾选：`我已核对：项目/研究标识`
  - 理由：`医学确认理由`；placeholder：`说明为何当前来源仍可用于本项目，至少10个字。`
  - 历史：`核验与确认记录`、`确认理由`

## Scope

- In scope: 中国临床试验医学经理/医学总监语境下的中文自然度、状态边界、CM与试验药物变更边界、override风险提示。
- Out of scope: 改业务逻辑、改状态机、增加安全扫描、作医学/PV结论、前端视觉验收。

## Success Criteria

- 对每条文字给出`保留/建议修改`，只修改有明确收益的内容。
- 不把warning/mismatch写成已匹配，不弱化逐项确认和理由要求。
- CM必须明确为非试验用药；试验用药/剂量调整保持单列。
- 输出简洁，可直接供Codex取舍。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-13 03:48:39: Task initialized by `tools/hermes_workflow_guard.py init-task`.
