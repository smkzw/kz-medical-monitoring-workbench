# Codex Main-Venue Plan: medical_monitoring_r4_d05_final_acceptance_20260812

Date: 2026-08-12
Objective: 独立只读验收R4-D05访视评估与Patient Journey离线纵切最终快照

## Task Decomposition

1. Verify frozen contract, current hashes and protected boundaries.
2. Run a fresh-context Luna veto/accept pass with adversarial probes.
3. Correct only actionable contract gaps and return to the same session.
4. Accept only after full D05/R4/R2/R3 and cleanup gates pass.

## Source Packet

Frozen D05 contract, current eight D05 source/test files, root exports, README,
R2/R3 regressions, port and cache state.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_qwen38` | `alibaba` | `qwen3.8-max` | `runs/conference/medical_monitoring_r4_d05_final_acceptance_20260812/general_pi_qwen38.md` |
| `general_grok45` | `grok-build` | `grok-4.5` | `runs/conference/medical_monitoring_r4_d05_final_acceptance_20260812/general_grok45.md` |

The generated default participant rows above were not dispatched. Decisive
independent verification used `codex_luna_verifier` through the documented CLI
compatibility route after native Luna spawn rejection.

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

One Luna session, three terminal passes: REJECT, REJECT, ACCEPT. Each follow-up
addressed concrete findings; no latency fallback, duplicate dispatch or late
output substitution occurred.

## Codex Verification Checklist

- Contract and exact hashes
- D05 twice; R4/R2/R3
- 116-row semantics and weak-builder attacks
- stable logical visit key
- formal auxiliary marker type and content-id recomputation
- root exports, Ruff, AST, cache zero and 8911 stopped
