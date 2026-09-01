# Conference Context: medical_monitoring_r1_framework_persistence_adr_20260809

Created: 2026-08-09 17:02:10
Objective: 基于 R1 已验收的框架中立 SQLite 领域内核、双候选框架 spike 和 audience-facing AE/MH 纵切，独立挑战并收口主图引擎、持久化、Temporal 延后、回滚和后续验证门的 ADR；不得修改产品、医学写作、真实项目、服务或运行库
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Grok Build `grok-4.5`, then Cursor CLI `cursor-grok-4.5-high`, then Pi/OpenCode Go `gpt-5.6-luna` (max), then Pi/Kimi `k3-256k` (high).
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/Alibaba `qwen3.8-max` (xhigh) during the Beijing 22:00-07:00 window, and outside that window its exact Qwen Max node is replaced by Pi/cms-smk `cms-model` (high); its remaining fallbacks are Pi/cms-smk `cms-model` (high), Pi/cms-smk `deepseek-v4-flash` (max), Pi/OpenCode Go `deepseek-v4-flash` (max), and Pi/DeepSeek `deepseek-v4-flash` (max). Participant 2 is Grok Build `grok-4.5`, with Cursor CLI `cursor-grok-4.5-high` and Pi/cms-router `minimax-m3` as fallbacks. Codex remains the final authority. The explicit Luna native/CLI compatibility route remains available for execution roles that declare Codex subAgent.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `poc/medical_monitoring_ai_native_r1/docs/ADR-001-framework-neutral-sqlite.md`
- `poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/docs/DEPENDENCY_DECISION.md`
- `poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/docs/SPIKE_EVIDENCE.md`
- `context/medical_monitoring_ai_native_r1_slice2_framework_spike_20260809_execution_context.md`
- `reviews/codex_execution_medical_monitoring_ai_native_r1_slice2_framework_spike_20260809_review.md`
- `metrics/medical_monitoring_ai_native_r1_slice2_framework_spike_20260809_execution_metrics.md`
- `poc/medical_monitoring_ai_native_r1/slices/aemh_audience_workbench/docs/SLICE3_EVIDENCE.md`
- `reviews/codex_execution_medical_monitoring_ai_native_r1_slice3_aemh_audience_workbench_20260809_review.md`
- Candidate adapter source/tests under
  `poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/` may be read
  when needed to verify an evidence claim.
- The 2026-08-09 dependency record already contains a same-day bounded scan of
  official documentation, wheel licenses/hashes and security minimums. Reuse
  it while assumptions remain unchanged; reopen official primary sources only
  if a material discrepancy is found.
- No production, medical-writing, real-project, service, shared-runtime or user
  configuration path is in the read or write set.

## Scope

- In scope: independently challenge and recommend the R1 graph-control and
  persistence disposition; compare the framework-neutral custom Graph IR,
  LangGraph 1.2.10, Agent Framework Core 1.13.0 and deferred Temporal 1.31.0;
  specify authority boundaries, checkpoint semantics, rollback, packaging and
  explicit reopen/stop gates; identify which R1 requirements remain unproved.
- In scope: decide whether LangGraph should become only a provisional primary
  orchestration adapter for the next isolated validation, while SQLite domain
  state and content-addressed artifacts remain authoritative and framework
  neutral.
- Out of scope: implementation edits, dependency installation, starting
  services, product adoption, production migration, medical-writing changes,
  real clinical projects, credentials, live providers, or claiming R1/R2
  completion.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- Each participant gives an explicit disposition for: framework-neutral core,
  LangGraph, Agent Framework, Temporal, and the R1-completion claim.
- Recommendations distinguish observed evidence, inference, residual risk and
  future validation gates, and include a reversible rollback route.
- The final ADR can be implemented as an isolated next-stage decision without
  letting any framework session/checkpoint become medical/domain authority.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 120 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Read-only conference: participants must not edit any workspace artifact.
- Historical failures repaired by the manager remain part of the decision
  record; do not erase them or relabel the spike as production durability.
- The accepted Agent Framework checkpoint-after-domain-commit residual must be
  treated as controlled-synthetic evidence only.

## Loop Log

- 2026-08-09 17:02:10: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-09 17:03: prompts completed and both guard preflights passed after
  replacing the generated absolute workspace wording with the current-workspace
  boundary.
- 2026-08-09 17:04: declared Pi and Grok routes launched once in parallel.
- Pi route: Beijing policy rewrote the declared Qwen node to `cms-smk/cms-model`;
  that node and every declared Pi fallback failed provider/model health before
  a resumable session existed. No report was accepted and no undeclared route
  was invented.
- Grok route: session `2dc54980-0b8e-49ca-a732-59996f62ed9b` returned only a
  170-byte progress sentence on its first pass. Codex classified this as an
  actionable incomplete-output gap and sent one same-session round-2 completion
  prompt. The resumed session returned a complete 24,174-byte independent
  report with terminal `end_turn` and no fallback.
- Codex disposition: affirm framework-neutral domain authority; accept
  LangGraph only as the next isolated validation's preferred orchestration
  adapter; retain Agent Framework as a reference with its residual; defer
  Temporal; reject R1-complete.
- Artifacts written:
  `poc/medical_monitoring_ai_native_r1/docs/ADR-002-provisional-langgraph-orchestration-adapter.md`
  and `poc/medical_monitoring_ai_native_r1/docs/R1_ADAPTER_FAILURE_MATRIX.md`.
- Deterministic checks: current Slice1 `103 passed in 0.70s`; document table and
  referenced-file checks passed; SHA-256 values recorded in the review.
