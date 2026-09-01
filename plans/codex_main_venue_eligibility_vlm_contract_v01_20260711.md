# Codex Main-Venue Plan: eligibility_vlm_contract_v01_20260711

Date: 2026-07-11
Objective: Review and adjudicate the closed-vocabulary VLM contract for eligibility visual evidence before any implementation or real clinical-image use

## Task Decomposition

1. Three independent participants review the same bounded contract and prior v11 gate.
2. `aishuo/MiniMax-M3` compares outputs, resolves disagreements, and produces the Hermes sub-venue package.
3. Reasonix DeepSeek Pro challenges the chair package as the high-risk main-venue reviewer.
4. Codex checks source boundary, applies accepted contract changes, runs the review gate, and decides whether nonclinical implementation may begin.

## Source Packet

- VLM closed-vocabulary contract v0.1.
- Prior visual-QC/VLM conference review and route metrics.
- Real v11 visual-QC gate record.
- No clinical image, raw OCR body, local source path, or production database is delegated.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/eligibility_vlm_contract_v01_20260711/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/eligibility_vlm_contract_v01_20260711/participant_mimo.md` |
| `participant_ds_flash` | `reasonix-cli` | `deepseek-v4-flash` | `runs/conference/eligibility_vlm_contract_v01_20260711/participant_ds_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `aishuo` | `MiniMax-M3` | `runs/conference/eligibility_vlm_contract_v01_20260711/hermes_lead.md` |
| `hermes_lead_v02` | `aishuo` | `MiniMax-M3` | `runs/conference/eligibility_vlm_contract_v01_20260711/hermes_lead_v02.md` |

## Main-Venue DeepSeek Pro Review

- Agent/model: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro`.
- Reasoning: maximum configured Reasonix effort. Verify stdout/metrics when possible.
- Forbidden: Hermes, OpenCode Go, Hermes custom providers, or direct DeepSeek provider `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/eligibility_vlm_contract_v01_20260711/main_deepseek_pro.md`

## Timeout And Retry Tracking

- Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used.
- `aishuo/MiniMax-M3` overload is not a reason to switch chair. Retain failure evidence and use a controlled same-route retry.

## Codex Verification Checklist

- No participant read or wrote outside the allowlist and single output path.
- Actual provider/model markers match assigned routes.
- Chair is `aishuo/MiniMax-M3`; no silent fallback.
- No output authorizes real clinical images or medical inference.
- Revised schema is fully closed and cross-field rules are deterministic.
- Production worker remains fail-closed until the explicit implementation gate passes.
