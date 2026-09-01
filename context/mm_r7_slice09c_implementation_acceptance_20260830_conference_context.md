# Conference Context: mm_r7_slice09c_implementation_acceptance_20260830

Created: 2026-08-30 22:49:31 CST
Objective: 独立审阅 R7 Slice-09C 实现是否逐项满足冻结合同 v0.2。必须直接重开合同、执行审计、源代码与 synthetic/offline tests，重点挑战：根级 append-only 审计链与 operation 同事务、R1 公共 verifier 复用、startup/open/same-key 三入口统一恢复、09A/09B 恢复状态与 rollback 证据、最小中文 DTO、两进程技术日志并发/轮转、故障注入、确定性与相邻回归。按 P0-P4 输出 ISSUES_ONLY/EVIDENCE_LOCATORS/NO_ISSUE_SCOPE/RECOMMENDED_REPAIR/RESIDUAL_RISK；测试计数不能替代源码和合同核对。不得改文件、启动服务/模型/浏览器、运行真实项目或触碰医学写作。
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

- Linked execution task: `mm_r7_slice09c_implementation_20260830`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `openai-codex/gpt-5.6-luna`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_r7_slice09c_business_audit_log_rotation_contract_v0_2_20260830.md`
- `reviews/codex_execution_mm_r7_slice09c_implementation_20260830_review.md`
- `context/mm_r7_slice09c_implementation_acceptance_round2_remediation_20260830.md`
- 当前 `poc/medical_monitoring_ai_native_r7/src/mm_r7/`、对应 tests 与产品 router。

## Scope

- In scope: 09C synthetic/offline 审计、核验、恢复接线、日志、故障与确定性。
- Out of scope: 真实项目/模型、浏览器视觉、性能 09D、产品发布、安全专项、医学写作。

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

- 2026-08-30 22:49:31 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-30: round 1 completed；发现 P1×1、P2×3、P3×3、P4×2。
- 2026-08-30: Codex 完成有界修复、聚焦/确定性/相邻回归并记录两项解释。
- 2026-08-30: same-session round 2 completed，`P0=P1=P2=P3=P4=0`；无 fallback。
