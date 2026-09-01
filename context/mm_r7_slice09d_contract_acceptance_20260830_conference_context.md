# Conference Context: mm_r7_slice09d_contract_acceptance_20260830

Created: 2026-08-30 23:57:07 CST
Objective: 独立审阅 R7 Slice-09D 性能、容量与长任务恢复合同 v0.1。逐项挑战 corpus 分级与成本、process-cold/warm 和采样统计、correctness-first 停止、故障/恢复状态、中文用户投影、反过拟合、独立 harness/LLM 责任和 R8 source-admission。按 P0-P4 输出可定位问题；测试计数不能替代合同完整性。不得改文件、启动服务/模型/浏览器、读取真实项目或触碰医学写作/安全专项。
Task type: `complex_delivery_conference`
Risk: `medium`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
  - This packet uses one Codex-led conference object (`general_single_object`) with no sub-venue chair. Its effective `CST` route chain is `codebuddy-cli/deepseek-v4-flash:max -> codebuddy-cli/glm-5.3-flash:max -> grok-build/grok-4.6:medium -> cursor/cursor-grok-4.6:medium`; the packet branch is recorded at creation and filtered against the actual execution route nodes recorded below. Before a new session, the runner rechecks the Beijing period; an already-started session is never rerouted.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice09d_contract_20260830`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `openai-codex/gpt-5.6-luna`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_r7_slice09d_capacity_performance_recovery_contract_v0_1_20260830.md`
- `reviews/medical_monitoring_r7_slice09d_capacity_performance_recovery_contract_v0_2_20260831.md`
- `context/medical_monitoring_r7_phase_review_after_slice09c_and_slice09d_plan_20260830.md`
- linked execution review、metrics 与三份 runner outputs。

## Scope

- In scope: 09D synthetic/offline 合同的可执行性、成本、统计、恢复、中文投影、反过拟合与证据门。
- Out of scope: 实现、真实项目/模型、浏览器、服务、安全专项、医学写作与 R8 运行。

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

- 2026-08-30 23:57:07 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-31: round 1 completed，发现 P0×2、P1×6、P2×7 及 P3/P4 清晰度缺口。
- 2026-08-31: Codex 形成 v0.2，明确 30-cell 基准包、15 格确定性、预算/资源阈值、聚合裁决、中文投影、证据准入和条款门；安全/权限设计继续排除。
- 2026-08-31: round 2 closed all P0-P2；剩余 P3×2/P4×3。Codex 补 profile calibration watchdog、三类中文状态、progress-gap、完整 fault 属性与 bundle-run 进程粒度，进入同 session round 3。
- 2026-08-31: round 3 closed all P0-P3；剩余 calibration 粒度/失败语义 P4×2。Codex 明确按 workload 校准、校准失败直接 cell red，并补 workload→cell 聚合规则，进入同 session final check。
