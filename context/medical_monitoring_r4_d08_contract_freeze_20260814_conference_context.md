# Conference Context: medical_monitoring_r4_d08_contract_freeze_20260814

Created: 2026-08-14 15:32:14
Objective: 对D08 v0.6同一不可变catalog/oracle/registry/generator/test快照执行只读独立冻结验收，决定ACCEPT_D08_CONTRACT或REVISE_D08_CONTRACT
Task type: `high_risk_contradiction_review`
Risk: `high`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Grok Build `grok-4.6` (high), then the distinct Cursor `cursor-grok-4.6-high` route, then the distinct Pi/OpenCode Go `gpt-5.6-luna` (max) route. The Codex subAgent Luna route remains a separate native/CLI compatibility path.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/Alibaba `qwen3.8-max` (xhigh) -> Pi/OpenCode Go `deepseek-v4-flash` (max) during the Beijing 22:00-07:00 window; daytime is Pi/CMS-SMK `deepseek-v4-flash` (max) -> Pi/OpenCode Go `deepseek-v4-flash` (max). Participant 2 is Grok Build `grok-4.6` (high), with the distinct Cursor `cursor-grok-4.6-high` and Pi/cms-router `minimax-m3` as fallbacks. Codex remains the final authority. The explicit Luna native/CLI compatibility route remains available for execution roles that declare Codex subAgent.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- D08 v0.6 contract and its exact hash-pinned catalog, independent oracle,
  registry, generator and focused test named in the verifier prompt.
- D08 artifact-build acceptance record is limited authorization, not final
  contract acceptance.
- D07 erratum record is adjacency authority for the accepted current D07
  oracle hashes; the stale root-test constant is not allowed to redefine that
  accepted state.
- Current filesystem and independently reproduced command output are the final
  source of truth.

## Scope

- In scope: read-only adversarial review of the same immutable D08 v0.6
  artifact snapshot; exact hashes, oracle independence, semantic completeness,
  anti-overfit, deterministic replay, negative mutations, and 8911 stopped.
- Out of scope: any runtime/product/UI/security implementation, real project or
  patient data, service startup, and the medical-writing subsystem.

## Success Criteria

- A fresh-context independent verifier returns exactly
  `ACCEPT_D08_CONTRACT` or `REVISE_D08_CONTRACT` with reproducible evidence.
- The verifier re-computes start/end hashes, runs the focused deterministic
  checks, challenges cases 179/198 and the decisive semantic matrices, and
  proves the generator cannot author expected outcomes.
- No in-scope file drifts during verification; 8911 remains stopped.
- Codex reviews the verdict and records the final freeze decision. Runtime is
  not unlocked unless the verdict is `ACCEPT_D08_CONTRACT` and parent checks
  remain green.

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

- 2026-08-14 15:32:14: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-14 15:33:00: Native fresh-context spawn explicitly rejected
  `gpt-5.6-luna` (available picker routes were Sol/Terra). Per current global
  AGENTS, selected `cli_compatibility_fallback` with the ChatGPT-bundled Codex
  CLI, preserving Luna/max, read-only workspace and the 120-minute hard wait;
  no model substitution is permitted.
- 2026-08-14 15:35:00: First CLI launch was immediately interrupted before
  usable output because prompt preflight had failed (missing the guard's exact
  closed-read/output section syntax). No verifier report was produced. The
  prompt was corrected and must pass preflight before the sole real route
  attempt.
