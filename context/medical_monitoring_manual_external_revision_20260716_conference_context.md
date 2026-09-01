# Conference Context: medical_monitoring_manual_external_revision_20260716

Created: 2026-07-16 12:30:52
Objective: 将医学监查子系统说明书重构为可外发的中文交互式电子书：审校全文中文原生性，去除本机与真实项目运行信息，修复表格与图形缺陷，增加可点击展开收起缩放交互并完成桌面视觉验收
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

- `docs/medical_monitoring_manual/医学监查子系统说明书.md`：待外发的完整中文正文。
- `tools/build_medical_monitoring_manual.cjs`：电子书构建器。
- `tools/prerender_medical_monitoring_mermaid.cjs`：图形预渲染器。
- `tools/test_medical_monitoring_manual_html.cjs`：浏览器验收脚本。
- 用户截图 `codex-clipboard-71828f9b-a876-45a3-b03f-f8f80c3457c2.png`：表格表头重叠与空白占位。
- 用户截图 `codex-clipboard-b56d3cf4-3347-44ee-8f1a-53d0996a99f7.png`：第16.4节 Mermaid 语法错误。

## Scope

- In scope：全文中文原生性审阅；外发信息清理；表格与图形的网页交互；章节引用超链接；桌面端布局与无重叠验收。
- Out of scope：修改医学监查工作台生产代码、改变医学规则的科学边界、增加未经用户要求的新业务模块。

## Success Criteria

- 正文不出现真实项目名称、受试者运行日志、开发测试快照、本机路径、主笔/模型/内部来源说明。
- Kimi Code 输出逐条中文问题清单，至少包含原词、建议替换、理由和位置。
- 22 幅图均无 Mermaid 错误文本；图形可折叠、展开、放大、缩放、复位并支持全屏查看。
- 表格无重复表头、空白占位和元素重叠；长表可折叠、展开和全屏查看。
- “见第X章/§X.X/附录X”等内部引用可点击跳转。
- 1920×1080、1440×900 桌面视口无页面级横向溢出、元素交叉或不可达操作。

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

- 2026-07-16 12:30:52: Conference initialized by `hermes_workflow_guard.py init-conference`.
