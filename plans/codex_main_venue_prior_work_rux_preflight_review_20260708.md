# Codex Main-Venue Plan: prior_work_rux_preflight_review_20260708

Date: 2026-07-08 CST
Objective: Audit current AI Medical Manager Workbench implementation and preflight the next RUX medical monitoring real-data build; Hermes advisory only, no source edits

## Task Decomposition

1. Freeze the review scope and provide a complete packet before dispatch.
2. Ask three participant models to independently review the same source packet.
3. Ask Hermes lead `minimax-m3` to compare the participants and identify conflicts, accepted recommendations, and rerun needs.
4. Ask DeepSeek supplier `deepseek-v4-pro` to review the Hermes package from the Codex main-venue perspective.
5. Codex will decide whether any recommendation is safe to land. No edits are pre-authorized.

## Source Packet

- `context/prior_work_rux_preflight_review_20260708_review_packet.md`
- `context/rux_monitoring_source_precheck_20260708.md`
- Prior closure records:
  - `logs/SOFT_PAUSE_20260708_0833_CST.md`
  - `logs/system_build_log.md`
  - `reviews/codex_conference_workbench_resume_review_20260708_review.md`
  - `runs/conference/workbench_resume_review_20260708/main_deepseek_pro.md`
- Current implementation files and tests listed in the review packet.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/prior_work_rux_preflight_review_20260708/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/prior_work_rux_preflight_review_20260708/participant_mimo.md` |
| `participant_ds_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/prior_work_rux_preflight_review_20260708/participant_ds_flash.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/prior_work_rux_preflight_review_20260708/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Provider/model: DeepSeek supplier `deepseek-v4-pro`.
- Reasoning: maximum available effort. Verify logs/usage when possible.
- Forbidden: OpenCode Go `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/prior_work_rux_preflight_review_20260708/main_deepseek_pro.md`

## Timeout And Retry Tracking

- To be filled after participant dispatch.
- Slow outputs remain `pending` until the configured hard wait and retry rules are met.

## Codex Verification Checklist

- Preflight all participant/chair/main prompts before dispatch.
- Verify each participant output exists and is not empty/truncated.
- Read Hermes lead and DeepSeek Pro outputs before accepting any recommendation.
- If code changes are later accepted, run focused tests for touched files, full backend regression when feasible, frontend build, and browser QC for affected surfaces.
- For RUX monitoring build, later verification must include original RUX listing/protocol parsing, protocol-derived rule traceability, subject timeline/Patient Profile browser QC, no local path leakage, and independent AI-runtime boundary checks.
