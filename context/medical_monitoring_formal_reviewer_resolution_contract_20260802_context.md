# Task Context: medical_monitoring_formal_reviewer_resolution_contract_20260802

## Objective

Build a pure validator for future B6 reviewer-resolution submissions so that a
real hash-bound outcome can be checked without mutating the existing package or
granting authority.

## Decision

The formal package already exposes the required fields but has no JSON-level
validator for a future reviewer submission. Add the smallest standalone
contract rather than widening the runtime mapping or approval models. A
structurally valid submission is a handoff diagnostic only; it is not a B6
approval and cannot unlock C14.

## Evidence

- Source implementation:
  `services/api/app/monitoring_formal_reviewer_resolution.py`
- Focused tests: `tests/test_monitoring_formal_reviewer_resolution.py`, **11 passed**.
- Synthetic contract replay:
  `records/active_slices/medical_monitoring_formal_reviewer_resolution_contract_20260802/FORMAL_REVIEWER_RESOLUTION_CONTRACT.json`.
- Current input package SHA:
  `fa9f37fcc3c6314e7ddf743336a0b0ceb2e341ff5eb00fb415508212ac02710c`.

## Scope and limits

The validator binds every outcome to the current package and B3/B4 hashes,
checks exact candidate fingerprints, explicit reviewer identity/time, medical
disposition, source lineage, aggregate/CAS evidence, external-action decision,
rationale and residual blockers. Approvals additionally require confirmed
lineage/CAS and explicit observed expected versions. It never infers absent
evidence, writes a gate, or enables runtime.

## Next safe action

Obtain real reviewer outcomes, validate them with this contract, then rerun B6
and approved-input checks. Until that external evidence exists, preserve
`pending_review`, C14 blocked state, release blocked state and stopped ports.
