# Codex Main-Venue Plan: medical_monitoring_r4_coverage_matrix_20260810

Date: 2026-08-10
Objective: 以新上下文独立反证 R4 全风险域 coverage matrix 与共同风险合同，核查医学语义、覆盖完整性、与 Design v1.1/R4 计划及冻结 R1-R3 合同的一致性，输出可执行 VETO 或 ACCEPT

## Task Decomposition

1. Participant 1 independently reviews clinical/regulatory semantics and false-positive/false-negative protections.
2. Participant 2 independently reviews engineering precision, state/identity/lifecycle compatibility and deterministic testability.
3. Codex checks every proposed blocker against the approved design, official sources and current frozen source contracts.
4. Codex applies only accepted, in-scope corrections to the matrix, reruns text/contract checks and records the final freeze decision.

## Source Packet

- Artifact: `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`
- Approved design: `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- Approved plan: `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R4
- Frozen reference: R1 `ae_mh.py` and focused tests; R2 `risk.py` and focused tests; R3 public contracts only when a rule/knowledge claim requires it
- Historical gap evidence: `context/monitoring_p7d_real_evidence_matrix_20260729.md`
- Official primary references: links in matrix section 2.2

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_qwen38` | `alibaba` | `qwen3.8-max` | `runs/conference/medical_monitoring_r4_coverage_matrix_20260810/general_pi_qwen38.md` |
| `general_grok45` | `grok-build` | `grok-4.5` | `runs/conference/medical_monitoring_r4_coverage_matrix_20260810/general_grok45.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Record start/end, selected/effective route, session ID, terminal state, fallback reason, same-session follow-up and whether the output was incorporated.
- Leave a running route pending through the configured hard wait; no fixed-interval redispatch.

## Codex Verification Checklist

- [x] Exact source packet and boundaries were respected.
- [x] Both participant reports are independent and include locators/evidence.
- [x] AE/MH、严重程度/严重性/监察优先级，以及 L0 执行覆盖、五类互斥 L1 医学评价、L1b 证据方向和 L3 生命周期分层一致。
- [x] Ten planned domains cover R4 plan steps 2-8 without stealing R5/R7 scope.
- [x] Candidate/source record/risk/Query counts and lifecycle semantics match frozen R2.
- [x] L0/L1/L3 的 `not_applicable`/`not_evaluable` 不串层，L1 negative 与 L1b 排除依据不能制造假性完整覆盖。
- [x] First-slice contract is implementable with deterministic synthetic tests and no fixed table names/project thresholds.
- [x] Accepted corrections are applied and the final artifact status/digest are recorded before freeze.
- [x] 8911 remains stopped; no product, medical-writing, real-project or frozen R1-R3 file changed.

Final freeze: `FROZEN_R4_CONTRACT_V1`; SHA-256 `6bb9f73a56de7e3ba38532b4fd3edadc76d788a099186f7c60212fb9c4a92705`.
