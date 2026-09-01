# Conference Context: mm_r7_slice08c4_visual_contract_20260830

Created: 2026-08-30 01:09:03 CST
Objective: 独立只读挑战并验收R7 Slice-08C-4 ego(lite)三视口运行时与视觉专项合同；核对用户任务、参考图并列比较、overlay/push、真实焦点、数据对账、中文视觉质量、全部P0-P4清零和隔离运行边界，关闭P0-P2后才允许启动隔离服务
Task type: `visual_report_structure`
Risk: `medium`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
  - This packet uses one Codex-led conference object (`visual_single_object`) with no sub-venue chair. Its effective `CST` route chain is `grok-build/grok-4.6:high -> cursor/cursor-grok-4.6:high -> codebuddy-cli/glm-5.3-flash:max -> openai-codex/gpt-5.6-terra:medium`; the packet branch is recorded at creation and filtered against the actual execution route nodes recorded below. Before a new session, the runner rechecks the Beijing period; an already-started session is never rerouted.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice08c4_visual_contract_20260830`
- Execution evidence status: `no linked execution packet`
- Excluded provider/model nodes: none
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `context/medical_monitoring_r7_slice08c4_ego_visual_acceptance_contract_20260830.md`（待冻结对象）
- `reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_1_20260829.md` §9–14
- `reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_2_20260829.md` §19–20
- `context/medical_monitoring_r7_slice08c3_implementation_acceptance_record_20260830.md`
- `context/medical_monitoring_subject_flow_dashboard_requirement_20260828.md`
- 用户上传流向参考：`/var/folders/yb/31r9763x6_54mdxswxk36c4w0000gn/T/codex-clipboard-07757ff8-29c4-4136-a9fa-17bbbc40d16b.png`（只参考信息结构）
- 既有 R5/07C-4 三视口产品截图路径由待冻结合同 §3.1 声明。
- W3C APG dialog/keyboard guidance 与 McKinsey Design System functional palette 链接仅为外部方法依据。
- 当前文件系统为最终真相；不得以旧截图或 Agent 自述代替当前运行证据。

## Scope

- In scope: 只读挑战合同是否足以驱动 1280/1440/1920 ego(lite) 真实用户任务、参考+产品并列图、全页/局部溢出、overlay/push、真实焦点/滚动锁/归还、reduced-motion、中文视觉细节、对比度、事件/风险行集、九项计数、来源返回与全部 P0-P4 清零；提出 P0-P4 和可执行修订。
- Out of scope: 不修改合同或产品源码；不启动服务、浏览器、真实项目或模型；不进行实际视觉接受；不触碰医学写作；不接受 R7 总体、生产或商业化。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- P0-P2 必须关闭后合同才可冻结并启动隔离服务；最终 visual execution 的接受标准必须是开放 P0-P4=0。

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

- 2026-08-30 01:09:03 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
