# Codex Main-Venue Plan: medical_writing_ai_change_application_20260713

Date: 2026-07-13
Objective: 实现医学写作AI建议经医学批准后显式、可追溯、CAS安全地应用到版本化工作副本，并用RUX、D001、PNH真实方案完成前后端验证

## Task Decomposition

1. Add a narrow application request/result contract and backend repository method.
2. Apply only the accepted suggestion from a medically approved thread to the exact locator-bound content block under working-copy CAS.
3. Persist the new working-copy revision, immutable snapshot and explicit thread/suggestion audit relationship atomically.
4. Add a frontend action in the existing AI rail, with disabled-state reasons and post-apply editor refresh.
5. Run destructive contract tests, three real-project isolated API loops, build and in-app browser desktop QC.
6. Compare conference advice with observed implementation/test/browser evidence; accept only compatible recommendations.

## Source Packet

Read-only file list and success criteria are defined in `context/medical_writing_ai_change_application_20260713_conference_context.md`.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_ai_change_application_20260713/general_aishuo_minimax.md` |
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/medical_writing_ai_change_application_20260713/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_writing_ai_change_application_20260713/general_opencode_mimo.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_glm` | `buddy` | `glm-5.2` | `runs/conference/medical_writing_ai_change_application_20260713/general_chair_glm.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Pending. No participant is failed merely for latency.

## Codex Verification Checklist

- Precondition matrix covers every non-approved state and cross-project identity.
- CAS conflict and idempotent replay are tested.
- Locator-bound single replacement preserves block order, non-text fields and source locators.
- Original document-session content remains byte-for-byte equivalent at the model payload level.
- RUX, D001 and PNH each complete one successful isolated application from their own real document service.
- Frontend control is unavailable before approval and refreshes to the resulting saved revision after success.
- 2048x1024 desktop page has no overlap, page-level horizontal overflow or console errors.
