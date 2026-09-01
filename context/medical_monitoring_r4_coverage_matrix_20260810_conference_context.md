# Conference Context: medical_monitoring_r4_coverage_matrix_20260810

Created: 2026-08-10 20:24:31
Objective: 以新上下文独立反证 R4 全风险域 coverage matrix 与共同风险合同，核查医学语义、覆盖完整性、与 Design v1.1/R4 计划及冻结 R1-R3 合同的一致性，输出可执行 VETO 或 ACCEPT
Task type: `high_risk_contradiction_review`
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

- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` — artifact under review.
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` sections 9-11 — approved design authority.
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R4 — approved implementation authority.
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py` and `poc/medical_monitoring_ai_native_r1/tests/test_ae_mh_vertical_slice.py` — frozen R1 vertical-slice evidence, read-only.
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py` and relevant focused tests — frozen lifecycle/adjudication evidence, read-only.
- `poc/medical_monitoring_ai_native_r3/**` and `poc/medical_monitoring_ai_native_r3_rule_ai/**` — frozen rule/knowledge contracts, read-only only when needed.
- `context/monitoring_p7d_real_evidence_matrix_20260729.md` — historical gap/control evidence, not current real-project acceptance.
- Official primary-source links embedded in the artifact under review.

## Scope

- In scope: fresh-context contradiction review of medical semantics, coverage-state semantics, denominator/time/identity logic, false-positive/false-negative protections, lifecycle/adjudication compatibility, user-facing projections and implementability of the proposed R4 first slice.
- In scope: return exact P0-P4 findings with file section/line locators, why each matters, and the smallest coherent remediation; finish with `VERDICT: ACCEPT` or `VERDICT: VETO` for freezing this matrix.
- Out of scope: editing any artifact, designing system security, product/runtime integration, real projects, model/provider execution for medical analysis, and port 8911.

## Success Criteria

- Each available participant returns an auditable, independent artifact review or an explicit route/fallback reason.
- Every material objection is tied to an exact contract statement and classified P0-P4; recommendations distinguish required freeze blockers from later implementation advice.
- The panel explicitly checks: AE/MH boundary semantics; severity/seriousness/monitoring priority; L0 execution coverage, five exclusive L1 dispositions, L1b evidence polarity and L3 lifecycle separation; candidate/source-record/risk/Query separation; R2 lifecycle/adjudication compatibility; domain completeness; Profile/Timeline/Journey and aggregation projections; first-slice testability.
- The panel does not demand true project evidence, product/security scope, or R5/R7 work as a precondition for this isolated R4 contract.
- No reviewed file is modified; Codex independently verifies accepted findings and retains final acceptance.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 120 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. A catalog/auth/transport health preflight timeout or malformed response is diagnostic and must still allow one live route attempt; only a missing CLI or an explicitly invalid, retired, or unlisted model may block before live dispatch. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Read only the declared workbench source packet and directly relevant frozen contracts; do not inspect real project folders or the medical-writing subsystem.
- Do not run services, tests against real projects, or any listener; do not modify files.
- Do not treat official standards as imposing one universal project-specific rule where protocol configuration is required.

## Loop Log

- 2026-08-10 20:24:31: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-10: Codex populated the source packet, bounded independent reviewer roles and freeze verdict criteria.
