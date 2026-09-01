# Codex Main-Venue Plan: source_registry_frontend_boundary_review_20260708

Date: 2026-07-08 CST
Objective: Review current AI medical manager workbench prior work and the proposed Source Registry frontend boundary fix; decide whether Codex should finish the server-side candidate-id refactor, remove local absolute paths from the frontend bundle, and add tests/QC before landing, without editing production code during review

## Task Decomposition

1. Assemble an advisory-only review packet with current code facts, prior verification, proposed fix, and explicit questions.
2. Run independent Hermes participant reviews against the same bounded source packet.
3. Run Hermes lead synthesis after participant outputs are present.
4. Run DeepSeek supplier `deepseek-v4-pro` main-venue critique of the sub-venue package.
5. Codex adjudicates whether to land the Source Registry/frontend boundary patch.
6. If landed, Codex must run backend tests, frontend build, source/dist path scan, and Source Registry browser QC before closing.

## Source Packet

- `context/source_registry_frontend_boundary_review_20260708_conference_context.md`
- `context/source_registry_frontend_boundary_review_20260708_review_packet.md`
- `logs/system_build_log.md`
- `logs/SOFT_PAUSE_20260708_0905_CST.md`
- `reviews/codex_conference_prior_work_rux_preflight_review_20260708_review.md`
- `metrics/prior_work_rux_preflight_review_20260708_conference_metrics.md`
- `services/api/app/main.py`
- `services/api/app/source_intake.py`
- `packages/contracts/workbench_contracts/models.py`
- `frontend/src/App.jsx`
- `frontend/AGENTS.md`
- `tests/test_source_registry.py`
- `tests/test_contracts.py`
- `frontend/tests/source_registry_qc.mjs`
- `frontend/tests/overview_ai_gateway_qc.mjs`
- `frontend/tests/safety_pv_manifest_qc.mjs`
- `context/hermes_soul_working_copy.md`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/source_registry_frontend_boundary_review_20260708/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/source_registry_frontend_boundary_review_20260708/participant_mimo.md` |
| `participant_ds_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/source_registry_frontend_boundary_review_20260708/participant_ds_flash.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/source_registry_frontend_boundary_review_20260708/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Provider/model: DeepSeek supplier `deepseek-v4-pro`.
- Reasoning: maximum available effort. Verify logs/usage when possible.
- Forbidden: OpenCode Go `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/source_registry_frontend_boundary_review_20260708/main_deepseek_pro.md`

## Timeout And Retry Tracking

- Start times, completion status, API-call markers, and any provider failures are recorded in `logs/conference/source_registry_frontend_boundary_review_20260708/*_stdout.txt` and `metrics/source_registry_frontend_boundary_review_20260708_conference_metrics.md`.
- Slow participants remain pending until terminal evidence exists.

## Codex Verification Checklist

- Prompt preflight passes for every Hermes role.
- Hermes participants write only their assigned output files.
- Codex reads all outputs before accepting recommendations.
- If code is patched:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_source_registry tests.test_contracts -v`
  - `npm run build`
  - `rg -n "/Users/" frontend/src/App.jsx frontend/dist` returns no hits.
  - `frontend/tests/source_registry_qc.mjs` passes against the running app.
  - rerun `frontend/tests/safety_pv_manifest_qc.mjs` if the `提交中` wording is changed.
