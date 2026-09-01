# Codex Main-Venue Plan: eligibility_vlm_runtime_v12_20260711

Date: 2026-07-11
Objective: Review the additive SQLite v12 durable VLM runtime foundation, identify remaining release-blocking defects, and define the next bounded circuit/identity slice without opening production VLM or using real clinical images.

## Task Decomposition

1. Three independent participants inspect the same bounded source packet without reading each other.
2. The required `aishuo/MiniMax-M3` Hermes chair compares the available outputs and current code.
3. Reasonix `deepseek-pro` challenges the chair package.
4. Codex verifies every accepted defect in source/tests, applies any required fix and reruns focused plus full regression.

## Source Packet

The source-of-truth list in the conference context plus the participant outputs. No real clinical source folder or image is part of this conference.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/eligibility_vlm_runtime_v12_20260711/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/eligibility_vlm_runtime_v12_20260711/participant_mimo.md` |
| `participant_ds_flash` | `reasonix-cli` | `deepseek-v4-flash` | `runs/conference/eligibility_vlm_runtime_v12_20260711/participant_ds_flash.md` |
Antigravity is excluded because this is not a visual conference.

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `aishuo` | `MiniMax-M3` | `runs/conference/eligibility_vlm_runtime_v12_20260711/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Agent/model: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro`.
- Reasoning: maximum configured Reasonix effort. Verify stdout/metrics when possible.
- Forbidden: Hermes, OpenCode Go, Hermes custom providers, or direct DeepSeek provider `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/eligibility_vlm_runtime_v12_20260711/main_deepseek_pro.md`

## Timeout And Retry Tracking

Record start/end time, actual provider/model markers, pending/failed/incorporated status, retry reason, and whether late outputs were used in metrics.

## Codex Verification Checklist

- Verify participant and chair prompts with preflight.
- Verify actual `aishuo/MiniMax-M3` provider/model markers.
- Reproduce accepted P0/P1 findings locally.
- Run focused VLM/evidence/migration tests, Ruff, full regression and frontend build.
- Keep production launcher and public raw-source VLM API disabled.
