# Task Context: medical_monitoring_r4_coverage_aemh_20260810

Created: 2026-08-10 20:16:39
Objective: 冻结 R4 全风险域 coverage matrix 与共同风险合同，并在隔离合成包中实现 AE/MH 漏报首个端到端风险纵切，不修改产品、医学写作、冻结 R1-R3 或真实项目，8911 保持停止
Task type: `long_horizon_code`
Risk: `high`
Selected agent route: `cms-smk` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py` and its focused tests, read-only reuse reference
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py` and frozen R2 public contracts, read-only reuse reference
- `poc/medical_monitoring_ai_native_r3/**` and `poc/medical_monitoring_ai_native_r3_rule_ai/**`, read-only rule/knowledge reference
- `context/monitoring_p7d_real_evidence_matrix_20260729.md`, historical gap evidence only
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`, current R4 contract draft
- Official ICH E2A, ICH E6(R3), CDISC SDTMIG v3.3, NCI CTCAE and NMPA clinical-data-submission guidance linked in the matrix

## Scope

- In scope: freeze the R4 common coverage/risk contract for all planned risk domains; independently challenge it; then create a new isolated synthetic/offline R4 package implementing the AE/MH consistency, seriousness and suspected-under-reporting vertical slice with coverage, evidence, lifecycle, Query and audience projection data.
- Allowed writes: `poc/medical_monitoring_ai_native_r4/**` plus this task's `context/`, `prompts/`, `reviews/`, `metrics/`, `plans/`, `runs/` and guard-owned archive files.
- Read-only: frozen R1/R2/R3 packages and their acceptance evidence.
- Out of scope: product source/runtime, the medical-writing subsystem, all five real projects, real provider/model execution for product analysis, port 8911, external communication, production migration, and system-security design/testing.

## Success Criteria

- Coverage matrix explicitly separates L0 execution coverage, five exclusive L1 medical dispositions, L1b evidence polarity, L2 objects and R2-owned L3 lifecycle, and defines applicability, inputs, authority, denominator, temporal boundary, false-positive/false-negative controls, adjudication, user projection and outputs for every R4 risk domain.
- An isolated reviewer challenges the matrix against Design/Plan, official primary standards and frozen R1/R2/R3 contracts; Codex resolves all accepted findings before marking it frozen.
- AE/MH R4 package uses structured roles rather than fixed source table names and keeps reported AE/MH, unverified clues, risk instances and Query drafts separately counted.
- AE/MH logic covers symptoms, CM indication, lab/exam, hospitalization/procedure, death/seriousness and IP action evidence; protocol-driven time boundaries; counterevidence; severity/seriousness/monitoring-priority separation; row-level provenance; shared temporal-spine projections; subject/site/project aggregation; and N/N+1 lifecycle.
- Deterministic tests cover positive, negative, boundary, counterevidence, not-applicable, not-evaluable, hidden, false-positive and false-negative cases plus focused cross-package contracts.
- Focused R4 and adjacent frozen-package regression pass; an independent verifier accepts the final stable snapshot.
- Port 8911 has no listener; no real project or medical-writing file is modified.

## Risk Boundaries

- Do not write to product/runtime, medical-writing, real-project or frozen R1/R2/R3 paths.
- Keep project-specific rules and thresholds out of the common engine.
- Do not adopt external executable dependencies in this slice; standards are evidence, not runtime components.
- Do not represent model output, a missing table, an empty result or an incomplete run as a clean medical conclusion.
- Do not conflate CTCAE/severity, seriousness and monitoring priority.
- Do not design or test system security in this task.
- Keep 8911 stopped.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, or malformed probe output must be recorded and followed by one real route attempt. Only a missing executable or explicit invalid/retired/unlisted model may stop before that attempt.

## Loop Log

- 2026-08-10 20:16:39: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-10: Codex read the R4 design/plan, frozen R1 AE/MH and R2 lifecycle contracts, historical risk evidence matrix, and official ICH/CDISC/NCI/NMPA sources; created the all-domain coverage-contract draft for fresh-context challenge.
- 2026-08-10: Pi medical review returned ACCEPT with non-blocking match-window/severity/lifecycle corrections; Grok engineering review returned VETO on state layers, denominators, lifecycle authority, temporal precision and joins.
- 2026-08-10: Codex accepted and corrected the in-scope defects, then resumed the same Grok session for a delta review. Grok marked every prior P1-P4 finding resolved and returned ACCEPT; Codex applied its three final P4 wording suggestions.
- 2026-08-10: Matrix frozen as `FROZEN_R4_CONTRACT_V1`, SHA-256 `6bb9f73a56de7e3ba38532b4fd3edadc76d788a099186f7c60212fb9c4a92705`; both final participant outputs are ACCEPT; 8911 remained stopped.

## Current Checkpoint

- Completed: R4 full-domain coverage matrix and common risk contract freeze.
- Pending: isolated synthetic/offline AE/MH implementation under `poc/medical_monitoring_ai_native_r4/**`.
- Next safe action: initialize the bounded R4 execution graph, then implement the common coverage primitives before the AE/MH reconciler and R2 lifecycle/projection adapters.
- Keep unchanged: product/runtime, medical-writing, five real projects, frozen R1-R3 and port 8911.
