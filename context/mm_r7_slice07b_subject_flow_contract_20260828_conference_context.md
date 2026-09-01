# Conference Context: mm_r7_slice07b_subject_flow_contract_20260828

Created: 2026-08-28 23:07:59 CST
Objective: 独立审阅 R7 Slice-07B 项目/中心受试者阶段流向看板合同。重点挑战阶段权威、路径守恒、四向对账、宽屏交互、中文体验、旧数据和 Journey 上下文；不得修改产品代码、启动服务或运行真实项目。
Task type: `visual_delivery_conference`
Risk: `high`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
- This packet uses one Codex-led conference object (`visual_single_object`) with no sub-venue chair. Its effective `CST` route chain is `grok-build/grok-4.6:high -> cursor/cursor-grok-4.6:high -> codebuddy-cli/glm-5.3-flash:max`; it is resolved once at packet creation and filtered against the actual execution route nodes recorded below before dispatch.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice07b_subject_flow_contract_20260828`
- Execution evidence status: `no linked execution packet`
- Excluded provider/model nodes: none
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_r7_slice07b_subject_flow_dashboard_contract_v0_2_20260828.md`
- `reviews/medical_monitoring_r7_slice07b_subject_flow_dashboard_contract_v0_3_20260828.md`（冲突时优先）
- `context/medical_monitoring_subject_flow_dashboard_requirement_20260828.md`
- `context/medical_monitoring_r7_slice07a_review_and_slice07b_plan_20260828.md`
- 当前 R5 authority、adapter、route 与默认页源码。
- Do not add production paths unless the user explicitly authorized reading them for this task.

## Scope

- In scope: 只读审阅阶段权威、路径守恒、四向对账、项目/中心身份、宽屏/键盘/中文体验、旧包兼容和 Journey 上下文。
- Out of scope: 产品代码修改、服务、真实项目、真实医学正确性、Patient Journey 重构、安全功能、R7/R8 接受。

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

- 2026-08-28 23:07:59 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-28 23:12 CST: 路由清单刷新为当前夜间 fallback `glm-5.3-flash`；既有 primary session 结果保留。三轮同 session 审阅后 v0.3 §9 已写入，合同对象 accept_limited。
