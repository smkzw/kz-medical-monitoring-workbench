# Conference Context: mm_r7_slice07c3_publication_contract_20260829

Created: 2026-08-29 03:16:07 CST
Objective: 独立审阅并纠偏 R7 Slice-07C-3 synthetic/offline ResultPublication 合同：原子发布、R6 receipts 门禁、现有 R5 S4 builder 与产品 R5AuthorityPacket 的唯一复用路径、progress 发布状态、result-entry 四元组/站点覆盖、幂等冲突和可恢复失败；不修改源码。
Task type: `code_open_audit`
Risk: `high`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
- This packet uses one Codex-led conference object (`general_single_object`) with no sub-venue chair. Its effective `CST` route chain is `codebuddy-cli/deepseek-v4-flash:max -> codebuddy-cli/glm-5.3-flash:max -> grok-build/grok-4.6:medium -> cursor/cursor-grok-4.6:medium -> openai-codex/gpt-5.6-luna:max`; it is resolved once at packet creation and filtered against the actual execution route nodes recorded below before dispatch.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice07c3_publication_contract_20260829`
- Execution evidence status: `no linked execution packet`
- Excluded provider/model nodes: none
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_r7_slice07c_three_mode_product_loop_contract_v0_2_20260829.md`
- `reviews/medical_monitoring_r7_slice07c3_result_publication_contract_v0_1_20260829.md`
- `context/medical_monitoring_r7_slice07c2_prepare_start_acceptance_record_20260829.md`
- Current R7 runtime/launch/receipt source and tests.
- Accepted R5 S4 builder/validator and product `R5AuthorityPacket` source/tests.

## Scope

- In scope: contract-level publication identity, transaction, receipt/R5 gate,
  progress/history/result-entry and failure/recovery semantics.
- Out of scope: source implementation, UI/ego, services, real projects/models,
  medical-writing and security design/testing.

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

- 2026-08-29 03:16:07 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-29: Round 1 要求完整 R5 bridge、双 manifest、原子 publication 与精确公开边界。
- 2026-08-29: Round 2 关闭原 8 项并提出 2×P1 + 5×P2；Codex 全部最小修订。
- 2026-08-29: Round 3 同 session 返回 `ACCEPT`；最终 manifest fingerprint 措辞补齐后冻结。
