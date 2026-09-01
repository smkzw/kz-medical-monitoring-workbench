# Task Context: medical_monitoring_r4_d03_ip_contract_20260811

Created: 2026-08-11 17:42:10
Objective: 冻结并实现 R4-D03 研究药暴露、依从性与医学处置关系的合成离线纵切，复用已接受公共合同并保持 8911 停止
Task type: `long_horizon_code`
Risk: `high`
Selected agent route: `cms-smk` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`, especially common contracts and R4-D03.
- `reviews/medical_monitoring_r4_d02_cm_slice_contract_v1_20260811.md` as the accepted adjacent-domain contract pattern, not as D03 clinical truth.
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/` and `poc/medical_monitoring_ai_native_r4/tests/` as current implementation truth.
- Current D02 Gate 5 acceptance record: `reviews/codex_conference_medical_monitoring_r4_d02_cm_acceptance_20260811_review.md`.
- No real-project data is a source for this slice. No new executable dependency or framework is being selected; the current frozen architecture and common contracts remain applicable, so a new external landscape scan is not decision-changing for this bounded slice.

## Scope

- In scope: freeze the D03 input, episode, identity, coverage, disposition, priority, Query, lifecycle, journey-projection and challenge-matrix contract; implement only a synthetic/offline vertical slice after Codex accepts that contract.
- In scope: planned-versus-actual exposure, treatment-role/stage mismatch, calculable adherence with explicit versioned numerator/denominator, protocol-allowed dose interruption/reduction/resumption/stop, and source-linked AE/lab/exam/efficacy action relationships.
- In scope: Chinese-native audience labels such as “研究药给药与方案不一致”“依从性待核实”“给药处置与医学事件不一致”; event types and risk types remain distinct in the journey projection.
- Out of scope: real projects, live models/providers, product services, R5 UI, formal PD reporting, safety/security design or testing, production writes, and any medical-writing subsystem file.

## Success Criteria

- A frozen D03 contract names authoritative inputs, fail-closed boundaries, L1 positive/negative/boundary/not_evaluable/not_applicable rules, exact EvaluationUnit identity and expected-set expansion, multi-snapshot behavior, three-part Query wording and journey joins.
- The contract distinguishes EX/EC/DA/IP from CM and never infers missed doses from one absent row or reuses a project-external adherence threshold.
- The implementation reuses the accepted R4 coverage, common identity, lifecycle and projection contracts without changing D01/D02 behavior.
- Synthetic tests cover all D03 primary subtypes plus cross-subject/site, treatment-role, stage, partial-date, missing denominator, allowed adjustment, duplicate/revision and N→N+1 cases.
- Focused D03 tests, full R4 regression, frozen R2/R3 regression, Ruff, compileall, package import/object identity and 8911-stopped checks pass on a stable snapshot; an independent reviewer owns final acceptance.

## Risk Boundaries

- Writable product scope is limited to the R4 POC package, its tests, this task's context/review/metrics/prompts/runs, and the D03 frozen contract. Do not modify the product application or any medical-writing path.
- Keep port 8911 stopped; do not run any of the five real clinical projects.
- Do not call an L1 finding a confirmed protocol deviation. Query drafts ask the site/user to verify facts and whether the situation constitutes a PD.
- Missing or conflicting treatment role, phase, planned/actual exposure, date precision, denominator, active protocol rule or cross-domain linkage must fail closed.
- Do not design or test the subsystem's security properties in this task.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, or malformed probe output must be recorded and followed by one real route attempt. Only a missing executable or explicit invalid/retired/unlisted model may stop before that attempt.

## Loop Log

- 2026-08-11 17:42:10: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-11 17:45:00: Codex re-anchored D03 from the frozen matrix, corrected the stale implementation-plan recovery point, and froze the above scope before any implementation dispatch.

## Lossless Pause Checkpoint — 2026-08-11

### Completed

- Re-anchored D03 against System Design v1.1, R0-R8 plan v1.1 and `FROZEN_R4_CONTRACT_V1`.
- Corrected the implementation plan's stale D02 recovery point.
- Created and froze `reviews/medical_monitoring_r4_d03_ip_slice_contract_v1_20260811.md` as `FROZEN_R4_D03_CONTRACT_V1`.
- Frozen contract covers six primary risk subtypes, exact EvaluationUnit/identity boundaries, project-specific calculable adherence, allowed action handling, cross-domain medical-action evidence, three-part Query and typed journey projection.
- Initialized this tracked task. No execution or conference session was dispatched.

### Current Evidence

- D03 contract initial SHA-256: `859b9fd340cdce18d12d34dbd357f07375b886c76d4c6d21f50de80d18ab339c`.
- Task context pre-checkpoint SHA-256: `5a5778dfc77329b2b585c9f00632127a8d28734e27b3f4fca0f91b723f9bcfd6` (this append necessarily changes it).
- Port 8911 check: `STOPPED`.
- Workspace root is not a Git repository, so `git status` is unavailable and was not treated as change evidence.
- No product source, R4 Python source/test, real project, service or medical-writing file was modified in this D03 start slice.

### Pending

- Independent review of the frozen D03 contract has not run.
- No D03 Python implementation, fixture, test, projection or root export exists yet.
- No D03-focused or regression test was run after freezing the contract.
- Generated guard prompt/review/metrics records remain; the reserved run/stdout paths were not created because no execution or conference dispatch occurred.

### Next Safe Action

1. Re-read this checkpoint, the frozen D03 contract and current R4 file hashes; confirm 8911 remains stopped.
2. Run a bounded independent contract challenge before implementation, focusing on treatment role/phase, adherence denominator, partial dates, allowed actions and exact cross-domain links.
3. If accepted, implement only `ip.py`, `ip_projection.py`, synthetic fixtures/tests and necessary `mm_r4.__init__` exports; preserve D01/D02 behavior.
4. Run D03 focused tests, full R4, frozen R2/R3, Ruff, compileall, import/object-identity and 8911 checks; then obtain independent current-snapshot acceptance.

Pause is lossless at the contract boundary. Do not infer that D03, R4 or the product is complete.
