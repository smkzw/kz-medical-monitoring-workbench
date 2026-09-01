# Codex Main-Venue Plan: medical_monitoring_manual_specificity_fit_20260716

Date: 2026-07-16
Objective: 审计医学监查说明书的项目特异内容边界，并将HTML图形默认适配为无需拖动即可完整阅读

## Task Decomposition

1. 全文审计项目特异的药物、阈值、量表、访视、来源表名和接口参数是否被误写为通用规则。
2. 重写 §16.3，并同步泛化 §23.2、§28.2、试验药物字段来源和项目指标集表达。
3. 修正图形默认适配，重排过度纵向或横向的复杂图。
4. 在 1920×1080 与 1440×900 完成浏览器验证，检查溢出、可读性和交互。

## Source Packet

- 权威正文：`docs/medical_monitoring_manual/医学监查子系统说明书.md`
- HTML 构建器：`tools/build_medical_monitoring_manual.cjs`
- 浏览器验收：`tools/test_medical_monitoring_manual_html.cjs`
- 用户指出的核心问题：§16.3、§23.2 和图形默认尺寸。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_monitoring_manual_specificity_fit_20260716/visual_aishuo_minimax.md` |
| `visual_kimi_code` | `kimi-code` | `kimi-code/kimi-for-coding` | `runs/conference/medical_monitoring_manual_specificity_fit_20260716/visual_kimi_code.md` |

## Sub-Venue Review

- No sub-venue chair. Codex leads the visual/design panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- 两名参与者并行完成一轮；均未超时、未启用替代模型。
- MiniMax-M3：245.601 秒；Kimi Code：268.760 秒。
- MiniMax 进程结束时出现 MCP 协程关闭警告，但正文输出完整、返回码为 0，不影响采纳。
- 无迟到输出，无需同会话追问。

## Codex Verification Checklist

- [x] §16.3 明确区分通用解构规则与说明性项目配置。
- [x] §23.2 与 §28.2 使用项目指标集，不包含固定指标。
- [x] 全文相关表名、阈值、风险标识和站点标识完成泛化。
- [x] 22 幅图默认无横向或纵向溢出。
- [x] 22 幅图可读性阈值、缩放、复位、聚焦、收起和全屏通过。
- [x] Markdown 审计、HTML 构建、SVG 预渲染和双桌面视口测试通过。
