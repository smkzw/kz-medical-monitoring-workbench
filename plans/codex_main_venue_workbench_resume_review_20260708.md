# Codex Main-Venue Plan: workbench_resume_review_20260708

Date: 2026-07-08 CST
Objective: Review AI Medical Manager Workbench resume-state changes, source registry/eligibility/dashboard public API boundaries, and overview inbox visibility before further commercialization build

## Task Decomposition

1. Re-anchor resume state from soft-pause logs and current runtime.
2. Reproduce and fix overview inbox truncation where all-phase eligibility actions crowded out source/data-health/handoff signals.
3. Dispatch bounded Hermes participants for independent review of previous work, API boundary risks, inbox recovery, and next-loop priority.
4. Run Hermes lead and DeepSeek supplier `deepseek-v4-pro` main-venue review.
5. Apply only Codex/Hermes consensus or main-venue accepted low-risk fixes.
6. Verify with live API checks, focused tests, full regression, frontend build, and browser QC.
7. Persist system/subsystem/conference logs and produce a soft-pause recovery note.

## Source Packet

- `context/workbench_resume_review_20260708_review_packet.md`
- `logs/SOFT_PAUSE_20260708_0640_CST.md`
- `logs/system_build_log.md`
- `logs/subsystems/project_dashboard_log.md`
- `logs/subsystems/module_scope_log.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/main.py`
- `services/api/app/source_intake.py`
- `services/api/app/workbench_inbox.py`
- `services/api/app/enrollment_adapter.py`
- `services/api/app/eligibility.py`
- `services/api/app/demo_repository.py`
- `frontend/AGENTS.md`
- `frontend/src/App.jsx`
- `frontend/tests/overview_ai_gateway_qc.mjs`
- `tests/test_source_registry.py`
- `tests/test_workbench_inbox.py`
- `tests/test_eligibility_adapter.py`
- `tests/test_contracts.py`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/workbench_resume_review_20260708/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/workbench_resume_review_20260708/participant_mimo.md` |
| `participant_ds_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/workbench_resume_review_20260708/participant_ds_flash.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/workbench_resume_review_20260708/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Provider/model: DeepSeek supplier `deepseek-v4-pro`.
- Reasoning: maximum available effort. Verify logs/usage when possible.
- Forbidden: OpenCode Go `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/workbench_resume_review_20260708/main_deepseek_pro.md`

## Timeout And Retry Tracking

- `participant_qwen_plus`: completed; incorporated.
- `participant_mimo`: completed; incorporated.
- `participant_ds_flash`: completed; incorporated.
- `hermes_lead`: completed; incorporated.
- `main_deepseek_pro`: completed; incorporated.
- No participant was failed for slowness. Optional Hermes-studio MCP startup failures during lead did not affect file review.

## Codex Verification Checklist

- Focused backend tests: passed, 39 tests OK after final edit round.
- Full backend regression: passed, 114 tests OK.
- Frontend build: passed with known Vite chunk-size warning.
- Live API V1: `/workbench-inbox?limit=80` returned all required item types with 99 total open items and 80 visible items.
- Live API V2: `/sources`, `/eligibility`, `/workbench-inbox`, and `/api/health` did not expose `/Users/`, hash fields, storage/server paths, source record ids, or data paths.
- Browser QC: passed at `records/visual_qc_20260708/overview_after_deepseek_review/overview_ai_gateway_qc.json`; desktop/mobile no overflow, no forbidden lifecycle/non-medical/EDC visible wording, read-state click reduced unread count by 1.

## Retrospective Note

This plan was completed after participant dispatch because DeepSeek Pro identified that the guard-created template still contained placeholders during the conference. The review artifacts record that process gap; this file is now completed for continuation and handoff.
