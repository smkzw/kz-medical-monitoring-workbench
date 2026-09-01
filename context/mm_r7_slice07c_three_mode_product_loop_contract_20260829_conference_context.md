# Conference Context: mm_r7_slice07c_three_mode_product_loop_contract_20260829

Created: 2026-08-29 00:41:03 CST
Objective: 独立审阅 R7 Slice-07C 三模式产品闭环合同，挑战日常全量/增量、锁库前修订复核、核查前固定总量、特殊风险规则、后台长任务、结果发布与 R5 看板/Patient Journey 身份边界；仅评审合成范围合同，不改源码、不运行真实项目。
Task type: `stage_review_plan`
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

- Linked execution task: `mm_r7_slice07c_three_mode_product_loop_contract_20260829`
- Execution evidence status: `no linked execution packet`
- Excluded provider/model nodes: none
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_r7_slice07c_three_mode_product_loop_contract_v0_1_20260829.md`
- `reviews/medical_monitoring_r7_slice07c_three_mode_product_loop_contract_v0_2_20260829.md`（冲突时优先）
- `reviews/medical_monitoring_r7_slice_07a_progress_ui_contract_v1_20260828.md`
- `reviews/medical_monitoring_r7_slice07b_subject_flow_dashboard_contract_v0_2_20260828.md`
- `reviews/medical_monitoring_r7_slice07b_subject_flow_dashboard_contract_v0_3_20260828.md`
- `context/medical_monitoring_r7_slice07b_subject_flow_acceptance_record_20260829.md`
- `context/medical_monitoring_r7_slice_02_product_api_run_entry_contract_20260828.md`
- `context/medical_monitoring_r7_slice_04_durable_run_progress_contract_20260828.md`
- `context/medical_monitoring_r6_runtime_slice_07_agent_harness_contract_20260828.md`

## Scope

- In scope: three-mode run setup, full/incremental semantics, versioned natural-language risk rules,
  background long-run behavior, atomic result publication, progress/result navigation, center coverage and
  R5 Patient Journey identity.
- Out of scope: source edits, service/browser execution, real projects, medical-writing files, security design,
  real clinical correctness and final acceptance.

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

- 2026-08-29 00:41:03 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-29 CST: Round 1 returned `revise` with A–J findings. Codex accepted the material findings and wrote
  v0.2 corrective clauses: bounded monitor start authority; full-current plus keyed-diff incremental inputs;
  template/work-unit identity; traceable Query attribution; new-run fixed-total semantics; project-level versioned
  risk rules; atomic ResultPublication with progress extension; site coverage; idempotency/timeout recovery; and
  a four-step implementation sequence.
- 2026-08-29 CST: Same-session Round 2 returned `ACCEPT` with one baseline-rule ambiguity. Codex added the
  same-mode + published-only baseline rule, prohibited post-lock snapshots as cross-mode baselines, fixed the
  full-run comparison field boundary, retained administrator-only waiting-start recovery, and recorded low-level
  prepare/public-token/publication-state/S4-builder implementation constraints. v0.2 is frozen.
