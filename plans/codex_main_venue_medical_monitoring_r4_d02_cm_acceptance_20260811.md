# Codex Main-Venue Plan: medical_monitoring_r4_d02_cm_acceptance_20260811

Date: 2026-08-11
Objective: Independent acceptance review of frozen isolated synthetic R4-D02 CM engine, D01 cross-domain consumption, journey projection, 30-case matrix, lifecycle and regression evidence; ACCEPT or REJECT without modifying files

## Task Decomposition

1. Independently compare the frozen D02 contract/matrix with the actual source
   and executable tests; do not rely on worker reports as acceptance authority.
2. Challenge the two former gaps: competing stable/new-start evidence and the
   real D01 dual-path dedup consumer.
3. Audit identity/lineage, Query/source joins, journey anchors/Chinese typed
   labels, 30-case coverage and N-to-N+1 behavior for false-clean paths.
4. Reproduce focused/full deterministic checks as needed and return an explicit
   `ACCEPT` or `REJECT` with exact evidence. Codex performs final synthesis.

## Source Packet

- Frozen D02 contract and common R4 matrix.
- D02 execution context through Gate 4.
- `src/mm_r4/{contracts,aemh,lifecycle,cm,cm_projection,cm_fixtures,__init__}.py`.
- `tests/{test_shared_domain_protocol,test_cm_slice,test_cm_projection,test_cm_challenge_matrix}.py`.
- Adjacent R2/R3 tests only when needed to reproduce regression evidence.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_qwen38` | `alibaba` | `qwen3.8-max` | `runs/conference/medical_monitoring_r4_d02_cm_acceptance_20260811/general_pi_qwen38.md` |
| `general_grok45` | `grok-build` | `grok-4.5` | `runs/conference/medical_monitoring_r4_d02_cm_acceptance_20260811/general_grok45.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Start: 2026-08-11 17:00:00 +0800.
- Hard wait: 120 minutes; no fixed-interval polling or latency redispatch.
- End/status/fallback/incorporation are recorded after terminal runner output.

## Codex Verification Checklist

- Recompute frozen and implementation digests after reviewers finish.
- Re-run any failing reviewer reproduction before accepting a defect.
- Require exact D01 224 plus full R4/R2/R3 green after any repair.
- Run Ruff, compilation and explicit public import identity check.
- Confirm no listener on 8911.
- Record residual synthetic/offline limitation and do not claim product/R5-R8
  readiness.
