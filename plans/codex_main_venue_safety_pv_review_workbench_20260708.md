# Codex Main-Venue Plan: safety_pv_review_workbench_20260708

Date: 2026-07-08 CST cleanup note
Objective: Build the Safety/PV Collaboration P0 review workbench: real MY009/RUX safety sources, candidate signal review actions, durable audit records, PV handoff candidates, frontend workflow, tests and browser QC, without replacing formal PV systems

## Task Decomposition

- Implement bounded Safety/PV candidate-review workbench only.
- Keep all outputs as待医学/PV确认; do not replace PV system, formal safety conclusion, regulatory reporting, E2B, or formal DSUR/IB workflow.
- Accept participant convergence plus Codex tests/browser QC for this P0 slice.
- Exclude Hermes lead and DeepSeek Pro main-venue placeholders from acceptance for this bounded slice.

## Source Packet

- `services/api/app/safety_pv_manifest.py`
- `services/api/app/safety_pv_review_workbench.py`
- `frontend/src/App.jsx`
- `frontend/tests/safety_pv_manifest_qc.mjs`
- `tests/test_safety_pv_manifest.py`
- `tests/test_safety_pv_review_workbench.py`
- `records/visual_qc_20260708/safety_pv_review/safety_pv_manifest_qc.json`
- `metrics/safety_pv_review_workbench_20260708_conference_metrics.md`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/safety_pv_review_workbench_20260708/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/safety_pv_review_workbench_20260708/participant_mimo.md` |
| `participant_ds_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/safety_pv_review_workbench_20260708/participant_ds_flash.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/safety_pv_review_workbench_20260708/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Provider/model: DeepSeek supplier `deepseek-v4-pro`.
- Reasoning: maximum available effort. Verify logs/usage when possible.
- Forbidden: OpenCode Go `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/safety_pv_review_workbench_20260708/main_deepseek_pro.md`

## Timeout And Retry Tracking

- Participant qwen/mimo/DeepSeek Flash completed and were accepted as advisory for bounded P0.
- Hermes lead and DeepSeek Pro were not run and must not be treated as completed.

## Codex Verification Checklist

- Focused Safety/PV backend tests.
- Full backend regression for the slice at the time.
- Frontend build.
- Desktop/mobile-smoke browser QC.
- Formal PV/regulatory safety workflows require a fresh DeepSeek Pro review before implementation or acceptance.
