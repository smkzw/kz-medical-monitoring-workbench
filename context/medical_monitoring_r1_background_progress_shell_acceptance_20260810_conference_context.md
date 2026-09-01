# Conference Context: medical_monitoring_r1_background_progress_shell_acceptance_20260810

Created: 2026-08-10 02:37:21
Objective: 独立挑战并验收隔离 R1 后台医学监查进度 shell，复核实际工作去重、权威进度只读投影、离页/刷新恢复、中文受众语言和真实浏览器视觉证据
Task type: `html_ppt_visual_browser`
Risk: `medium`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Grok Build `grok-4.5`, then Cursor CLI `cursor-grok-4.5-high`, then Pi/OpenCode Go `gpt-5.6-luna` (max), then Pi/Kimi `k3-256k` (high).
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/Alibaba `qwen3.8-max` (xhigh) during the Beijing 22:00-07:00 window, and outside that window its exact Qwen Max node is replaced by Pi/cms-smk `cms-model` (high); its remaining fallbacks are Pi/cms-smk `cms-model` (high), Pi/cms-smk `deepseek-v4-flash` (max), Pi/OpenCode Go `deepseek-v4-flash` (max), and Pi/DeepSeek `deepseek-v4-flash` (max). Participant 2 is Grok Build `grok-4.5`, with Cursor CLI `cursor-grok-4.5-high` and Pi/cms-router `minimax-m3` as fallbacks. Codex remains the final authority. The explicit Luna native/CLI compatibility route remains available for execution roles that declare Codex subAgent.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` 第 12 节及 `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R1 恢复点。
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/background_progress.py`、`audience_progress.py`、`store.py`。
- `poc/medical_monitoring_ai_native_r1/slices/background_progress_shell/{server.py,index.html,styles.css,app.js,docs/DATA_CONTRACT.md}`。
- `poc/medical_monitoring_ai_native_r1/tests/test_background_progress.py`。
- `poc/medical_monitoring_ai_native_r1/slices/background_progress_shell/evidence/final_state.png`。
- `output/playwright/medical_monitoring_r1_background_progress_shell_20260810/{desktop_1440x900.png,narrow_900x700.png}`。
- 本任务主会场的真实浏览器、测试输出和当前文件系统。

Frozen review inputs (SHA-256):

- `background_progress.py`: `fe1be09bbef31d21251757f72704c20d7ba04b18ad5da2c50dc5476efa886132`
- `server.py`: `e7e562d3570c2d6851705821c4bad3019179e3d594522163c96cc7eb16a0438b`
- `index.html`: `ae4ad511de53a25ee3bc8cc1bac3c7c4729104abb41d27660e6d67e15df61492`
- `styles.css`: `2718e165478ec51806827d62bc07f662bd3ffdfeead4d866b0de3d76501794c9`
- `app.js`: `14debe5439b72fbcaa005ed152beb2c2d1b23dad9c2f903c5df0651007bad76b`
- `test_background_progress.py`: `b2c8caa383b7ddec24bee7852b761498060101ea6b9d2fa3117b851ef4dafeb9`

## Scope

- In scope:
  - 独立复现三 facade 并发下每个 `unit_step` 真实只调用一次，不只数审计事件。
  - 确认后台工作与页面轮询解耦，刷新/重连只从 SQLite + `project_audience_progress` 重建视图。
  - 审查 HTTP 只返回受众白名单字段、静态界面不估算进度、失败/受阻不冒充完成。
  - 审视中文原生性、层级、信息密度、不溢出、进度条与数字一致，以及工程语言不外露。
- Out of scope:
  - 修改任何源码或测试；reviewer 只读并可运行 synthetic/offline 检查。
  - 产品源码、医学写作子系统、真实项目/provider/8911、真实临床结论。
  - 跨应用进程/设备重启的存活与跨进程作业 claim；本切片只声称单应用进程内的页面离开、刷新和 facade 重建。

## Success Criteria

- 首先核对六个冻结源/测试哈希；任一不符则 `STALE_INPUT`。
- 输出严格 `VERDICT: ACCEPT` 或 `VERDICT: VETO`，VETO 按 P0-P4 列精确位置、可达路径与最小修复。
- 独立运行聚焦测试，亲自使用计数 step 复现三 facade 并发且总调用数等于 8。
- 确认服务器只绑定 `127.0.0.1:0`、关闭后不可连接，8911 无监听。
- 检查三张截图，重点确认 100% 与总/阶段进度条一致、失败/受阻显示、无文本截断及无用户无关的工程语言。
- 明确列出未验证范围与残余风险；不将本切片写成 R1 总体或产品验收。

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 120 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. A catalog/auth/transport health preflight timeout or malformed response is diagnostic and must still allow one live route attempt; only a missing CLI or an explicitly invalid, retired, or unlisted model may block before live dispatch. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Reviewer 不得修改任何文件，不得启动 8911、不得读取五个真实项目或医学写作子系统。
- 如需 HTTP 复现，仅可用自动分配的临时回环端口，结束必须关闭。

## Loop Log

- 2026-08-10 02:37:21: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-10 02:46: Kimi/K3-256K first pass returned VETO on silent worker death and repeated real action after a terminal Store write failure.
- 2026-08-10 02:55: After the main venue repaired error continuation, stable idempotency-key propagation and fault coverage, the same reviewer session rechecked the new frozen snapshot and returned ACCEPT.
- 2026-08-10 03:07: Codex reran current core/adjacent suites and correctness/compile gates, confirmed browser evidence and closed listeners, and accepted only this bounded synthetic slice.
