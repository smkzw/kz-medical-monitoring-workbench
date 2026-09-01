# Conference Context: medical_monitoring_r5_stage_20260818

Created: 2026-08-18 11:28:00
Objective: 按 System Design v1.1 与 R0-R8 计划冻结并连续实施 R5 风险驾驶舱、中心图谱与 Subject Workspace/Patient Journey，保护医学写作，先合同后最小纵切，最终以真实浏览器和资深医学监察员任务验收
Task type: `visual_report_structure`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Grok Build `grok-4.6` (high), then the distinct Cursor `cursor-grok-4.6-high` route, then the distinct Pi/OpenCode Go `gpt-5.6-luna` (max) route, then Codex subAgent Luna (max). The Codex subAgent route remains a separate native/CLI compatibility path.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex, logic-heavy, evidence-sensitive, artifact-heavy, and high-risk contradiction work uses a Codex-chaired panel with no sub-venue chair. Participant 1 is night Pi/Alibaba `qwen3.8-max` (xhigh) -> Codex subAgent `gpt-5.6-luna` (max), and day Pi/CMS-SMK `deepseek-v4-flash` (max) -> Pi/OpenCode Go `gpt-5.6-luna` (max) -> Kimi Code `k3-256k` (high). Participant 2 is Grok Build `grok-4.6` (high), with the distinct Cursor `cursor-grok-4.6-high` and Pi/cms-router `minimax-m3` as fallbacks. Codex remains the final authority.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

1. `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`，特别是第 10–12 节。
2. `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` 的 R5 步骤与完成证据。
3. `context/medical_monitoring_r4_stage_closure_acceptance_record_20260818.md` 及 R4 当前稳定 projection/contracts。
4. `reviews/medical_monitoring_patient_journey_research_20260809.md`、R1 Patient Journey Slice 4 与既有浏览器证据。
5. `frontend/AGENTS.md` 的 Subject Timeline、Patient Profile、desktop-first 与中文业务命名合同。
6. 当前 `frontend/src/features/medical-monitoring`、相关 API 只读合同、实际渲染和浏览器行为。
7. 当前文件系统和实时验证优先于历史摘要；外部研究仅复用已经核实且假设未变化的 Patient Journey 决策。

## Scope

- In scope：项目风险驾驶舱、中心风险图谱、Risk Inspector、统一 Subject Workspace、受试者医学旅程/指标趋势/事件明细、共享时间轴、风险/来源深链、返回上下文、数据口径与 desktop-first 视觉系统。
- In scope：先以 synthetic/offline/current accepted projection 建立可测试的用户面纵切，再做真实浏览器功能/视觉验收；需要时最小接入产品医学监查路由。
- Out of scope：医学写作任何源码/状态、真实五项目医学结论、生产部署、商业化、安全专项设计/测试、任务化待办/强制人工复核、Query 外发/关闭工作流。
- 8911 在合同冻结与离线组件实现期间保持停止；仅在进入明确的真实浏览器验收步骤时临时启动并在验收后停止。

## Success Criteria

- R5 合同明确资深医学监察员首屏问题、最短下钻路径、信息层级、空/缺失/不可评估语义和禁用术语。
- 项目/中心/受试者聚合值可由 R4 authority 重建，分子、分母、cutoff、coverage 和隐藏成员不被混算。
- Journey/Profile/Timeline 共用 spine、视窗、访视/日期/研究日、选择和风险锚点；身份不一致 fail-closed。
- 所有中高风险优先可见；AE/MH/CM/IP/检验检查/住院操作/症状疗效/方案符合性及风险类型不只靠颜色区分。
- 项目/中心风险到正确 Subject Workspace 最多一次下钻，再一次操作到原始来源；返回恢复筛选、排序、滚动与选择。
- 组件/合同测试、相邻回归、构建、真实桌面浏览器任务、截图与独立视觉/医学审阅通过；8911 验收后停止。
- 外部模型只提供隔离建议或实施 handoff，Codex 检查实际文件、测试和渲染后才接受。

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

- 2026-08-18 11:28:00: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-18 11:35: R4 closing record/review/metrics completed and guard review gate passed; remediation sessions archived recoverably.
- 2026-08-18 11:40: Re-anchored System Design, R5 plan, Patient Journey research, product/frontend contracts and current medical-monitoring implementation. Product Design context preflight found no saved external context; current workspace and accepted MG-K10/R1 visual contracts remain the design source.
- 2026-08-18: R5 S0 contract frozen at SHA `763747a...`; normal/optimized verifier, compile and focused Ruff passed; 204 specifications remain future-stage executable obligations rather than false S0 behavior claims.
- 2026-08-18: Fresh isolated stage reviewer returned `ACCEPT_R5_CONTRACT` after stable seven-SHA replay. Acceptance only unlocks S1; 8911 remains stopped.

## LOOP

- Objective：形成可独立验收的 R5 合同并连续交付第一条 audience-facing 纵切。
- Hypothesis：R4 已提供足够权威投影；主要风险是把旧碎片页面机械拼接、聚合口径漂移或让内部术语压过医学任务。
- Action：现状审计 → R5 合同/挑战矩阵 → 独立 stage review → 最小纵切 → 聚焦/相邻/构建 → 浏览器与医学任务验收。
- Observation：合同可重建性、单跳定位率、共享时间轴一致性、任务点击数、渲染截图和独立 findings。
- Decision：先接受合同再写产品 UI；任何身份/聚合/时间轴 P0–P4 退回最小传播路径修复。
- Record：本文件、主计划、R5 contract/review/metrics、浏览器证据与最终 acceptance record。
