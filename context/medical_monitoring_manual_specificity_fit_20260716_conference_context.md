# Conference Context: medical_monitoring_manual_specificity_fit_20260716

Created: 2026-07-16 13:32:05
Objective: 审计医学监查说明书的项目特异内容边界，并将HTML图形默认适配为无需拖动即可完整阅读
Task type: `visual_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no Hermes sub-venue chair: Hermes `aishuo / MiniMax-M3` and Kimi Code (`kimi-code` / `kimi-code/kimi-for-coding`) latest authenticated model. If either is unavailable, the runner tries Grok Build `grok-4.5` (`grok-build`), then Hermes OpenCode Go `qwen3.7-plus` and `mimo-v2.5`. Hermes' own Grok route is not used.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use Grok Build `grok-4.5` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3` and Hermes OpenCode Go `deepseek-v4-flash`. Any unavailable complex-task role follows Reasonix CLI `deepseek-v4-flash`, Kimi Code (`kimi-code` / `kimi-code/kimi-for-coding`) latest authenticated model, then Hermes OpenCode Go `qwen3.7-plus` and `mimo-v2.5`. Hermes' own Grok route is not used.
- Reasonix is used here only as a declared fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统说明书.md`
- `docs/medical_monitoring_manual/医学监查子系统说明书.html`
- `tools/build_medical_monitoring_manual.cjs`
- `tools/prerender_medical_monitoring_mermaid.cjs`
- `tools/test_medical_monitoring_manual_html.cjs`
- `/Users/smkzw/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/SmkFat_310f/temp/InputTemp/0b8427db-95d6-4733-98e1-64c52be034e4.png`（仅 Codex 负责最终视觉判断）

## Scope

- In scope: 识别被误写成通用规范的适应症、量表、药物、阈值、访视、接口参数和字段示例；提出 16.3 与 23.2 的重写建议；评估图形默认适配、字体、画布高度及溢出行为。
- Out of scope: 修改医学监查工作台生产代码、改变医学风险规则边界、增加与本轮问题无关的新功能。

## Success Criteria

- 16.3 仅定义跨项目的方案提取结构和生效规则，项目药物清单移入明确标记的说明性示例。
- 23.2 的接口和数据流使用项目无关的指标集合参数，不出现 EASI/ALT/AST/HGB 等固定查询参数。
- 全文项目特异内容均处于“示例”或“项目配置”语境；通用规则不得暗含具体适应症、药名、量表、访视或阈值。
- 1920×1080 和 1440×900 默认视图下，所有图形无需横向或纵向拖动即可看到完整图形；放大、全屏和节点聚焦仍可用。
- Codex 完成实际浏览器与原始分辨率截图验收。

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use 30 and 40 respectively.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-16 13:32:05: Conference initialized by `hermes_workflow_guard.py init-conference`.
