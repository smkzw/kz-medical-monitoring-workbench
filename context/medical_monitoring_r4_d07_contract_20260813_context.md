# Task Context: medical_monitoring_r4_d07_contract_20260813

Created: 2026-08-13 19:23:25
Objective: Freeze the synthetic/offline R4-D07 clinical safety, laboratory and examination monitoring contract, coverage matrix and validation plan before implementation, while preserving medical-writing, product/services, real projects and port 8911
Task type: `high_risk_contradiction_review`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`.
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`, R4 step 6 and current recovery point.
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`, especially D07 and shared L0/L1/L2/L3, Query, lifecycle and Journey contracts.
- Accepted synthetic/offline D01-D06 contracts and public R1-R3 APIs; consume them read-only and do not weaken or fork their authority.
- Current filesystem is authoritative. Workbench root is not a Git repository, so use explicit hashes and file/test evidence.
- External primary sources: ICH E2A, E3, E19; NCI CTCAE official resources; FDA DILI and ICH E14 guidance pages; NMPA DMC guidance and CDE clinical-trial safety reporting guidance. External sources inform the generic contract but never override the active project protocol/IB/RSI/central-lab rule within its claim scope.

## Scope

- In scope: a versioned synthetic/offline D07 clinical safety, laboratory, vital-sign, ECG, physical-examination, imaging and other safety-examination contract; source authority, typed objects, unit/range/baseline/grade/trend rules, AE/CM/IP/action handoffs, five L1 dispositions, priority, Query, renderer-neutral Journey projection, lifecycle and an executable challenge plan.
- Out of scope: D07 runtime code before contract acceptance; project-specific hard-coded tests/thresholds; formal AE/SAE/AESI/DILI/QT diagnosis or regulatory reporting; D08 cross-domain causal adjudication; D09/D10 center/project aggregation; R5 UI; real projects/data/providers; product/services/8911; medical-writing; system security design/testing.

## Success Criteria

- Every decision is reproducible from accepted typed inputs, versioned rules and source locators; models cannot invent units, ranges, grades, thresholds, baseline, clinical significance or medical action.
- Normal/range, CTCAE grade, seriousness, clinical significance and monitoring priority remain separate dimensions.
- New abnormality, baseline-abnormal worsening, persistence/recurrence, missing repeat/action/explanation, CS/NCS contradiction and AE/CM/IP/action linkage are explicitly covered without turning every abnormal result into an AE.
- Protocol/IB/product-specific DILI, QT and other organ-risk rules are versioned rule packages rather than universal literals in the shared kernel.
- D07 has a unique owner boundary and only emits stable subject-level results for D08/D10; no duplicated risks/Queries or project aggregation.
- Synthetic challenge plan includes five dispositions, hidden false negatives, NCS/baseline/sample-quality false positives, unit/range/version/date/identity failures, incremental close/reopen, Query and Journey/source-jump cases.
- Independent clinical/engineering contradiction review accepts the immutable contract snapshot with no P0-P4 before implementation starts.

## Risk Boundaries

- Allowed writes: this task context, D07 contract/research/review/prompt/run/metrics artifacts under this workbench only.
- Do not write D07 runtime/source/tests before contract acceptance.
- Preserve D01-D06, R1-R3, product and medical-writing files; do not start services or port 8911; do not read or run real projects.
- Do not interpret the user's exclusion of system security work as exclusion of the clinical safety monitoring domain explicitly required by R4-D07.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, or malformed probe output must be recorded and followed by one real route attempt. Only a missing executable or explicit invalid/retired/unlisted model may stop before that attempt.

## Loop Log

- 2026-08-13 19:23:25: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-13: Codex inspected the accepted D01-D06 sequence and common R4 coverage contract, and ran a bounded primary-source scan of ICH E2A/E3/E19, NCI CTCAE, FDA DILI/E14 and Chinese NMPA/CDE safety-monitoring sources. No D07 runtime code or real project was touched; 8911 remained stopped.
- 2026-08-13: Independent Luna verifier session `019ffae1-ee77-7070-8043-0bb7c22c5fe2` returned `REVISE` on contract v0.1 (`e842b0ac...`): six P1 and three P2 gaps in typed ownership, scope/authority/correction/hash, coverage/D05 gates, validation artifacts, orthogonal outputs/lifecycle, closed medical schemas and Journey provenance. Report: `runs/codex-subagent_medical_monitoring_r4_d07_contract_20260813.md` (`2db6442a...`).
- 2026-08-13: Codex revised the contract to v0.2 without starting runtime work. The revision adds typed owner/query/handoff routing, producer-consumer bindings, per-record scope/time/authority/correction objects, exact-key canonical hashing, stable identity, materialized coverage/domain-completion and D05 gates, closed grade/CS-NCS/follow-up/priority schemas, split action obligations, R2 lifecycle binding, typed Journey/source jumps/Chinese validation, and immutable validation-artifact/anti-self-proof requirements.
- 2026-08-13: Focused self-review then closed four residual gaps before same-session verifier follow-up: orthogonal assessment references in handoffs/projections, typed organ-pattern and examination-context assessments, typed D07 Query with accepted D04 PD-context gating, and Journey seriousness/priority bindings. Next safe action is to hash v0.2 and request a targeted follow-up in the same verifier session; contract freeze and runtime implementation remain prohibited until independent acceptance and executable validation artifacts exist.
- 2026-08-13: Same-session Luna follow-up 1 (`runs/codex-subagent_medical_monitoring_r4_d07_contract_20260813_followup1.md`, `34b81fc1...`) returned `REVISE`. The remaining set was six precision gaps: transitive scope/identity/cutoff, exact coverage reconciliation and D05 gate behavior, exact validation-artifact/DSL/integrity schemas, conditional medical schemas, typed action-obligation identity, and executable Journey/audience/source-jump validation.
- 2026-08-13: Codex revised the contract to v0.3. It adds per-record scope decisions and full tuple equality, timezone/cutoff rules, stable source-event identity and algorithm version; exact coverage equations, applicability evidence and a gate-blocked control-plane object; conditional range/conversion/grade/predicate/baseline/trend/organ/examination rules; content-addressed action-obligation definitions/bindings; typed PD wording permission; audience lexicon/payload/source-jump validation; and exact artifact key sets, semantic/content hashes, registry bijections, closed DSL, expected leaves, integrity stage/error taxonomy and oracle independence. Next safe action is another targeted review in the same Luna session; no runtime or validation artifact generation is authorized before semantic acceptance.
- 2026-08-13: Same-session Luna follow-up 2 (`runs/codex-subagent_medical_monitoring_r4_d07_contract_20260813_followup2.md`, `46426a85...`) returned `REVISE`, while accepting coverage/D05, validation-artifact independence and action-obligation identity. Three residual precision issues remained: source-revision/cutoff propagation, closed predicate/trend semantics, and shared-spine/one-to-many source-jump consistency.
- 2026-08-13: Codex revised the contract to v0.4 with explicit source-revision equality across scope/unit/result/pattern, a D05-bound cutoff decision and inclusive interval truth table, closed predicate and trend enums/truth rules, complete shared-spine scope equality, and conditional single/ordered-many target-ref source-jump schemas. Next safe action remains a targeted same-session semantic review; no runtime or validation artifact generation has started.
- 2026-08-13: Luna same-session follow-up 3 accepted v0.4 semantic contract. The artifact execution loop then closed schema integration, applicability/D05-gate coverage, case-017, trace/source value-level references and wrong-run mutation. Fresh Luna artifact session `019ffb6f-02a8-7ee3-86ef-b1790585f6e5` returned `REVISE`, then accepted the repaired snapshot in the same session as `ACCEPT_D07_ARTIFACT_FREEZE`; focused `125 passed`, reference/determinism checks passed, 8911 remained stopped. Authoritative record: `context/medical_monitoring_r4_d07_artifact_freeze_acceptance_record_20260813.md`. Next safe action is synthetic/offline D07 runtime implementation.
