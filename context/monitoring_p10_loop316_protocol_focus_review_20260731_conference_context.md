# Conference Context: monitoring_p10_loop316_protocol_focus_review_20260731

Created: 2026-07-31 22:07:59
Objective: 独立审查P10方案结构证据聚焦与50条输出预算实现，确认未放宽医学门、未破坏冻结输入身份，并识别真实RUX受控重试前的阻断缺陷。
Task type: `high_risk_contradiction_review`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Cursor CLI `cursor-grok-4.5-high`, then Grok Build `grok-4.5`, then Kimi Code `k3-256k`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use Pi/Alibaba `qwen3.8-max-preview` (xhigh) as the sub-venue chair, leading Codex subAgent `gpt-5.6-luna` (max) and Pi/DeepSeek `deepseek-v4-flash` (max). In Codex App, the Codex subAgent participant is dispatched natively through `multi_agent_v1` so the parent can see progress and reuse the same session. The Codex participant fallback chain is Kimi K3 high -> Pi/DeepSeek V4 Flash max -> CodeBuddy hy3 max. Chair fallback is Grok Build `grok-4.5`, then Cursor CLI `cursor-grok-4.5-high`.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `context/monitoring_p10_loop316_protocol_focus_20260731_context.md`
- `context/monitoring_p10_loop316_v16_protocol_pause_20260731.md`
- `runs/pi_monitoring_p10_loop316_protocol_focus_20260731.md`
- `services/api/app/monitoring_ai_source_packet.py`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_source_packet.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`
- Codex-observed verification:
  - focused three-file regression: `186 passed in 6.27s`
  - full monitoring regression: `1142 passed, 4291 deselected, 27 warnings`
  - current implementation hashes:
    - `monitoring_ai_source_packet.py`: `ee685ed8c83615c22c3d7df284627246a3f972bc2a5bf53d1832a98b7777a681`
    - `monitoring_ai_service.py`: `be7019dbb6d719c61fd29bdd24e754022b3e80e8c073417db9a4d26635252f53`
- Codex read-only projection against the six frozen RUX inputs:
  - visit: 200 -> 91 spans; serialized payload ratio 0.516
  - study treatment: 200 -> 139; ratio 0.729
  - safety: 200 -> 148; ratio 0.763
  - efficacy: 95 -> 68; ratio 0.750
  - early withdrawal/deviation: 169 -> 70; ratio 0.467
  - data quality: 53 -> 33; ratio 0.668
- Codex read-only satisfiability/closure audit after participant completion:
  - detected conflicts: visit `1 x 3 IDs`; study treatment `1 x 3 IDs`;
    safety/efficacy/early-withdrawal/data-quality `0`; therefore the reported
    large-conflict/50-ID interaction is not a blocker for these six RUX retries.
  - every primary table root in all six focused packets retained its available
    same-row cells and table headers (`bad_table_roots=0`).
  - current list-role metadata has overlapping parent sets and some primary
    `list_item` roles without an exact-equal title parent set; this reflects the
    pre-existing heuristic grouping. It does not prove loss of all titles/items in the
    focused packet, but it means exact per-list-group closure is not yet established by
    the current tests or validator and must be weighed explicitly by the chair.
- The 10 existing protocol candidates remain `proposed/pending_user_confirmation`;
  no candidate decision, fact adoption, rule activation, or mapping activation occurred.

## Scope

- In scope:
  - Read-only adversarial review of the provider-facing focus algorithm, 50-ID
    candidate budget, repair contract, frozen-input identity, and v2 fail-closed gates.
  - Identify release-blocking defects before a single controlled retry of the six
    failed RUX protocol topics.
  - Distinguish blocking defects, follow-up improvements, and acceptable residual risk.
- Out of scope:
  - Editing source/tests, changing runtime databases, starting/stopping services,
    calling the real product provider, retrying jobs, medical candidate decisions,
    facts/rules/mappings activation, frontend work, or medical-writing files.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- Each participant explicitly checks:
  1. whether a selected structure can be orphaned after focus;
  2. whether mandatory bundles/conflicts can make the 50-ID contract impossible;
  3. whether provider focus preserves persisted input identity and validation authority;
  4. whether the repair envelope still duplicates avoidable material;
  5. whether current tests prove the real failure modes rather than only synthetic shapes.
- Chair provides a clear `block / accept with conditions / accept` recommendation for
  the single RUX retry, with evidence locators.

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
- Conference is strictly read-only. Do not edit any source, test, context, runtime, or
  report path; return findings to the runner.

## Loop Log

- 2026-07-31 22:07:59: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-31 22:12 CST: Codex added the verified source packet, regression counts,
  frozen-input projections, and explicit adversarial questions.
- 2026-07-31 22:31 CST: After both participants completed, Codex added the real
  conflict-size and table-closure audit so the chair can resolve conditional findings
  against the six actual frozen RUX inputs.
