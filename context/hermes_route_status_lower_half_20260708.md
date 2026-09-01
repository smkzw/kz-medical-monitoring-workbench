# Hermes Route Status - lower_half_commercialization_rux_monitoring_20260708

## Purpose

This note records route status for the current Codex-chaired conference so the Hermes chair and DeepSeek Pro reviewer can distinguish product findings from provider/runtime incidents.

## Participant Status

Completed participant outputs:

- `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_qwen_plus.md`
- `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_mimo.md`
- `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_ds_flash.md`
- `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_glm52_product.md`
- `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_kimi_frontend_retry.md`

Supporting subagent reports:

- `runs/subagents/module_maturity_audit_current_20260708.md`
- `runs/subagents/monitoring_frontend_interaction_audit_20260708.md`
- `runs/subagents/rux_monitoring_rule_layer_review_20260708.md`

## Kimi Route Incident

- First full-context Kimi run:
  - Prompt: `prompts/conference/lower_half_commercialization_rux_monitoring_20260708/participant_kimi_frontend.md`
  - Stdout: `logs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_kimi_frontend_stdout.txt`
  - Result: failed with supplier HTTP 400 / invalid request parameters.
  - Interpretation: route/size/request incident, not a product finding.
- Kimi minimal smoke:
  - Stdout: `logs/conference/lower_half_commercialization_rux_monitoring_20260708/kimi_route_smoke_stdout.txt`
  - Result: returned `KIMI_ROUTE_OK`.
  - Interpretation: the `kimi-k2.7-code` route is not globally unavailable.
- Compact Kimi retry:
  - Prompt: `prompts/conference/lower_half_commercialization_rux_monitoring_20260708/participant_kimi_frontend_retry.md`
  - Output: `runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_kimi_frontend_retry.md`
  - Stdout: `logs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_kimi_frontend_retry_stdout.txt`
  - Result: completed successfully after four API calls.

## Codex Handling Rule

The Hermes chair should use the compact Kimi retry as the valid frontend Buddy participant output. The first full-context failure should be counted in metrics as a route incident and should not be interpreted as disagreement with the product architecture.

