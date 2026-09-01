# Codex Main-Venue Plan: mw_reference_translation_batch_phase2_20260716

Date: 2026-07-16
Objective: 设计并实现医学写作竞品Protocol/SAP批量监管中文候选：仅处理内容confirmed或user_overridden且结构审核approved的当前有效片段；保留来源、版本、失败隔离、持久恢复和医学审核门禁；不得自动医学批准或语料准入

## Task Decomposition

1. Reconstruct the accepted phase-1 boundary and inspect existing single-span translation/review/admission contracts.
2. Obtain independent three-round participant reviews, then a three-round GLM chair synthesis.
3. Define the smallest typed batch contract and state machine without widening medical authority.
4. Implement backend persistence/API and frontend `译文审核` batch surface with disjoint tests.
5. Verify focused tests, broad regression, service restart, PNH/RA real projects, and desktop visual state.

## Source Packet

Use the source-of-truth list in `context/mw_reference_translation_batch_phase2_20260716_conference_context.md`. Participants are read-only and must cite concrete files/symbols.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/mw_reference_translation_batch_phase2_20260716/participant_minimax.md` |
| `participant_deepseek_pro` | `buddy` | `deepseek-v4-pro` | `runs/conference/mw_reference_translation_batch_phase2_20260716/participant_deepseek_pro.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/mw_reference_translation_batch_phase2_20260716/participant_mimo.md` |
| `consultant_grok45` | `grok-build` | `grok-4.5` | `runs/conference/mw_reference_translation_batch_phase2_20260716/consultant_grok45.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `chair_glm52` | `buddy` | `glm-5.2` | `runs/conference/mw_reference_translation_batch_phase2_20260716/chair_glm52.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Participants: soft wait 20 minutes, large-task wait 45 minutes.
- Chair: hard wait 90 minutes.
- Slow responses remain pending; retry only after terminal error or hard-wait/no-progress conditions.
- Preserve session IDs and same-session round evidence in `runs/` and `logs/`.

## Codex Verification Checklist

- [ ] Participant prompts pass preflight and all available roles complete three same-session rounds.
- [ ] Chair explicitly compares participant and Grok outputs and challenges consensus.
- [ ] Backend scope is server-derived and double-gated.
- [ ] Batch persistence, idempotency, failed-only retry, and restart recovery are tested.
- [ ] No automatic medical approval or corpus admission route exists.
- [ ] PNH and RA real browser flows pass without stable-runtime writes.
- [ ] Broad regression and production build pass.
