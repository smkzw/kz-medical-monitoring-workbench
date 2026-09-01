# Codex Main-Venue Plan: medical_writing_ctgov_pilot_v2_review_20260712

Date: 2026-07-12
Objective: Review the completed ClinicalTrials.gov protocol corpus pilot v2 through pass7, challenge evidence completeness, safety, rights and production-integration boundaries, and determine the next bounded product step without exposing or translating source text.

## Task Decomposition

1. Verify pass6 manifest, receipts and deterministic replay directly in Codex.
2. Run three independent bounded participant reviews without raw source text.
3. Have exact `aishuo/MiniMax-M3` compare the three outputs as the sole sub-venue chair.
4. Codex adjudicates findings, applies only reproducible pilot corrections, and decides the next product boundary.

## Source Packet

Use only the source list in the conference context. Raw PDFs, API bodies, extracted text and renders are excluded.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/medical_writing_ctgov_pilot_v2_review_20260712/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_writing_ctgov_pilot_v2_review_20260712/general_opencode_mimo.md` |
| `general_buddy_glm` | `buddy` | `glm-5.2` | `runs/conference/medical_writing_ctgov_pilot_v2_review_20260712/general_buddy_glm.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_ctgov_pilot_v2_review_20260712/general_aishuo_minimax.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

Record start/end time, pending/failed/incorporated status, retry reason, session id, all three same-session rounds, actual provider/model markers and whether late outputs were used.

## Codex Verification Checklist

- Pass7 manifest has six selected studies, nine document receipts/analyses and two distinct indication/phase queries.
- Every document receipt revalidates size, `%PDF-` magic and SHA-256.
- All nine pre-translation gates remain blocked and no translation/RAG admission occurred.
- Pass7 runs twice without immutable-manifest drift and verifies AD 453/453 across five pages plus PNH 49/49.
- Pilot unit tests cover runtime-reuse normalization and path traversal rejection.
- No model output is accepted as legal, clinical, regulatory, visual or production authority.
