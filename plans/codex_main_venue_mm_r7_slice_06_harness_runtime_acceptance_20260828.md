# Codex Main-Venue Plan: mm_r7_slice_06_harness_runtime_acceptance_20260828

Date: 2026-08-28
Objective: 独立审查纠偏后的 R7 Slice-06 synthetic/offline harness 调用、有限重试与恢复实现，逐项挑战冻结合同矩阵、状态机、身份/租约边界、公开泄漏与回归证据；不得运行真实模型、服务、真实项目或修改产品文件。

## Task Decomposition

1. Independently trace the frozen matrix through current R7/R1/R6 seams.
2. Challenge identity/status/retry/lease/stop/rebuild fail-closed behavior and tests.
3. Challenge product Chinese projection and internal-field leakage evidence.
4. Return exact defects or a bounded acceptance; Codex reproduces every material claim.

## Source Packet

The authoritative packet is the frozen Slice-06 contract, current corrected R7
source/tests, product router test, worker receipt/stage record, Codex execution
review and restored runner evidence listed in the conference context. R1/R6 are
read-only adjacent contracts. No web research or production/runtime access is needed.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_antigravity` | `google-antigravity` | `gemini-3.7-flash` | `runs/conference/mm_r7_slice_06_harness_runtime_acceptance_20260828/general_pi_antigravity.md` |
| `general_grok46` | `grok-build` | `grok-4.6` | `runs/conference/mm_r7_slice_06_harness_runtime_acceptance_20260828/general_grok46.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Start after prompt preflight; wait up to the declared 120-minute hard boundary.
- Do not poll or redispatch for latency. Follow up only for a concrete missing finding
  or ambiguous evidence, and reuse the same session handle.
- Record terminal duration, session id, fallback and whether output was incorporated.

## Codex Verification Checklist

- Reproduce every P0–P2 finding against current bytes.
- If repaired, rerun harness focus, full R7, product router, R1/R6 functional and
  determinism/boundary gates as affected.
- Revalidate receipt digests, compile under isolated cache and stopped 8911/5174.
- Keep acceptance synthetic/offline and separate from real-model smoke.

## Completion

- Both primary participants completed without fallback.
- Codex disproved one proposed recovery defect with a direct claim-before-bind
  crash replay and repaired the separately reproduced multi-unit `继续` defect.
- Grok round 2 reused its original session and accepted the current bytes.
- Offline conference verdict: PASS to the separate matrix-14 live-smoke gate;
  no broader phase or product acceptance is implied.
