# Task Context: medical_monitoring_r5_s2_precondition_contract_20260818

Created: 2026-08-18 14:11:30
Objective: 冻结并独立验收 R5 S2 synthetic/offline supplemental stage-authority packet contract；不写运行时，不启动8911
Task type: `stage_review_plan`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-sol` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md`
- `artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json`
- `context/medical_monitoring_r5_contract_acceptance_record_20260818.md`
- `context/medical_monitoring_r5_s1_acceptance_record_20260818.md`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/`
- R4 public contracts/projections referenced by the S1 adapter, read-only.
- Fresh S2 planner handoff `R5_S2_PRECONDITION_CONTRACT_READY` recorded in the parent task.

## Scope

- In scope: freeze a renderer-neutral, synthetic/offline-only S2 supplemental stage-authority overlay and exact packet contract; add deterministic generator/verifier artifacts; pin S0/S1/R4 authority SHAs; record the exact deferred leaves activated only for S2; prove all other deferred leaves remain closed.
- In scope: one machine-readable packet schema covering the exact R4 binding, center binding, single temporal visit/event/risk anchor, one-hop source binding, and isolated two-worker Inspector test authority needed by the first thin slice.
- Out of scope: S2 packet/runtime implementation, product frontend, browser, 8911, real projects, real models, clinical truth, production, security work, R1-R4 edits, existing S0/S1 refreeze, and all medical-writing paths.

## Success Criteria

- Contract explicitly states synthetic/offline test authority only and cannot be interpreted as clinical truth or production eligibility.
- Machine overlay pins the accepted S0 exact-contract SHA and accepted S1 adapter SHA; it does not mutate S0 object shapes, enums, invariants, or mappings.
- Activated deferred targets are an exact sorted set limited to the S2 thin slice; remaining deferred targets are exact and fail closed.
- Packet schema is exact-key with types, cardinality, nullability, closed enums, canonical hashing, NFC/sorted-unique constraints, and cross-object invariants.
- Center mapping derives domain/severity/pattern/individual identity from actual typed R4 member relations, never counts or UI inference.
- Temporal authority is a single visit/event/risk-anchor/source chain on the same subject/cutoff and never fabricates dates or nearest matches.
- Inspector test authority uses current R4 public dataclasses, two isolated attempts/workers/verifications, visible conflict, independent adjudicator, packet-only ModelEvidence; public worker/support/counter refs remain empty and S4-deferred.
- Deterministic verifier passes in normal and `PYTHONOPTIMIZE=2` modes, pins the exact artifact set and source SHAs, and fails on tampering.
- Fresh isolated reviewer returns `ACCEPT_R5_S2_PRECONDITION_CONTRACT` on one stable SHA set.
- Port 8911 remains stopped throughout.

## Risk Boundaries

- Allowed writes are limited to new S2 contract/review/context/metrics artifacts and `artifacts/medical_monitoring_r5_s2_authority_packet_contract_v0_1/**`.
- Do not modify `frontend/**`, `services/**`, `packages/**`, existing R1-R4, the accepted S0/S1 implementation or contract artifacts, real project data, or any medical-writing path.
- Do not start 8911, a browser, a model endpoint, or a long-running service.
- The supplemental packet must never claim current R4 public authority for synthetic temporal or Inspector facts.
- The delegated agent is not final authority; Codex owns integration, deterministic verification, and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, malformed output, or a stale/incomplete catalog must be recorded and followed by one real route attempt. Explicit user-selected routes are not blocked merely because the catalog does not list them; only a missing executable or native transport boundary may stop before that attempt.

## Loop Log

- 2026-08-18 14:11:30: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-18 14:14:00: Re-anchored current AGENTS, accepted S0/S1 records, 8911 stopped, and bounded S2 to contract-only work.
- 2026-08-18 14:33:00: Worker candidate passed mechanical checks; Codex rejected missing packet identity, baseline entities, projection-version binding, and mutable task-context pin.
- 2026-08-18 14:43:00: Fresh reviewer returned REVISE because public baseline assessment refs contradicted the S0 `BaselineAssessment.item_id` mapping.
- 2026-08-18 14:50:00: Corrected to the unique item-id projection, normal/optimized checks and 13 tamper probes passed, and the same isolated reviewer returned `ACCEPT_R5_S2_PRECONDITION_CONTRACT`.
