# Task Context: medical_monitoring_r5_s4_runtime_contract_20260819

Created: 2026-08-19 16:17:57
Objective: 冻结R5-S4 Risk Inspector synthetic/offline renderer-neutral runtime薄切合同与实现/验收边界
Task type: `stage_review_plan`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-sol` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`.
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`.
- `reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md`.
- `reviews/medical_monitoring_r5_s4_implementation_contract_v0_1_20260819.md`.
- `context/medical_monitoring_r5_s4_contract_acceptance_record_20260819.md`
  (`ACCEPT_R5_S4_CONTRACT`; contract only).
- `artifacts/medical_monitoring_r5_s4_contract_v0_1/{accepted_authority_anchor.json,packet_schema.json,exact_overlay.json,challenge_registry.json,source_pins.json,manifest.json}`.
- R4 read-only authority in `poc/medical_monitoring_ai_native_r4/src/mm_r4/{ensemble.py,ensemble_contracts.py,d10_contracts.py,d10_projection.py}`.
- Accepted R5 S1-S3 runtime patterns in `poc/medical_monitoring_ai_native_r5/src/mm_r5/{canonical.py,contracts.py,authority_adapter.py,s2_contracts.py,s2_authority_builder.py,s2_thin_slice.py,s3_contracts.py,s3_authority_builder.py,s3_projection.py}` and corresponding tests.
- Current filesystem is authoritative. The prior contract reviewer accepted the stable snapshot; 8911 is stopped.

## Scope

- In scope: propose the smallest exact S4 runtime thin-slice contract, typed public/runtime objects,
  source-to-output joins, deterministic reconstruction, challenge allocation, file allowlist,
  verification matrix, acceptance marker and rollback boundary needed before implementation.
- The contract must consume the accepted external authority anchor plus real R4/R5 typed public
  objects; it must not turn the contract verifier into runtime or copy the 2,000-line test fixture.
- Preserve 0/1/N semantics, input isolation, baseline source recheck, raw/parsed separation,
  seven-dimension verification before adjudication, full/non-hideable conflicts, independent
  adjudicator, deterministic Chinese audience projection, draft-only Query, append-only history,
  Journey fallback none, and audience/audit/hash separation.
- Named deferred remains fail-closed: AE/MH history, full subject temporal spine, critical authority.
- Out of scope: implementation, UI/browser/S7, 8911, real projects/models, R4 or S0-S3 edits,
  frontend/services, medical-writing, production and security-specialty work.

## Success Criteria

- Return a concrete contract proposal that Codex can write without inventing missing choices.
- Freeze exact proposed filenames and write allowlist under `poc/medical_monitoring_ai_native_r5/**`.
- Identify which accepted S4 machine artifacts are runtime input, test oracle only, or forbidden
  as runtime decision input; forbid case id/index/oracle/mutation/sentinel branching.
- Define typed object names and exact responsibility boundaries for contracts, builder,
  projection and validator; specify whether root `mm_r5/__init__.py` may receive minimal exports.
- Define deterministic non-LLM tests for valid 0/1/N, source/identity/hash tamper, baseline,
  conflicts, adjudication, Query, history, audience text and deferred failures.
- Define focused and adjacent regression gates, R4/R5 read-only SHA gate, normal/O2/import/Ruff/
  compile gate, and independent verdict `ACCEPT_R5_S4` / `REVISE_R5_S4`.
- No P0-P4 ambiguity, no hidden authority expansion, and no product/UI claim.

## Risk Boundaries

- This task is read-only planning. Do not modify any file.
- Do not start 8911 or any service; do not run real projects/models or browser work.
- Do not modify or re-sign the accepted S4 contract/artifacts/anchor or any R4/S1-S3 file.
- The runtime must not read challenge expected outcomes, registry categories, case ids, test locators,
  mutation metadata, or synthetic sentinel conventions to decide semantics.
- Runtime may validate packets against frozen public constants but cannot delegate all behavior to
  `tools/verify_medical_monitoring_r5_s4_contract_v0_1.py`; it must reconstruct from typed inputs.
- R4 remains the authority for medical risk/severity/Query/ensemble/adjudication; R5 only adapts and
  projects. High risk, mutual negation and baseline miss stay visible.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, malformed output, or a stale/incomplete catalog must be recorded and followed by one real route attempt. Explicit user-selected routes are not blocked merely because the catalog does not list them; only a missing executable or native transport boundary may stop before that attempt.

## Loop Log

- 2026-08-19 16:17:57: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-19 16:18: Contract source, scope, success criteria and read-only boundary frozen by Codex.
- 2026-08-19: Native `gpt-5.6-sol:high` planner completed read-only review; recommended four-module
  runtime split, no root export change, typed-anchor injection, 89 runtime + 8 governance cases.
- 2026-08-19: Codex materialized the proposal as
  `reviews/medical_monitoring_r5_s4_runtime_contract_v0_1_20260819.md`; runtime remains locked
  pending a fresh isolated `ACCEPT_R5_S4_RUNTIME_CONTRACT` verdict.
- 2026-08-19: Fresh isolated reviewer returned three successive `REVISE` verdicts; Codex closed
  historical gate/schema conflicts, N=0 conflict behavior, typed source/unavailable state,
  upstream Inspector trust, public APIs, accepted enums, deterministic Chinese projection and
  history-prefix semantics without modifying accepted machine artifacts.
- 2026-08-19: Reviewer returned `ACCEPT_R5_S4_RUNTIME_CONTRACT` on stable raw SHA
  `58848c51bbf25acddf1b34e2631d32f9294f8df22ecf6b5df438705ddcf16f54`.
  Acceptance record: `context/medical_monitoring_r5_s4_runtime_contract_acceptance_record_20260819.md`.
  Only contract section 8 create-only files are unlocked; runtime itself remains unaccepted.
