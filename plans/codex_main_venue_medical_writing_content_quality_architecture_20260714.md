# Codex Main-Venue Plan: medical_writing_content_quality_architecture_20260714

Date: 2026-07-14
Objective: 审阅医学写作源内容异常闭环架构：保守确定性检测、正文优先证据、带理由医学确认/纠正、内容指纹失效、审计、working-copy批准阻断、approved-final兜底门禁及编辑器内紧凑交互；基于RUX真实<0}阳性和D001/PNH对照，不修改原始方案

## Task Decomposition

1. Independently challenge deterministic detection and real-project validation boundaries.
2. Independently challenge persistence, fingerprint invalidation, concurrency, audit and idempotency.
3. Independently challenge approval/export bypasses and editor-first interaction.
4. GLM chair compares participants after all available outputs complete and records conflicts/rerun needs.
5. Codex decides the production contract, implements with tests, performs browser acceptance and records rejected advice.

## Source Packet

- `records/active_slices/medical_writing_content_quality_20260714/ARCHITECTURE_REVIEW_PACKET.md`
- `records/active_slices/medical_writing_content_quality_20260714/TASK_RECORD.md`
- `context/medical_writing_content_quality_architecture_20260714_conference_context.md`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_content_quality_architecture_20260714/general_aishuo_minimax.md` |
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/medical_writing_content_quality_architecture_20260714/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_writing_content_quality_architecture_20260714/general_opencode_mimo.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_glm` | `buddy` | `glm-5.2` | `runs/conference/medical_writing_content_quality_architecture_20260714/general_chair_glm.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Record participant start/end time, session id, three-round continuity, terminal failure or fallback, and whether Codex incorporated each recommendation.

## Codex Verification Checklist

- Conference prompt preflight passes with no nonexistent or overbroad read path.
- All participant outputs are independent and all roles complete three rounds in the same session.
- Chair reads participant outputs only after they exist and explicitly compares contradictions.
- Codex verifies every accepted claim against current code and tests before production edits.
- Production implementation proves RUX positive, D001/PNH controls, stale disposition invalidation, draft availability, approval blocking and approved-final backstop.
