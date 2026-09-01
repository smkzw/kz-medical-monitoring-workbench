# Conference Context: mm_r8_gate3_notification_contract_review_20260831

Created: 2026-08-31 12:44:49 CST
Objective: 独立审阅 R8 G3 离页通知决策合同 v0.1：逐项挑战 Path A/B 语义、三元身份、终态保留、幂等、权限降级、点击无启动副作用、中文可行动文案及 G4/G5/G6 边界；只读 synthetic/offline 合同，不运行服务/浏览器/模型/真实项目。
Task type: `stage_review_plan`
Risk: `medium`
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
  - This packet uses one Codex-led conference object (`general_single_object`) with no sub-venue chair. Its effective `CST` route chain is `cms-router/minimax-m3:xhigh -> google-antigravity/gemini-3.7-flash:high -> opencode-go/muse-spark-1.2-contributor:xhigh -> openai-codex/gpt-5.6-luna:max`; the packet branch is recorded at creation and filtered against the actual execution route nodes recorded below. Before a new session, the runner rechecks the Beijing period; an already-started session is never rerouted.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r8_gate3_notification_contract_review_20260831`
- Execution evidence status: `no linked execution packet`
- Excluded provider/model nodes: none
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_r8_gate0_source_admission_anti_overfit_contract_v0_1_20260831.md` §§3.3、8.2、9：上游终态、Path A/B 与 Gate 顺序的权威定义。
- `context/medical_monitoring_r8_gate2_synthetic_runtime_acceptance_record_20260831.md`：G2 接受边界与明确未接受项。
- `reviews/medical_monitoring_r8_gate3_notification_decision_contract_v0_3_20260831.md`：依两轮审阅纠偏后的当前待审合同草案。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R7 步骤3 及顶部 R8 恢复锚点。
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` §§15.1–15.4。
- 当前 UI 只作为缺口证据：`frontend/src/App.jsx:1446`、`frontend/src/features/medical-monitoring/r7/MedicalMonitoringR7ProgressPanel.jsx:116`。

## Scope

- In scope: 只读挑战合同选路、语义完整性、身份/终态/幂等/权限/导航不变量、中文用户表达、失败关闭、G4/G5/G6 边界和可执行的修订建议。
- Out of scope: 编辑任何文件；启动服务、端口、浏览器或产品模型；访问真实项目；修改医学写作；评判医学准确性；声称真实送达、产品或 §15.4 完成。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- 逐项给出 P0–P4 可定位发现，并明确 `ACCEPT_G3_CONTRACT | REVISE_G3_CONTRACT | BLOCK_G3_CONTRACT`。
- 若认为 Path A 选择或应用内持久降级语义有误，必须直接引用 G0 §8.2 文本，不自行重定义 Path B。
- 检查是否原样保留 `partial/final_partial/truncated/failed/timed_out/cancelled/interrupted/blocked`，以及 `analysis_complete` 的“结果可访问”额外门。
- 检查点击、重放、降级、权限拒绝及通道失败是否可能创建新运行、改写终态或伪造用户已看到。

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
- 不得将会商输出直接写入待审合同；只返回审阅报告，由 Codex 决定是否修订。
- 不使用真实项目/药物/疾病/量表/列名作为例子；不把通知合同扩展为系统安全专项。

## Loop Log

- 2026-08-31 12:44:49 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-31: Codex 在 dispatch 前补齐权威源、范围、成功标准和风险边界；由于 G6 前禁止产品浏览器工作，且当前无可用 `codex-with-chatgpt` 本地 skill 文件，本次不启动 ChatGPT Web advisory，直接使用 guard 声明的可执行会商路由。
- 2026-08-31: 首轮 `Pi/cms-router/minimax-m3:xhigh` 无 fallback 返回 `REVISE_G3_CONTRACT`。Codex 接受 Path A 原文、双通道一致、终态/可访问双门、导航绑定、投递证据、§15.4 清单和 G6 binding 纠偏；拒绝无依据的签名系统、任意 100 次门槛与删除历史通知建议，形成 v0.2 并待同 session 复审。
- 2026-08-31: 同 session 第二轮确认 v0.2 的 P1 已全部关闭，仅保留“撤销/重新准入后禁止新通知事实”一项 P2。Codex 补齐该阻断、取消/中断说明入口、非终态必测清单和统一未登记项目文案，形成 v0.3 并待同 session 终审。
