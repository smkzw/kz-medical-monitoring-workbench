# Codex Main-Venue Plan: mm_r7_slice07c2_prepare_start_acceptance_20260829

Date: 2026-08-29
Objective: 独立审阅 R7 Slice-07C-2 synthetic/offline prepare-and-start、launch registry、public history、幂等/补偿、跨项目隔离和长等待语义；不修改文件，给出 accept/revise/block advisory。

## Task Decomposition

1. Audit prepare/start, registry identity and public history against the frozen contract.
2. Challenge interruption, replay, state convergence, authorization and public leakage.
3. Apply bounded corrections, rerun deterministic tests, and request same-session rechecks.

## Source Packet

Frozen 07C v0.2 and 07C-2 contracts; current launch registry, run setup,
background recovery, product router, focused/full tests, receipt and README.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_single_object` | `codebuddy-cli` | `deepseek-v4-flash` | `runs/conference/mm_r7_slice07c2_prepare_start_acceptance_20260829/general_single_object.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

One CodeBuddy/DeepSeek V4 Flash max session completed three passes within the
120-minute hard-wait policy. Pass 1 and 2 were incorporated as revisions; pass 3
returned `ACCEPT`. No fallback or replacement session was used.

## Codex Verification Checklist

- [x] Frozen request/public-history contract matched.
- [x] Idempotency conflict, cross-project tokens and role boundary tested.
- [x] Reservation-only interruption heals the same run.
- [x] Runtime completion reconciles to bounded public history.
- [x] Product and full R7 tests, compileall and stopped ports passed.
- [x] No visual surface, real project, service or medical-writing mutation.
