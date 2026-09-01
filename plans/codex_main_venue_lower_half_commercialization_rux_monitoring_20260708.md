# Codex Main-Venue Plan: lower_half_commercialization_rux_monitoring_20260708

Date: 2026-07-08 CST
Objective: Resume AI medical manager workbench build toward commercial-ready product across all medical-related modules; decide and start the next implementation slice, prioritizing RUX-03-002 real-data medical monitoring rule/event layer while preserving full-module roadmap.

## Task Decomposition

1. Re-anchor current workbench state from logs, source files, tests, and active services.
2. Run parallel advisory review:
   - Hermes participants independently assess next build slice, schema, risks, and tests.
   - Buddy `glm-5.2` reviews Chinese clinical product wording and information architecture risks.
   - Buddy `kimi-k2.7-code` reviews frontend/interaction implications for medical monitoring.
   - Codex SubAgents run read-only maturity, RUX rule-layer, and monitoring frontend audits.
3. Codex compares outputs against current source truth and rejects stale or already-fixed findings.
4. If consensus supports RUX first, write failing tests for RUX P0 data dictionary/rule/event layer.
5. Implement only the smallest RUX backend slice that passes those tests and advances the commercial target.
6. Run focused backend tests, full backend regression, frontend build/QC if UI touched, and update logs.

## Source Packet

- `context/lower_half_commercialization_rux_monitoring_20260708_review_packet.md`
- `context/rux_monitoring_source_precheck_20260708.md`
- `logs/SOFT_PAUSE_20260708_0958_CST.md`
- `logs/system_build_log.md`
- `frontend/AGENTS.md`
- `README.md`
- Current backend/frontend/test files listed in the packet.
- Original RUX files are read-only Codex sources; Hermes uses the precheck unless explicitly assigned.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_mimo.md` |
| `participant_ds_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_ds_flash.md` |
| `participant_glm52_product` | `buddy` | `glm-5.2` | `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_glm52_product.md` |
| `participant_kimi_frontend` | `buddy` | `kimi-k2.7-code` | `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_kimi_frontend.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/lower_half_commercialization_rux_monitoring_20260708/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Provider/model: DeepSeek supplier `deepseek-v4-pro`.
- Reasoning: maximum available effort. Verify logs/usage when possible.
- Forbidden: OpenCode Go `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/lower_half_commercialization_rux_monitoring_20260708/main_deepseek_pro.md`

## Timeout And Retry Tracking

- To be filled after dispatch.

## Codex Verification Checklist

- Preflight prompts before dispatch.
- Verify each model's stdout markers for provider/model/API completion/usage where available.
- Treat slow model outputs as pending, not failed, unless terminal error or timeout policy is met.
- Review all advisory outputs against current source files.
- Before code edits: write failing tests for the chosen behavior.
- After code edits: focused tests, full backend regression, frontend build/QC when applicable, public payload path/hash leak scan.
