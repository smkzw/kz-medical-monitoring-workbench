# Codex Main-Venue Plan: medical_writing_revision_ui_20260708

Date: TODO
Objective: Wire 医学写作 rich editor revision UI to existing revision-thread backend with pending-medical-approval boundaries, Chinese clinical wording review, and browser QC

## Task Decomposition

1. Current-state verification:
   - Confirm backend revision-thread API and tests.
   - Confirm current frontend AI rail is static and not endpoint-wired.
   - Confirm existing Tiptap dependency and editor integration.
2. External/internal design grounding:
   - Use `research/medical_writing_revision_ui_research_20260708.md` and current medical-writing log.
   - Preserve structured protocol authoring, human-in-the-loop review, and audit boundaries.
3. TDD implementation:
   - Add frontend/static contract tests that fail before frontend wiring.
   - Add/extend browser QC to exercise submit and action flow.
   - Implement the smallest React state/actions needed to call existing endpoints and render revision threads.
4. Verification:
   - Run focused medical-writing API/frontend tests.
   - Run browser QC desktop/mobile.
   - Run frontend build and relevant/full regression as time allows.
5. Persistence:
   - Update subsystem and system logs.
   - Fill Codex review/metrics after Hermes/subagent review and Codex verification.

## Source Packet

- `context/medical_writing_revision_ui_20260708_conference_context.md`
- `research/medical_writing_revision_ui_research_20260708.md`
- `logs/subsystems/medical_writing_log.md`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `frontend/tests/medical_writing_manifest_qc.mjs`
- `services/api/app/main.py`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_manifest.py`
- `tests/test_medical_writing_revision_api.py`
- `tests/test_medical_writing_manifest.py`
- `context/medical_writing_revision_api_context.md`
- `reviews/codex_medical_writing_revision_api_review.md`
- `metrics/medical_writing_revision_api_metrics.md`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/medical_writing_revision_ui_20260708/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_writing_revision_ui_20260708/participant_mimo.md` |
| `participant_ds_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/medical_writing_revision_ui_20260708/participant_ds_flash.md` |
| `participant_glm52_product` | `buddy` | `GLM-5.2` | `runs/conference/medical_writing_revision_ui_20260708/participant_glm52_product.md` |
| `participant_kimi_frontend` | `buddy` | `kimi-k2.7-code` | `runs/conference/medical_writing_revision_ui_20260708/participant_kimi_frontend.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/medical_writing_revision_ui_20260708/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Provider/model: DeepSeek supplier `deepseek-v4-pro`.
- Reasoning: maximum available effort. Verify logs/usage when possible.
- Forbidden: OpenCode Go `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/medical_writing_revision_ui_20260708/main_deepseek_pro.md`

## Timeout And Retry Tracking

Record start/end time, pending/failed/incorporated status, retry reason, provider/model stdout markers, and whether late outputs were used in `metrics/medical_writing_revision_ui_20260708_conference_metrics.md`.

## Codex Verification Checklist

- Prompt preflight passes for all dispatched prompts.
- If Buddy routes are unavailable, record exact route failure and continue with available conference outputs rather than silently substituting.
- TDD red step captured before production frontend wiring.
- Focused API tests pass: `tests.test_medical_writing_revision_api`.
- Frontend contract tests pass after implementation.
- Browser QC proves revision submit/action on desktop and mobile.
- Build passes with no new blocking warnings.
- Public UI contains no local absolute paths, lifecycle subsystem names, or formal-output overclaims.
- Codex personally reviews rendered screenshots/metrics before accepting the slice.
