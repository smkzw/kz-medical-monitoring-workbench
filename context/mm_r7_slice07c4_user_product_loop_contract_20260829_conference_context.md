# Conference Context: mm_r7_slice07c4_user_product_loop_contract_20260829

Created: 2026-08-29 06:13:21 CST
Objective: 独立审查 R7 Slice-07C-4 中文产品闭环合同：重点挑战公开结果上下文桥、四步向导、历史/主动作、离页恢复、结果看板与 Patient Journey 同身份贯通、中文/桌面视觉验收；只读，不修改产品源码。
Task type: `visual_report_structure`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
- This packet uses one Codex-led conference object (`visual_single_object`) with no sub-venue chair. Its effective `CST` route chain is `grok-build/grok-4.6:high -> cursor/cursor-grok-4.6:high -> codebuddy-cli/glm-5.3-flash:max`; it is resolved once at packet creation and filtered against the actual execution route nodes recorded below before dispatch.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice07c4_user_product_loop_contract_20260829`
- Execution evidence status: `no linked execution packet`
- Excluded provider/model nodes: none
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_r7_slice07c4_user_product_loop_contract_v0_1_20260829.md`
- `reviews/medical_monitoring_r7_slice07c4_user_product_loop_contract_v0_2_20260829.md`
- `reviews/medical_monitoring_r7_slice07c_three_mode_product_loop_contract_v0_1_20260829.md`
- `reviews/medical_monitoring_r7_slice07c_three_mode_product_loop_contract_v0_2_20260829.md`
- `context/medical_monitoring_r7_slice07c3_result_publication_acceptance_record_20260829.md`
- `frontend/AGENTS.md`、现有 R5 页面/adapter/route state、07A progress 组件。
- R7 product router 的 options/rules/prepare/history/progress/result-entry 与相关测试。

## Scope

- In scope: 合同完整性、用户任务/中文/信息层级、公开结果上下文身份桥、失败关闭、复用边界、桌面
  多视口与 ego(lite) 验收矩阵。
- Out of scope: 产品源码修改、真实项目或模型、8911、医学质量结论、医学写作、安全功能、R7/R8 总体接受。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- 独立 reviewer 明确给出 ACCEPT/REVISE，并逐项指出 P0-P4、可执行修订与是否允许冻结实施。
- 合同不得留下公开 token 到内部 R5 authority 的未闭合身份路径，也不得允许静态 fixture 充当已发布结果。

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

- 2026-08-29 06:13:21 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-29: Round 1 returned `REVISE`; Codex accepted the public-result identity, three-mode vocabulary,
  next-run action, history DTO and chrome-density findings.
- 2026-08-29: v0.2 appendix added persisted result-context lookup, public-token progress, three public R5 projection
  GETs/public envelope, one-in-flight rule, revised work-bar matrix, eight-field history and nonduplicative page chrome.
  Round 2 must review v0.1 + v0.2 together and decide whether the combined contract can freeze.
- 2026-08-29: Same session continued through targeted Round 3/4. Final pass verified the last token immutability,
  selected-run, launch-registry allowlist and five P1 edits, then returned `ACCEPT` with no fallback.
