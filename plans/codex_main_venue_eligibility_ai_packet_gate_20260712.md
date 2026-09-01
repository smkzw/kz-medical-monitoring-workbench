# Codex Main-Venue Plan: eligibility_ai_packet_gate_20260712

Date: 2026-07-12
Objective: 复核入排审核AI受控证据packet、调用前版本/QC门禁、packet幂等和公共API身份边界

## Task Decomposition

1. Independently audit packet assembly and provider/persistence request trace.
2. Required `aishuo/MiniMax-M3` chair compares participants and adjudicates source claims.
3. Reasonix `deepseek-pro` challenges the complete sub-venue package.
4. Codex reproduces actionable defects, patches only verified issues and reruns focused/full tests.

## Source Packet

The authoritative source list and verified 568-test baseline are in `context/eligibility_ai_packet_gate_20260712_conference_context.md`.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/eligibility_ai_packet_gate_20260712/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/eligibility_ai_packet_gate_20260712/participant_mimo.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `aishuo` | `MiniMax-M3` | `runs/conference/eligibility_ai_packet_gate_20260712/hermes_lead.md` |

## Main-Venue Review

- Reasonix CLI `deepseek-pro` writes `runs/conference/eligibility_ai_packet_gate_20260712/main_deepseek_pro.md`.
- Codex performs final source verification, patching and acceptance.

## Timeout And Retry Tracking

Record route markers, duration, terminal status, retry evidence and whether each output was incorporated.

## Codex Verification Checklist

- Provider/model/completion route markers verified.
- No original clinical files/images read by delegated models.
- Packet body only from integrity-checked controlled artifacts.
- Stale/QC/idempotency/public actor boundaries traced and tested.
- Focused and authoritative backend regressions pass after any patch.
