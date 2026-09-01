# Codex Main-Venue Plan: eligibility_evidence_review_vertical_20260711

Date: 2026-07-11
Objective: 设计并评审D001与MY009真实原始资料从OCR/文本证据到逐条IN/EX独立AI初审、医学确认和审计持久化的生产级垂直切片

## Task Decomposition

1. Independently review current source/rule identity and stale-source risks.
2. Design evidence extraction/revision objects for PDF/image/DOC/DOCX with archive fail-closed.
3. Define task-specific independent AI output schema and deterministic validation.
4. Define unambiguous IN/EX medical decision states and overall aggregation.
5. Define SQLite v6 transactions, CAS, idempotency, restart and audit behavior.
6. Define desktop criterion-review interaction and slow cross-project response guard.
7. Define the six-subject real-project and adversarial test matrix.
8. Hermes chair compares participants; Reasonix DeepSeek Pro adjudicates high-risk conflicts; Codex authorizes or revises implementation.

## Source Packet

- `context/eligibility_evidence_review_vertical_20260711_conference_context.md`
- `records/active_slices/eligibility_next_slice_20260711/CONFERENCE_SOURCE_PACKET.md`
- `records/active_slices/eligibility_next_slice_20260711/INDEPENDENT_BACKEND_AUDIT.md`
- `records/active_slices/eligibility_next_slice_20260711/INDEPENDENT_FRONTEND_AUDIT.md`
- Current code files explicitly listed in the conference context.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/eligibility_evidence_review_vertical_20260711/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/eligibility_evidence_review_vertical_20260711/participant_mimo.md` |
| `participant_ds_flash` | `reasonix-cli` | `deepseek-v4-flash` | `runs/conference/eligibility_evidence_review_vertical_20260711/participant_ds_flash.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/eligibility_evidence_review_vertical_20260711/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Agent/model: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro`.
- Reasoning: maximum configured Reasonix effort. Verify stdout/metrics when possible.
- Forbidden: Hermes, OpenCode Go, Hermes custom providers, or direct DeepSeek provider `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/eligibility_evidence_review_vertical_20260711/main_deepseek_pro.md`

## Timeout And Retry Tracking

Record start/end time, provider/model stdout markers, API calls/tokens, pending/failed/incorporated status, retry reason and whether late output was used. Slow output remains pending under the conference timeout policy.

## Codex Verification Checklist

- [ ] All participant prompts pass bounded read/write preflight.
- [ ] No participant reads raw patient files or legacy conclusions.
- [ ] Rule/source/extraction/state revisions and 409 behavior are explicit.
- [ ] AI output schema covers every top-level rule and binds evidence ids.
- [ ] IN and EX decisions are semantically unambiguous.
- [ ] OCR incomplete vs no-evidence states are distinct.
- [ ] D001/MY009 six-subject matrix covers restart, idempotency, drift and cross-project isolation.
- [ ] Frontend preserves desktop hierarchy and clears stale project state.
- [ ] No production code is changed before Codex accepts the gate.
