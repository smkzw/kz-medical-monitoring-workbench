# Conference Context: medical_monitoring_r4_d09_contract_20260814

Created: 2026-08-14 20:15:41
Objective: 冻结R4-D09中心重复模式与系统性风险的typed合同、分母与coverage门、cutoff/时间窗、分层与可比性、个体证据展开、owner/投影边界及挑战矩阵，保持8911停止且不触碰医学写作或真实项目
Task type: `high_risk_contradiction_review`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Grok Build `grok-4.6` (high), then the distinct Cursor `cursor-grok-4.6-high` route, then the distinct Pi/OpenCode Go `gpt-5.6-luna` (max) route. The Codex subAgent Luna route remains a separate native/CLI compatibility path.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/Alibaba `qwen3.8-max` (xhigh) -> Pi/OpenCode Go `deepseek-v4-flash` (max) during the Beijing 22:00-07:00 window; daytime is Pi/CMS-SMK `deepseek-v4-flash` (max) -> Pi/OpenCode Go `deepseek-v4-flash` (max). Participant 2 is Grok Build `grok-4.6` (high), with the distinct Cursor `cursor-grok-4.6-high` and Pi/cms-router `minimax-m3` as fallbacks. Codex remains the final authority. The explicit Luna native/CLI compatibility route remains available for execution roles that declare Codex subAgent.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`。
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` 中 D09 与共用合同。
- `context/medical_monitoring_r4_d09_external_pattern_decision_20260814.md`。
- 已接受 D01-D08 合同/接受记录仅用于 owner 与输入边界；不得反向改写其语义。
- 当前文件系统为最终真相；workbench 不是 Git 仓库，使用显式文件清单和 SHA-256 固化。

## Scope

- In scope：D09 中心模式的 typed input/output、unit identity/stable core、中心/受试者/风险/来源绑定、numerator/denominator/coverage/cutoff/分析窗/分层/可比性、五类 L1 disposition、反证与小样本门、增量 lineage、热点受试者/个体证据展开、中文中心解释与 Query 边界、D10/R5 投影边界、挑战矩阵与冻结证据要求。
- Out of scope：D09 runtime/实现、D10 项目聚合、R5/UI/Patient Journey 视觉实现、真实项目/患者数据/模型、8911/服务、产品源码、医学写作、安全设计/测试、中心综合评分/惩罚排名、监管或现场监查最终结论。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- 合同不得仅凭风险数为零生成中心 negative，不得以单个高风险个例证明系统性问题，也不得以中心平均值稀释个体高风险。
- 每个聚合量均可追溯到分子成员、分母构成、coverage、时间窗、版本与个体来源；重复 revision/导出/跨域同源不得多计。
- 小样本、短随访、暴露/病例组合/启动时间/数据版本不可比具有闭集 boundary/not_evaluable 语义；项目阈值由 versioned ModeContract 提供，公共合同不硬编码数值。
- D09 只消费 D01-D08 已接受个体结果并形成中心模式，不反向改写个体风险，不越权形成 D10 项目结论。

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

- 2026-08-14 20:15:41: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-14: Codex 将 generic context 替换为 D09 精确合同；完成 ICH E6(R3)、FDA 风险监查指南及中心统计监查方法的两遍核验，结论记录于 `context/medical_monitoring_r4_d09_external_pattern_decision_20260814.md`。
- 2026-08-14: Pi/CMS-SMK 与 Grok Build 在原会话内完成 v0.1-v0.3 多轮挑战；v0.3 两路均允许进入独立冻结 review。
- 2026-08-14: 独立 Codex Luna/max CLI compatibility session `01a0004e-3fb6-7b30-a552-95edd8d9932a` 对 v0.3、v0.4 返回 `REVISE_D09_CONTRACT`，推动 replay-stable R2 handoff、global/unit gate 分层、机会量/visibility/query/partition schema 闭合。
- 2026-08-14: v0.5 SHA `9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40` 获独立 `ACCEPT_D09_CONTRACT`；8911 停止。合同冻结，artifact/runtime 尚未开始。
