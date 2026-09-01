# Codex Main-Venue Plan: medical_monitoring_r1_framework_persistence_adr_20260809

Date: 2026-08-09
Objective: 基于 R1 已验收的框架中立 SQLite 领域内核、双候选框架 spike 和 audience-facing AE/MH 纵切，独立挑战并收口主图引擎、持久化、Temporal 延后、回滚和后续验证门的 ADR；不得修改产品、医学写作、真实项目、服务或运行库

## Task Decomposition

1. Re-anchor the decision against System Design v1.1 and the R0-R8 plan.
2. Audit the accepted framework-neutral Store/artifact authority and the two
   isolated adapter results, including repaired failures and residual risks.
3. Obtain two independent, read-only architecture challenges without sharing
   participant reasoning or outputs.
4. Codex decides the graph/persistence disposition and writes a reversible ADR
   with explicit non-adoption and R1-remaining-work gates.
5. Run deterministic link/source checks and the applicable review gate; archive
   only task-owned temporary conference material after acceptance.

## Source Packet

- System authority: `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
  and `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`.
- Core decision: `poc/medical_monitoring_ai_native_r1/docs/ADR-001-framework-neutral-sqlite.md`.
- Candidate evidence: `poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/docs/DEPENDENCY_DECISION.md`
  and `poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/docs/SPIKE_EVIDENCE.md`.
- Accepted reviews/metrics: Slice2 framework spike and Slice3 audience workbench
  records listed in the conference context.
- Same-day official-source and package-license discovery is already frozen in
  the dependency record; reopen only on a material inconsistency.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_qwen38` | `alibaba` | `qwen3.8-max` | `runs/conference/medical_monitoring_r1_framework_persistence_adr_20260809/general_pi_qwen38.md` |
| `general_grok45` | `grok-build` | `grok-4.5` | `runs/conference/medical_monitoring_r1_framework_persistence_adr_20260809/general_grok45.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Record start/end time, terminal state, actual provider/model/session,
  fallback reason and whether each output was incorporated.
- Launch each declared route once and wait on the runner hard wait; no fixed
  polling or redispatch for latency.

## Codex Verification Checklist

- All authoritative sources were read from the current filesystem.
- Both participant reports are terminal or explicitly pending under policy.
- ADR states exact authority, adapter, checkpoint and rollback boundaries.
- ADR does not claim product adoption, production durability or R1 completion.
- Temporal reopen condition is falsifiable; Agent Framework residual is not
  softened; historical repaired defects remain visible.
- No product, medical-writing, real-project, service, runtime or lockfile change.
- Review/metrics contain deterministic anchors and pass the guard review gate.
