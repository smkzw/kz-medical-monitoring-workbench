# Codex Main-Venue Plan: medical_monitoring_r4_aemh_acceptance_20260810

Date: 2026-08-10
Objective: Independent acceptance review of stable synthetic R4 AE/MH longitudinal risk slice against FROZEN_R4_CONTRACT_V1, with public R2/R3 integration, fail-closed identity and close gates, Query/journey projections, and protected boundaries

## Task Decomposition

1. Freeze source digest and deterministic pre-dispatch anchors.
2. Dispatch two isolated read-only whole-snapshot reviews in parallel.
3. Compare findings against code and frozen matrix; reproduce every proposed veto.
4. If a real defect exists, repair only R4, rerun all anchors, freeze a new digest, and request same-session targeted re-review.
5. When stable reviewers and Codex accept, record review/metrics, clean exact R4 caches and execution temporaries, and advance the implementation plan without claiming product integration.

## Source Packet

- Frozen R4 coverage matrix and current `poc/medical_monitoring_ai_native_r4/` source/tests/README.
- Read-only R2 risk/identity/acceptance and R3 normalization public authorities.
- System Design v1.1 and R0-R8 plan only for R4 scope and stop-boundary cross-checks.
- Initial reviewed digest `545605e34bbda2b8eb67794952c3689edc17dc21a512b583dd73f3d343b7b277`; after accepted reviewer findings and R4-only repair, final digest `f100a0344db27f1d6e404a8b1fdd88a849dd43e5f0996a2e9e609b1c42546550`.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_qwen38` | `alibaba` | `qwen3.8-max` | `runs/conference/medical_monitoring_r4_aemh_acceptance_20260810/general_pi_qwen38.md` |
| `general_grok45` | `grok-build` | `grok-4.5` | `runs/conference/medical_monitoring_r4_aemh_acceptance_20260810/general_grok45.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Start after both prompt preflights pass. Each route gets one live dispatch and the 120-minute hard wait.
- Same-session follow-up only for a reproducible gap or incomplete report; no latency redispatch.
- Record effective provider/model/session/fallback from runner output in metrics.

## Codex Verification Checklist

- Recompute source digest before and after conference.
- Re-run R4 full, focused R2/R3, Ruff, compile/import, exact boundary subset, and 8911 stop check after any change.
- Inspect identity recomputation before all side effects and exact candidate/ref one-to-one validation.
- Inspect complete-ledger plus exact historical linked-negative close gate and uncertainty/different-event behavior.
- Confirm no runtime `sys.path`, tests-helper, private R2 API, fixed table/project rule, or silent temporal default.
- Validate Query basis/finding/action and source links; journey category/risk/uncertainty source links.
- Do not promote this synthetic R4 slice to product/R5 acceptance.

## Completion

- [x] Initial independent reviews completed and reproducible gaps adjudicated.
- [x] R4-only repairs completed; frozen R1-R3 and protected systems unchanged.
- [x] Final deterministic anchors passed: R4 224, focused R2 213, focused R3 126, Ruff/compile/import/hash/8911.
- [x] Two effective independent review routes returned final ACCEPT.
- [x] Codex accepted only the isolated synthetic R4-D01 slice; next stage is R4-D02.
