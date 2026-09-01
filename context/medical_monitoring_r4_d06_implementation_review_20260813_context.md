# Task Context: medical_monitoring_r4_d06_implementation_review_20260813

Created: 2026-08-13 05:29:58
Objective: Independently review the exact R4-D06 synthetic/offline implementation snapshot for runtime-derived semantics, non-circular 219-case evidence, frozen-contract compliance, regressions and acceptance blockers
Task type: `high_risk_contradiction_review`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Frozen D06 contract and acceptance record: `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md`, `context/medical_monitoring_r4_d06_contract_acceptance_record_20260813.md`.
- Immutable validation inputs: typed catalog, independent oracle, registry and generator named in the implementation context.
- Exact implementation source/test hashes supplied in the review prompt.
- Worker handoff `runs/pi_medical_monitoring_r4_d06_implementation_20260813.md` is a claim source, not acceptance authority.
- Current filesystem and independently executed tests are authoritative.

## Scope

- In scope: read-only adversarial review of exact D06 implementation snapshot; verify runtime-derived outcomes, non-circular challenge evidence, trace/hash/audience/identity contracts and focused regression evidence; issue P0-P4 findings and ACCEPT/REJECT.
- Out of scope: edits; services/8911; real projects/data/providers; R5/product UI; statistical efficacy analysis; medical writing; security design/testing; D07-D10.

## Success Criteria

- All supplied hashes match and focused tests/generator check reproduce.
- Runtime evaluator/projection do not read expected outcomes, oracle or manifest and do not branch on challenge identifiers.
- Test-side assembly does not replace runtime medical/trace/audience/hash results with expected or manifest values.
- Semantically identical typed inputs cannot produce substantively different expected runtime outcomes; any frozen-artifact contradiction is blocking.
- Reviewer returns evidence-backed P0-P4 findings and exact verdict without editing.

## Risk Boundaries

- Read-only. Do not modify any file or start any service.
- Do not accept green counts when the oracle is satisfied through expected-output injection or non-runtime metadata substitution.
- The known 106/191 duplicate-input trace mismatch is a required adversarial target, not a pre-decided sole finding; search for additional concrete escapes.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, or malformed probe output must be recorded and followed by one real route attempt. Only a missing executable or explicit invalid/retired/unlisted model may stop before that attempt.

## Loop Log

- 2026-08-13 05:29:58: Task initialized by `tools/hermes_workflow_guard.py init-task`.
