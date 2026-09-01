# Codex Main-Venue Plan: medical_writing_competitor_corpus_production_20260712

Date: 2026-07-12
Objective: Review the production implementation slice for a usable ClinicalTrials.gov competitor protocol corpus integrated into medical writing, including discovery, document security/versioning, structured extraction, independent-AI regulatory Chinese translation, medical approval, source-constrained retrieval, and editor interaction.

## Task Decomposition

1. Review the current writing editor, runtime store, AI gateway and Pilot V2 evidence.
2. Challenge the proposed production state machine, lineage and independent-AI boundaries.
3. Define the smallest TDD slice that creates usable discovery-to-medical-review behavior without bypassing gates.
4. Define editor-side evidence discovery, review and citation interactions.
5. Define two-real-project and failure-path acceptance before production-ready status.

## Source Packet

- Product authorization and acceptance record.
- Pilot V2 reproducibility and evidence-boundary review.
- Existing production writing, persistence and AI gateway implementations.
- Existing editor-first medical-writing interaction.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/medical_writing_competitor_corpus_production_20260712/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_writing_competitor_corpus_production_20260712/general_opencode_mimo.md` |
| `general_buddy_glm` | `buddy` | `glm-5.2` | `runs/conference/medical_writing_competitor_corpus_production_20260712/general_buddy_glm.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_competitor_corpus_production_20260712/general_aishuo_minimax.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

TODO: Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used.

## Codex Verification Checklist

- Contract/state transitions are explicit and fail closed.
- Unapproved versus approved retrieval is testable.
- AI tasks are provider-independent and schema-validated.
- Version replacement invalidates downstream derived content.
- No raw source text/path/model secret leaks through public responses.
- At least two real indication/phase flows and all failure branches are defined.
