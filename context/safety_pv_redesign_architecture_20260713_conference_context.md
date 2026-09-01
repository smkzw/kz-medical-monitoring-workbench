# Conference Context: safety_pv_redesign_architecture_20260713

Created: 2026-07-13 07:33:37
Objective: 复核Safety/PV A方案、统一项目医学风险核查工作台、共享底层与四类PV文件医学审阅交互，形成Product Design Brief决策依据，不执行生产修改
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no Hermes sub-venue chair: Hermes `aishuo / MiniMax-M3`, Hermes `buddy / kimi-k2.7-code`, and Hermes OpenCode Go `qwen3.7-plus`.
- Chinese labels or Chinese sentence review uses a single Hermes `buddy / deepseek-v4-pro` gate and does not start a conference.
- Other complex tasks use Hermes `buddy / glm-5.2` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3`, Hermes `buddy / deepseek-v4-pro`, and Hermes OpenCode Go `mimo-v2.5`.
- This conference route does not invoke Reasonix for a high-risk second review.
- Every conference role is dispatched through a three-round same-session loop: independent pass, skeptical challenge, and corrected final pass. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- User definition and current design gate: `records/active_slices/safety_pv_redesign_20260713/DISCOVERY_RECORD.md`.
- Shared ownership and acceptance proposal: `records/active_slices/safety_pv_redesign_20260713/SHARED_CONTRACT_AND_ACCEPTANCE_DESIGN.md`.
- Legacy A/B/C impact analysis: `records/active_slices/safety_pv_redesign_20260713/LEGACY_INTERFACE_MIGRATION_IMPACT.md`.
- External and local baseline: `records/research/safety_pv_dual_project_20260713/EXTERNAL_AND_LOCAL_BASELINE.md`.
- Current contracts and services listed explicitly in participant prompts.
- The user selected A after participant dispatch: retire the legacy Safety/PV business UI and preserve necessary history read-only. The user also added a dedicated full “安全性风险预警” entry inside medical monitoring, similar in workflow depth to `ae-risk-assessment`; Safety/PV links to this monitoring-owned workspace rather than owning an expert risk page.
- The user then broadened the monitoring entry beyond Safety/PV: it must be a project medical-risk review workbench combining subject/site/trial-level Patient Profile, Subject Timeline, AE/MH underreporting, PD underreporting, prohibited/restricted medication and study-drug compliance, protocol visit/time-window violations, data-logic checks, CFDI pre-inspection self-check relevance, incremental monitoring revisions and cross-view interaction. Safety/PV is only an extra tag/collaboration destination for relevant risks.

## Scope

- In scope: critique the two-entry architecture, unique source-of-truth boundaries, comprehensive monitoring-owned medical-risk review workbench, medical-manager workflow, four PV document review families, dynamic source-request interaction, AI/user revision loop, Option A migration, and multi-real-project acceptance strategy.
- Out of scope: production edits, final visual design, browser acceptance, formal PV decisions/reporting, security scanning, choosing A/B/C for the user, or broadening into a full PV case/signal-management system.

## Success Criteria

- Identify any duplicated business object, state machine, parser, editor, audit store or approval path.
- Produce a concrete end-to-end interaction for safety-focused Timeline/Profile reuse and PV draft medical review.
- Keep DSUR, SAE report, CTD 2.7.4 and ISS distinct while maximizing shared infrastructure.
- Validate Option A and specify how the monitoring-owned project medical-risk workbench differs from a retained Safety/PV expert page while supporting optional Safety/PV tagging and handoff.
- Define evidence and tests needed for RUX-03-002 and MY009, including source replacement, stale state, CAS, override and independent-AI traceability.
- Return corrections and unresolved questions suitable for a Product Design Brief Gate; do not claim implementation approval.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- CM means non-investigational concomitant medication. Investigational product administration and dose adjustment must remain separate.
- Safety/PV must reference monitoring Timeline/Profile and risk objects rather than copying them.
- PV document review must reuse the medical-writing collaboration kernel rather than create a second editor.
- Files receive technical/content/role/project/version validation with warned expert override; heavy security scanning is excluded.
- AI produces traceable candidates pending medical approval and never a formal PV or regulatory conclusion.

## Loop Log

- 2026-07-13 07:33:37: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-13: Codex populated source, scope, success and boundary controls; role-specific prompts separate workflow/UX, Chinese PV/regulatory logic, and architecture/migration review.
- 2026-07-13: Buddy DeepSeek returned only round 1 and failed with `no usable Hermes session was established`; Codex preserved that artifact and activated OpenCode Go `qwen3.7-plus` as a different-provider fallback for the same Chinese/PV role.
- 2026-07-13: User approved Option A and added a dedicated monitoring-owned safety risk warning entry modeled on the depth of `ae-risk-assessment`. Chair synthesis must incorporate this later decision and treat earlier A/B/C comparisons as historical decision support only.
- 2026-07-13: Buddy GLM-5.2 chair returned only round 1 and failed with `no usable Hermes session was established`; Codex preserved the artifact and activated OpenCode Go `qwen3.7-plus` as a different-provider fallback chair.
- 2026-07-13: User broadened the new monitoring entry from safety-only warning to a unified project medical-risk review workbench with trial/site/subject rollups, CFDI-oriented logic, PD/protocol/medication/data checks, incremental updates and cross-view overlays. This latest boundary supersedes safety-only naming.
- 2026-07-13: Qwen fallback chair completed three rounds but returned a patch/diff with omitted sections rather than a complete auditable package. Codex marked it unusable for review-gate purposes and activated OpenCode Go `mimo-v2.5` as the final different-session chair fallback with the latest unified draft and commercial research in its read list.
