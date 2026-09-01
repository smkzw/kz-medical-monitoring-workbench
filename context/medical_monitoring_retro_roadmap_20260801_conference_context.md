# Conference Context: medical_monitoring_retro_roadmap_20260801

Created: 2026-08-01 20:30:52
Objective: 只读审查医学监查子系统需求、实现、测试、运行证据与中英文外部平台方法，形成需求-实现-证据差距矩阵、宏观及分阶段路线图、下一 Goal 文本和恢复 Prompt；不修改产品源码、不启动服务或真实项目。
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Cursor CLI `cursor-grok-4.5-high`, then Grok Build `grok-4.5`, then Kimi Code `k3-256k`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use Pi/Alibaba `qwen3.8-max-preview` (xhigh) as the sub-venue chair, leading Codex subAgent `gpt-5.6-luna` (max) and Pi/OpenCode Go `deepseek-v4-flash` (max). In Codex App, the Codex subAgent participant is dispatched natively through `multi_agent_v1` so the parent can see progress and reuse the same session. The OpenCode Go participant falls back first to Pi/DeepSeek V4 Flash max; the Codex participant fallback chain remains Kimi K3 high -> Pi/DeepSeek V4 Flash max -> CodeBuddy hy3 max. Chair fallback is Grok Build `grok-4.5`, then Cursor CLI `cursor-grok-4.5-high`.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- Current filesystem under this workbench is authoritative; prior memory is only a locator.
- Current bounded recovery anchor:
  - `context/monitoring_p10_v11_canary_pause_20260801.md`
  - `runs/execution/monitoring_p10_v11_isolated_canary_20260801/TERMINAL_EVIDENCE.md`
  - `runs/execution/monitoring_p10_v11_zero_submit_gate_20260801/ZERO_SUBMIT_EVIDENCE.md`
  - `reviews/codex_monitoring_p10_v11_isolated_canary_20260801_review.md`
  - `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`
- Product and planning authority:
  - `docs/medical_monitoring_manual/医学监查子系统说明书.md`
  - `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md`
  - `docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md`
  - `docs/medical_monitoring_manual/医学监查子系统_Goal模式启动Prompt.md`
  - `records/active_slices/medical_monitoring_goal_p10_20260730/REQUIREMENTS_TRACEABILITY.md`
  - `records/active_slices/medical_monitoring_goal_p10_20260730/TASK_CONTEXT.md`
- Implementation authority:
  - `services/api/app/`
  - `frontend/src/`
  - `tests/`
- External claims must be verified against current primary or official sources. Commercial platforms are comparative evidence only. Any executable component recommended for later adoption must have a verified open-source license compatible with intended use.

## Scope

- In scope:
  - Read-only requirement, architecture, code, test, runtime-evidence, and governance audit.
  - P0-P10 requirement-to-implementation-to-evidence traceability.
  - English and Chinese platform, standards, regulatory, and eligible open-source landscape.
  - Macro objective, phased objectives, step-level plan, entry/exit gates, dependencies, residual risks, next Goal text, and exact recovery prompt.
- Out of scope:
  - Product-source or runtime-library changes.
  - v12 implementation, provider calls, POST submissions, candidate actions, or attempts to salvage v9-v11.
  - Starting ports 8911 or 5174, touching unrelated port 18911, or running the three real projects.
  - Weakening identity/treatment boundaries, fail-closed behavior, source-first rules, or medical-writing isolation.
  - Claiming original deleted parent-thread restoration or release readiness without evidence.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- A file-level architecture review identifies concrete strengths, defects, coupling, test gaps, evidence gaps, and likely failure modes with locators.
- A P0-P10 matrix distinguishes implemented, partially implemented, evidence-only, stale, missing, and release-blocking states.
- External research separates regulatory/industry patterns, commercial platform patterns, and eligible open-source building blocks, with source quality and licensing stated.
- The roadmap contains an umbrella objective, bounded stages, step-level Done criteria, dependencies, stop/rollback rules, and the v12-first next safe action.
- The current Goal Prompt is critiqued against actual state and replaced by two copyable texts: next Goal objective and recovery prompt.
- Final durable output is limited to task records under `context/`, `plans/`, `reviews/`, `metrics/`, `runs/`, and `prompts/`; product source remains unchanged.

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
- Keep ports 8911 and 5174 stopped. Do not touch unrelated port 18911.
- Freeze v9, v10, and v11 evidence. Do not retry, reuse, salvage, reclassify, or execute any v11 candidate action.
- The next implementation action may only be proposed here: a separate offline v12 corrective that returns exact field path plus matched boundary token to provider repair and relies on provider regeneration, never post-processing deletion.
- Treat the v11 terminal result as `failed / invalid_ai_output / retryable=0` with zero persisted candidates; it is evidence of correct fail-closed behavior and incomplete controlled repair, not a validator defect.
- Do not modify or overwrite unrelated user changes. Do not run tests or services in this audit; use existing deterministic and runtime evidence and report anything not freshly rerun.

## Loop Log

- 2026-08-01 20:30:52: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-01: Context completed for a read-only retrospective and roadmap; current v11 pause is the recovery boundary.
