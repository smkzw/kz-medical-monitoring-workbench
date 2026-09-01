# Codex Main-Venue Plan: mm_r7_slice06_matrix14_bridge_fix_review_20260828

Date: 2026-08-28
Objective: Independently review the R7-to-R6 invocation ID mapping and deterministic output-contract repair after the first matrix-14 MTPLX smoke exposed invalid_invocation_id. Verify R6 and R1 remain unchanged, the mapping is deterministic and collision-resistant enough for bounded runtime identity, classifier equality uses the mapped ID, the prompt is deterministic and carries exact expected coverage without provider/model identity, tests cover the live failure mode, and decide whether one controlled MTPLX retry may proceed before DeepSeek. Do not modify files or call models.

## Task Decomposition

1. Independently reproduce the first live failure and audit the mapping.
2. Audit dispatch/classifier symmetry, JSON-RPC identity and prompt purity.
3. Verify frozen R1/R6 integrity and the focused/adjacent test evidence.
4. Decide whether one controlled MTPLX retry is allowed before DeepSeek.
5. Codex remediates any accepted test gap and owns the final decision.

## Source Packet

- conference context and matrix-14 execution packet
- current R7 bridge and focused tests
- frozen R6 adapter and R1 classifier
- worker02 first live-smoke report and runner metadata

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_antigravity` | `google-antigravity` | `gemini-3.7-flash` | `runs/conference/mm_r7_slice06_matrix14_bridge_fix_review_20260828/general_pi_antigravity.md` |
| `general_grok46` | `grok-build` | `grok-4.6` | `runs/conference/mm_r7_slice06_matrix14_bridge_fix_review_20260828/general_grok46.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Pi/Gemini: complete in 122.970 s, no fallback, incorporated.
- Grok Build: complete in 381.994 s, no fallback, incorporated.
- No late output or participant retry. One later product-harness MTPLX repair
  retry was separately authorized and is not a conference participant retry.

## Codex Verification Checklist

- [x] Exact R6 grammar and first failure reproduced.
- [x] Deterministic mapped ID and classifier equality verified.
- [x] Prompt includes exact coverage and excludes provider/model identity.
- [x] Real frozen-R6 grammar regression added after Grok objection.
- [x] R7/product/R1/R6 offline suites passed under declared exclusions.
- [x] Ports remained stopped and R1/R6 hashes remained unchanged.
- [x] Conference scope accepted; matrix-14 live gate kept separate.
