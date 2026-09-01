# Conference Context: mm_r5_s7_event_icon_visual_acceptance_20260827

Created: 2026-08-27 12:28:40
Objective: 以真实资深医学监查人员视角审阅R5 Patient Journey最新1600x1000普通和高密度截图及运行页面：重点判断八域图标是否美观、语义直观、中文标签是否清晰、风险标记是否抢占或混淆、横向时间先后是否一眼可见，并报告P0-P4；不得仅判断能否显示或流程能否跑通。
Task type: `visual_delivery_conference`
Risk: `medium`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair. The effective visual participant chain is `kimi-code/k3-256k:medium -> cursor/cursor-grok-4.6:high -> grok-build/grok-4.6:high -> opencode-go/muse-spark-1.2-contributor:xhigh -> codex/gpt-5.6-luna:max`; it is filtered against the actual execution route nodes recorded below before dispatch.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex, logic-heavy, evidence-sensitive, artifact-heavy, code-review, and high-risk contradiction work uses a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/google-antigravity `gemini-3.7-flash` (high) -> Pi/OpenCode Go `muse-spark-1.2-contributor` (xhigh) -> Kimi Code `k3-256k` (high) -> Codex subAgent `gpt-5.6-luna` (max). Participant 2 is Grok Build `grok-4.6` (high) -> Grok Build `grok-4.6` (medium) -> Pi/cms-router `minimax-m3` (high). Codex remains the final authority.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r5_s7_event_icon_refinement_20260827`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `cursor-cli/auto`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- 当前 R5 源码：`frontend/src/features/medical-monitoring/r5/`。
- 当前普通/高密度浏览器证据：`artifacts/mm_r5_s7_patient_journey_timeline_correction_20260827/`。
- 合成运行边界：`WORKBENCH_R5_S7_FIXTURE_MODE=true`；普通受试者 `s7-subject-10008`、高密度受试者 `s7-subject-density-001`、日期边界受试者 `s7-subject-date-001`。
- 用户确认的体验目标：中文原生、风险重点突出、八域事件可区分、横向时间先后可见。
- Do not add production paths unless the user explicitly authorized reading them for this task.

## Scope

- In scope: 八域图标、图例、泳道头、轨道事件、风险徽标、日期待确认区、三档语义缩放、普通/高密度 Patient Journey。
- Out of scope: 指标趋势业务重构、真实项目运行、医学写作子系统、安全专项设计或测试。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 120 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. A catalog/auth/transport health preflight timeout or malformed response is diagnostic and must still allow one live route attempt; explicit user routes also proceed when the catalog is stale or incomplete, while a genuinely missing CLI or native transport boundary may block. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-08-27 12:28:40: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-27: Kimi K3 同一 session 多轮审阅；Codex 依次关闭右缘裁字、AE 图标语义、月份网格/访视压字、日期待确认区图标、风险卡片层叠、聚合文案与遮挡。最终参与者结论为无存活 P0-P2；Codex 又完成 MH 图标与短文案打磨。
