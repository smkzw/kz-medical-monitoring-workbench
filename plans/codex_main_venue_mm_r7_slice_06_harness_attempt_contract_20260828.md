# Codex Main-Venue Plan: mm_r7_slice_06_harness_attempt_contract_20260828

Date: 2026-08-28
Objective: 独立审阅并挑战 R7 Slice-06 harness capability attempt、有限重试、恢复与诚实 session/cancel 语义合同；只读源码与合同，不修改文件，不调用模型服务或真实项目，不启动产品服务。输出必须逐项回答四个待会商问题，列出 P0-P4 缺陷及可执行修订建议，并明确 ACCEPT 或 REVISE。

## Task Decomposition

1. Independently reconcile the draft against R1 attempt journal/controller invariants.
2. Independently reconcile it against the R6 one-shot OMP adapter and R7 run-level control state.
3. Challenge preflight-zero-attempt, retry ceiling, continuation/session language, cancel, and dual-CAS ordering.
4. Synthesize amendments, freeze a corrected contract, and only then authorize implementation.

## Source Packet

- Draft contract and Slice-05-to-06 phase review under `context/`.
- Frozen Slice-05 contract/erratum and R6 harness acceptance record.
- Current R1 store/capability controller/runtime, R6 harness adapter, and R7 background/run-binding/progress source.
- R0-R8 implementation plan v1.1.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_antigravity` | `google-antigravity` | `gemini-3.7-flash` | `runs/conference/mm_r7_slice_06_harness_attempt_contract_20260828/general_pi_antigravity.md` |
| `general_grok46` | `grok-build` | `grok-4.6` | `runs/conference/mm_r7_slice_06_harness_attempt_contract_20260828/general_grok46.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Start: 2026-08-28 11:36 CST.
- Run both declared roles serially with the runner's 120-minute hard wait.
- Reuse the recorded role session for any targeted clarification; do not create replacement sessions for a live role.
- Record terminal route identity, fallback, duration and incorporation in review/metrics after both roles finish.
- Completed: Pi 2 rounds/35.445s and Grok 2 recorded continuation rounds/271.670s; both reused the same
  session, with no fallback. Grok's final v0.3 delta is the accepting terminal review.

## Codex Verification Checklist

- Confirm participant route identity and no undeclared fallback.
- Reopen cited source lines rather than accepting model assertions.
- Resolve every P0/P1 and material P2 before freezing.
- Preserve the distinction between logical attempt continuation and actual transport same-session continuation.
- Confirm no model/service/real-project invocation and 8911/5174 remain stopped during contract freeze.
- Hash the final contract and record remaining implementation/acceptance limits.
- Completed: final contract SHA-256
  `3c879889e30541b2556bc8c2643758029b52e7cc9876f9b27d7e0e5b73bbbc21`.
