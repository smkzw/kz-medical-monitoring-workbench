# Task Context: monitoring_checklist_chinese_labels_20260713

Created: 2026-07-13 18:23:03
Objective: Review the medical-monitoring seven-column checklist Chinese labels and risk-category terms for concise, accurate Chinese clinical-trial usage across RUX-03-002 and MY009-UC
Task type: `chinese_label_sentence_review`
Risk: `high`
Selected agent route: `buddy` / `deepseek-v4-pro` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User-required column labels: `受试者编号`、`中心编号`、`风险级别`、`风险类别`、`具体风险项`、`当前处置`、`更新时间`.
- User-required concise risk-category examples include `AE漏报`、`MH漏报`、`CS/NCS判定不合理`、`禁用药PD`、`方案执行PD`; category should act as the short label for the key medical reason.
- Current project-agnostic primary categories: `AE漏报`、`MH漏报`、`CS/NCS判定`、`实验室异常`、`禁用药PD`、`访视时间PD`、`用药依从性`、`方案执行PD`、`试验药物执行PD`、`疗效评估`; optional collaboration marker: `Safety/PV`.
- Current row-status label: `待医学复核`.
- Current RUX examples: `S01017 ALT/AST >3xULN，需中断用药复核` -> `实验室异常` + `Safety/PV`; `S03040 治疗期BSA超过20%，需停药/计划外访视复核` -> `方案执行PD`.
- Current MY009 examples: `S01003 试验药物服用记录需核对` -> `用药依从性`; `S01003 临床意义实验室异常需核对AE/复测` -> `CS/NCS判定` + `Safety/PV`.
- `CM` is restricted to non-investigational concomitant medication/treatment. Study-drug interruption, restart, and dose adjustment are separate investigational-product changes.

## Scope

- In scope: Chinese clinical-trial terminology, brevity, ambiguity risk, label consistency, and whether current categories communicate the immediate medical reason without overstating an unconfirmed conclusion.
- Out of scope: UI layout, code implementation, risk-rule logic, medical adjudication of individual rows, web research, and any source-file modification.

## Success Criteria

- Return a keep/change decision for every column label and current risk-category label.
- For every proposed change, provide the exact replacement and one-sentence clinical-language rationale.
- Preserve the boundary between a review trigger and a confirmed medical conclusion.
- Flag only P0/P1/P2 wording issues; do not add new features or categories without evidence.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-13 18:23:03: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-13: Codex supplied the exact user requirement and two-project verified examples; no raw private documents are required for this language gate.
