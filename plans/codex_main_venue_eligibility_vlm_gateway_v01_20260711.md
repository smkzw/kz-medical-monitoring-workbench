# Codex Main-Venue Plan: eligibility_vlm_gateway_v01_20260711

Date: 2026-07-11
Objective: Review the independently runnable local/private eligibility VLM gateway, nonclinical security fixtures, privacy boundary, and no-fallback circuit breaker before any worker integration

## Task Decomposition

1. Inspect the bounded gateway and tests against v0.2.
2. Obtain independent Qwen, Mimo, and Reasonix DeepSeek Flash code/contract reviews.
3. Route sub-venue synthesis only to `aishuo/MiniMax-M3` and verify actual markers.
4. Codex adjudicates findings, applies only narrow agreed fixes, and reruns verification.
5. Keep worker integration and real clinical-image use closed until separate gates pass.

## Source Packet

Use only the files listed in `context/eligibility_vlm_gateway_v01_20260711_conference_context.md`.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/eligibility_vlm_gateway_v01_20260711/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/eligibility_vlm_gateway_v01_20260711/participant_mimo.md` |
| `participant_ds_flash` | `reasonix-cli` | `deepseek-v4-flash` | `runs/conference/eligibility_vlm_gateway_v01_20260711/participant_ds_flash.md` |
| `participant_antigravity_gemini35` | excluded | non-visual conference | not run |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `aishuo` | `MiniMax-M3` | `runs/conference/eligibility_vlm_gateway_v01_20260711/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Agent/model: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro`.
- Reasoning: maximum configured Reasonix effort. Verify stdout/metrics when possible.
- Forbidden: Hermes, OpenCode Go, Hermes custom providers, or direct DeepSeek provider `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/eligibility_vlm_gateway_v01_20260711/main_deepseek_pro.md`

## Timeout And Retry Tracking

Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used in metrics.

## Codex Verification Checklist

- No placeholder participant/chair output.
- Exact route markers recorded.
- Focused tests and compile checks pass before chair review.
- Full repository tests and frontend build pass after accepted fixes.
- Review and metrics contain no unresolved placeholders before review gate.
