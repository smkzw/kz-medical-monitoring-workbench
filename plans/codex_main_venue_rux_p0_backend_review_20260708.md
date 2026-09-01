# Codex Main-Venue Plan: rux_p0_backend_review_20260708

Date: 2026-07-08 CST
Objective: Review the current RUX-03-002 medical monitoring P0 backend implementation and the planned unified inbox integration before any further product-code changes. Identify concrete defects, conflicts, source-boundary issues, test gaps, and safe next changes. Do not edit files.

## Task Decomposition

1. Prepare a bounded review packet for the current RUX P0 backend and planned unified inbox integration.
2. Run parallel Hermes participant review without file edits.
3. Have Hermes lead compare participant outputs and identify accepted/contested recommendations.
4. Run DeepSeek Pro main-venue review after the Hermes lead output is available.
5. Codex decides which recommendations are accepted. No code is landed unless Codex and Hermes agree and a failing test is written first.

## Source Packet

- `context/rux_p0_backend_review_20260708_conference_context.md`
- `context/rux_p0_backend_review_20260708_review_packet.md`
- `records/rux_monitoring_profile_20260708/rux_p0_verification_gates_20260708.md`
- `logs/system_build_log.md`
- `logs/subsystems/medical_monitoring_log.md`
- `KNOWN_ISSUES.md`
- `services/api/app/rux_monitoring_service.py`
- `services/api/app/main.py`
- `services/api/app/workbench_inbox.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_rux_monitoring_service.py`
- `tests/test_workbench_inbox.py`
- `context/hermes_soul_working_copy.md`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/rux_p0_backend_review_20260708/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/rux_p0_backend_review_20260708/participant_mimo.md` |
| `participant_ds_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/rux_p0_backend_review_20260708/participant_ds_flash.md` |
| `participant_glm52_product` | `buddy` | `glm-5.2` | `runs/conference/rux_p0_backend_review_20260708/participant_glm52_product.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/rux_p0_backend_review_20260708/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Provider/model: DeepSeek supplier `deepseek-v4-pro`.
- Reasoning: maximum available effort. Verify logs/usage when possible.
- Forbidden: OpenCode Go `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/rux_p0_backend_review_20260708/main_deepseek_pro.md`

## Timeout And Retry Tracking

Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used in `metrics/rux_p0_backend_review_20260708_conference_metrics.md`.

## Codex Verification Checklist

- Confirm every Hermes output file exists and is not a placeholder.
- Confirm Hermes did not make source edits.
- Check provider/model markers in stdout where available.
- Accept only recommendations tied to source files or packet evidence.
- Before any code change, write a failing test for the accepted next slice.
- After any code change, run focused backend tests, full backend tests when feasible, and update logs/known issues.
