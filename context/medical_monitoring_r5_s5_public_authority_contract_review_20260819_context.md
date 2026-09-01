# Task Context: medical_monitoring_r5_s5_public_authority_contract_review_20260819

Created: 2026-08-19 20:21:33
Objective: 独立复核 R5-S5 两项公共权威合同候选的 immutable SHA、语义闭合与实现解锁边界
Task type: `stage_review_plan`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-sol` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_r5_s5_public_authority_contract_v0_1_20260819.md`
- `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/**`
- `tools/generate_medical_monitoring_r5_s5_public_authority_contract_v0_1.py`
- `tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py`
- Accepted parent R5 v0.3 machine contract, S4 acceptance, and current R1/R2/R4/R5 source paths pinned by the manifest.

## Scope

- In scope: fresh-context read-only semantic and mechanical review of one immutable SHA set; replay normal/O2 generator/verifier and independent tamper probes; issue exactly `ACCEPT_R5_S5_PUBLIC_AUTHORITY_CONTRACT` or `REVISE_R5_S5_PUBLIC_AUTHORITY_CONTRACT`.
- Out of scope: editing any file, creating runtime/tests, accepting either implemented public authority, accepting S5, frontend/browser/services/8911, real projects/models, clinical truth, production, security, or medical writing.

## Success Criteria

- Contract schemas close exact identity, receipt, visibility, source, temporal geometry/membership and AE/MH append-only history semantics without claiming unavailable upstream direct authority.
- Parent 64 cases are an exact projection, no second quota ledger exists, public-specific cases are bounded and executable as contract tamper probes.
- Normal/O2 verification, SHA stability, source pins, no-assert, no-runtime and 8911-stopped gates pass.
- Any P0-P4 or ambiguity returns REVISE with exact evidence.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Strictly read-only. The reviewer may veto or accept the contract candidate but must not repair it.
- Acceptance only unlocks a later public-authority implementation contract; it is not `ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1`, `ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1`, or `ACCEPT_R5_S5_CONTRACT`.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, malformed output, or a stale/incomplete catalog must be recorded and followed by one real route attempt. Explicit user-selected routes are not blocked merely because the catalog does not list them; only a missing executable or native transport boundary may stop before that attempt.

## Loop Log

- 2026-08-19 20:21:33: Task initialized by `tools/hermes_workflow_guard.py init-task`.
