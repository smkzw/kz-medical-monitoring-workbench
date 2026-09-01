# Conference Context: mm_r8_gate0_contract_review_20260831

Created: 2026-08-31 11:22:34 CST
Objective: 对医学监查 R8-0 联合准入合同 v0.1 做 fresh-context 独立挑战：检查真实资料解锁顺序、来源零写入、输出隔离、独立 harness/LLM 责任、防硬编码与过拟合、真实应用/通知/§15.4、full/incremental、P0-P4 缺陷传播及 clean-streak reset。不得读取真实项目路径、不得运行真实模型/服务/浏览器、不得修改产品源码；输出可定位 P0-P4 发现和最小修订，不能声称最终接受。
Task type: `stage_review_plan`
Risk: `high`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.


## Preferred Browser Advisory Chair

- Role: `chatgpt-web-pro-advisory` via `codex-with-chatgpt`.
- Assignment: preferred stage-level retrospective and phase-planning adviser.
- UI selection: `Pro` / `GPT-5.6 Sol`; the visible UI state must be positively verified.
- Boundary: read-only C2C advisory chair, not a runner subprocess or executable participant. Reuse the same session, perform 20-30 second foreground DOM checks, and persist `c2c session` / `c2c record` state. A browser timeout is pending, not failure; there is no automatic callback.
- Codex remains the formal packet chair and final authority. If the advisory response is unavailable or invalid, continue the declared executable panel.


## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
  - This packet uses one Codex-led conference object (`general_single_object`) with no sub-venue chair. Its effective `CST` route chain is `cms-router/minimax-m3:xhigh -> google-antigravity/gemini-3.7-flash:high -> opencode-go/muse-spark-1.2-contributor:xhigh`; the packet branch is recorded at creation and filtered against the actual execution route nodes recorded below. Before a new session, the runner rechecks the Beijing period; an already-started session is never rerouted.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r8_gate0_contract_draft_20260831`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `openai-codex/gpt-5.6-luna`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_r8_gate0_source_admission_anti_overfit_contract_v0_1_20260831.md`（被审对象，SHA-256 候选 `a19fd612c758f38107c937c93f44f1d693e3a68f6bea3f4200ee212d8a95158b`）
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `context/medical_monitoring_r7_phase_acceptance_record_20260831.md`
- `reviews/codex_execution_mm_r8_gate0_contract_draft_20260831_review.md`
- 三份 `runs/execution/mm_r8_gate0_contract_draft_20260831/worker_0*.md` 仅作起草来源追溯；不得把其自述当成合同接受证据。
- 五个真实项目根是禁止访问的生产型来源；不得列举、`stat`、读取、哈希、搜索或打开。

## Scope

- In scope：逐条挑战联合合同是否可执行、可失败、不可提前解锁；给出 P0-P4、定位、影响和最小修订；核对 G0-G15、状态语义、零写入、输出隔离、harness responsibility、anti-overfit、通知、§15.4、full/incremental、双角色双轮与 clean-streak。
- Out of scope：修改文件、实现产品、读取真实项目、调用任何真实模型/harness、启动服务或浏览器、外部研究、视觉验收、医学结论、最终接受。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- 每个发现必须给出合同章节、可复现失败路径、严重度、最小修订和修订后的确定性验收信号。
- 明确区分“合同可接受”“synthetic readiness”“逐项目来源准入”“真实模型运行”“真实应用/浏览器/§15.4”五种不同声明。
- 不新增与风险无关的框架、平台或未来商业化要求。

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

- 2026-08-31 11:22:34 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-31 11:22 CST: `codex-with-chatgpt` skill 入口缺失；Oracle dry-run 仅解析为浏览器 advisory，未启动浏览器。因本任务硬边界禁止浏览器，按 fallback contract 继续 declared executable panel。
