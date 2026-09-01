# Conference Context: mm_r7_slice_04_progress_contract_20260828

Created: 2026-08-28 08:13:37
Objective: 独立挑战并冻结 R7 Slice-04 持久化 Run 进度事实面合同，重点核查产品 Run 与 R1 manifest/work-unit ledger 的身份映射、显式创建与零写入边界、revision 幂等、中文受众投影和后续后台恢复可演进性；不得修改源码、启动服务、调用模型或运行真实项目。
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair. The effective visual participant chain is ``; it is filtered against the actual execution route nodes recorded below before dispatch.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex, logic-heavy, evidence-sensitive, artifact-heavy, code-review, and high-risk contradiction work uses a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/google-antigravity `gemini-3.7-flash` (high) -> Pi/OpenCode Go `muse-spark-1.2-contributor` (high) -> Kimi Code `k3-256k` (medium) -> Codex subAgent `gpt-5.6-luna` (max). Participant 2 is Grok Build `grok-4.6` (medium) -> Pi/Cursor `cursor-grok-4.6` (medium) -> Pi/cms-router `minimax-m3` (high). Codex remains the final authority.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice_04_progress_contract_20260828`
- Execution evidence status: `no linked execution packet`
- Excluded provider/model nodes: none
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `context/medical_monitoring_r7_slice_04_durable_run_progress_contract_20260828.md`
- `context/medical_monitoring_r7_phase_review_and_slice04_plan_20260828.md`
- `context/medical_monitoring_r7_slice_03_product_mount_acceptance_record_20260828.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`（R7）
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`（第 12 节）
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/audience_progress.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/background_progress.py`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/api.py`（隔离 API，仅作边界对照）
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/run_entry.py`
- `services/api/app/medical_monitoring_r7_product_router.py`
- 只读当前工作台文件；不得读取真实临床项目或医学写作子系统。

## Scope

- In scope: 挑战合同是否能以最少新增代码复用 R1 权威事实源；核查 canonical 项目/产品 Run/
  R1 Run 映射、显式 prepare、零写入 GET、manifest revision、幂等、对账失败关闭、中文输出及
  Slice-05 可演进性；给出可直接修订的合同条款和验收用例。
- Out of scope: 修改任何源码；启动 8911/5174；后台线程或执行；真实模型、真实项目、前端、
  浏览器、Patient Journey、受试者流向看板、医学写作和系统安全功能。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- 两席独立识别高影响缺口，给出具体修订；Codex 能据此形成无歧义的 frozen contract。
- 合同明确 runtime 路径、产品/R1 Run 映射、manifest 构造来源、同内容重放与内容变化语义、
  旧 revision 回调、中文投影字段和本切停止线。
- 不修改源码、不启动服务、不调用模型、不运行真实项目；Codex 保留最终接受权。

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

- 2026-08-28 08:13:37: Conference initialized by `hermes_workflow_guard.py init-conference`.
