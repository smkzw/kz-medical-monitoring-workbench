# Conference Context: medical_monitoring_r3_kernel_acceptance_20260810

Created: 2026-08-10 13:51:56
Objective: 独立工程与医学监查语义验收 R3 Study Intelligence 合成 POC 快照：严格复核来源权威、异构 listing 画像/mapping/身份、全量快照增量 diff、自然语言规则生命周期、反过拟合及中文原生边界；仅读、不做系统安全审计、不触碰医学写作/产品/真实项目、不启动 8911。
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Grok Build `grok-4.5`, then Cursor CLI `cursor-grok-4.5-high`, then Pi/OpenCode Go `gpt-5.6-luna` (max), then Pi/Kimi `k3-256k` (high).
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/Alibaba `qwen3.8-max` (xhigh) during the Beijing 22:00-07:00 window, and outside that window its exact Qwen Max node is replaced by Pi/cms-smk `cms-model` (high); its remaining fallbacks are Pi/cms-smk `cms-model` (high), Pi/cms-smk `deepseek-v4-flash` (max), Pi/OpenCode Go `deepseek-v4-flash` (max), and Pi/DeepSeek `deepseek-v4-flash` (max). Participant 2 is Grok Build `grok-4.5`, with Cursor CLI `cursor-grok-4.5-high` and Pi/cms-router `minimax-m3` as fallbacks. Codex remains the final authority. The explicit Luna native/CLI compatibility route remains available for execution roles that declare Codex subAgent.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`，重点 §§5-9、15-20。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`，重点 R3 与阶段完成门。
- `context/medical_monitoring_r3_study_intelligence_20260810_context.md` 与 `reviews/medical_monitoring_r3_external_solution_discovery_20260810.md`。
- 当前审阅对象：`poc/medical_monitoring_ai_native_r3/src/mm_r3/*.py` 与 `poc/medical_monitoring_ai_native_r3/tests/*.py`。
- 上游只读锚点：`poc/medical_monitoring_ai_native_r1/`、`poc/medical_monitoring_ai_native_r2/`；不得修改。
- 当前非 LLM 锚点：R3 `338 passed`；R3 Python 摘要 `6feb4fb77ce198baa67af383333fb52956f0d01eeec59af0daa90dfb597726ba`；R1 全树摘要 `ba6692f7252449beaca1817bad06629ce7acc846c75985fd143264faac023d87`；R2 Python 摘要 `69033e28616ca497579d7b3b9bbbd87ab8fc3031eb7d0259ba3954db1a338003`；8911 无监听者。
- 以上路径均位于授权的 workbench；真实项目、产品应用源码和医学写作子系统不在读取范围。

## Scope

- In scope：独立复核 R3-A 资料权威/冲突合同，R3-B listing 结构画像、mapping、稳定身份和规范化，R3-C 全量快照 diff、临床影响传播、规则草稿/模拟/版本化激活，以及三种合成结构、隐藏改名/重排/中文原生反过拟合用例。
- In scope：允许只读检查源码、设计、计划、R3 任务记录和测试；允许执行 R3 聚焦或全量 pytest、内存/语法检查、摘要核对和端口只读检查。
- Out of scope：任何文件修改、R4/R5 实现、真实项目、产品/前端/医学写作、真实医学结论、服务/8911、浏览器与 Patient Journey 视觉验收、额外系统安全设计或测试。

## Success Criteria

- 每个参与者给出 `ACCEPT`、`CONDITIONAL ACCEPT` 或 `REJECT`，并以文件定位、命令输出或可复现反例支持阻断项。
- 工程审阅证明或反驳：来源/项目/修订绑定，listing/mapping/identity/diff/rule 生命周期不允许不一致状态静默进入后续基线。
- 医学监查语义审阅证明或反驳：全量导出增量语义、记录消失/删除区分、规则作用范围、中文原生与反过拟合边界足以作为合成 R3 内核，而不冒充真实项目或 UI 完成。
- R3 全量测试通过、源码/测试无执行中漂移；R1/R2 摘要不变；无缓存残留；8911 仍停止。
- 参与者只读且不越界；Codex 根据独立报告和锚点拥有最终接受或返修决定。

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

## Loop Log

- 2026-08-10 13:51:56: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-10 13:58:00: Codex 完成中文原生表头/日期/性别/严重程度及 coverage-note 边界补强；R3 全量 `338 passed`，当前 Python 摘要与 R1/R2 锚点已写入来源包；进入独立只读审阅。
- 2026-08-10 14:15:00: Pi 完整工程审阅接受初始快照并复现 `_record_id` 进入 clinical payload 的低级假 diff；Grok 同一 session 经两次完成请求给出条件接受。Codex 采用 N-1 最小修复和回归测试；最新全量 `339 passed`。
- 2026-08-10 14:18:00: 同一 Pi session 对修复后快照独立复核：R3-C 聚焦 `104 passed`、全量 `339 passed`、R3 根目录摘要 `418b5aacef1e0be50f6d8992aa01c19a1eaaeb2008dc42da77e122e898f4120d` 首尾稳定、R1/R2 锚点稳定、无缓存、8911 停止，最终 ACCEPT。会商闭环。
