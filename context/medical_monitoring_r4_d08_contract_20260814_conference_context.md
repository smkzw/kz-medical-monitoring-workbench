# Conference Context: medical_monitoring_r4_d08_contract_20260814

Created: 2026-08-14 12:28:04
Objective: 冻结 R4-D08 多表医学逻辑与数据质量 synthetic/offline 合同，覆盖跨域身份、时间精度、关系完整性、双向孤立、修改传播、Query 与 Journey 高亮，并经独立反证审阅后才允许实现
Task type: `high_risk_contradiction_review`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Grok Build `grok-4.6` (high), then the distinct Cursor `cursor-grok-4.6-high` route, then the distinct Pi/OpenCode Go `gpt-5.6-luna` (max) route. The Codex subAgent Luna route remains a separate native/CLI compatibility path.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/Alibaba `qwen3.8-max` (xhigh) -> Pi/OpenCode Go `deepseek-v4-flash` (max) during the Beijing 22:00-07:00 window; daytime is Pi/CMS-SMK `deepseek-v4-flash` (max) -> Pi/OpenCode Go `deepseek-v4-flash` (max). Participant 2 is Grok Build `grok-4.6` (high), with the distinct Cursor `cursor-grok-4.6-high` and Pi/cms-router `minimax-m3` as fallbacks. Codex remains the final authority. The explicit Luna native/CLI compatibility route remains available for execution roles that declare Codex subAgent.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_5_20260814.md` is the current revised draft under review, never authority over frozen upstream contracts. v0.2-v0.4 were superseded before freeze.
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` and `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` define D08 scope/order.
- Accepted D01-D07 contracts and their public identity/coverage/Query/Journey contracts are upstream read-only constraints; D08 may not recompute their owned medical semantics.
- CDISC SDTM relationship semantics, OpenLineage column lineage and Great Expectations cross-table integrity are method references only; no external runtime is adopted.

## Scope

- In scope: independent clinical/engineering contradiction review of the D08 v0.5 contract; relationship-unit denominator, evaluation/public identity, temporal precision, cutoff/cardinality, bidirectional orphan checks, correction propagation, fail-closed coverage, Query and Journey projection; exact remediation proposals.
- Out of scope: editing the draft, implementation, services/8911, real projects/data/providers, D09-D10 aggregation, R5 UI, product source, medical writing and system-security work.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- Each participant returns `ACCEPT_D08_DRAFT_FOR_FREEZE` or `REVISE_D08_DRAFT`, with reproducible contradictions and exact contract changes. No implementation is authorized by this conference pass.

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

- 2026-08-14 12:28:04: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-14: Both independent participants returned `REVISE_D08_DRAFT`. Codex accepted the shared restrictive decisions: D08 owns graph/integrity/identity/lineage only; explicit RELID is one unit, non-explicit missing links use obligation-side slots; mixed data/rule change splits into separate propagation units; hidden treatment nodes are omitted from audience projection. Draft v0.2 closes the reported owner, grain, cardinality, raw/materialized, identity/hash, propagation, coverage, visibility and anti-overfit gaps. Same-session round 2 is pending.
- 2026-08-14: Same-session round 2 again returned `REVISE_D08_DRAFT`. Codex retained the accepted owner/grain boundaries and produced v0.3 with only residual pins: cutoff admission, temporal-result disposition table, upstream L1 inheritance, eight-dimension Evaluation unit plus separate stable/public identities, covered-zero versus uncovered resolve, closed cardinality/propagation/claim-token vocabularies, N-ary RELID single-unit semantics, hidden-obligation projection, exact fixture/registry/ref fields. Same-session round 3 must decide only whether semantic drafting may proceed to freeze-artifact construction; it cannot issue full contract/runtime acceptance.
- 2026-08-14: Round 3 closed NEW-01…NEW-05 but found cutoff/not-found precedence and adjacent interface ambiguity. Pi's first round-3 output truncated at provider limit; an allowed compact same-session recovery returned the actionable residuals. Codex produced v0.4: typed cutoff decisions and four oracle outcomes, clinical event-time versus revision-time separation, closed-empty waiver handoff, internal join versus audience redaction, obligation-side fanout identity, and possible-relation-set temporal comparison. Round 4 is limited to artifact-build permission; full contract/runtime acceptance remains blocked.
- 2026-08-14: Round 4 returned one artifact-build accept and one revise. Codex accepted the two reproducible divergences and converted the accepting report's generator conventions into contract fields. v0.5 fixes time-missing precedence over cutoff boundary, directional allowed temporal relations, exact waiver three-state schema, fanout gate grain, and accepted stable-node correction across cutoff retaining propagation. Round 5 is the final narrow draft gate before any freeze-artifact construction.
- 2026-08-14: Same-session round 5 returned two `ACCEPT_D08_DRAFT_FOR_FREEZE_ARTIFACT_BUILD` verdicts. Codex bound the exact v0.5 file/semantic hash in `context/medical_monitoring_r4_d08_draft_artifact_build_acceptance_record_20260814.md`. Only catalog/oracle/registry/generator construction is unlocked; `ACCEPT_D08_CONTRACT`, runtime, D09/D10, R5 UI, real data and 8911 remain blocked.
