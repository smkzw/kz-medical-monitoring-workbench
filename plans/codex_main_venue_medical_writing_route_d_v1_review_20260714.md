# Codex Main-Venue Plan: medical_writing_route_d_v1_review_20260714

Date: 2026-07-14
Objective: Reconcile the original participant findings with the remediated Route D v1 implementation and SYN-RA-201 greenfield pilot, then issue a bounded pilot/production decision.

## Task Decomposition

1. Preserve the three independent Round-3 participant outputs as the pre-remediation review baseline.
2. Verify and remediate confirmed controller/schema/provenance defects without changing the production route.
3. Run a genuinely greenfield RA workflow from synthetic sponsor brief and frozen public evidence through Word rendering.
4. Compare direct structured model invocation with a bounded Agent harness for one nontrivial sentence gap.
5. Ask GLM-5.2 chair to reconcile stale versus remaining findings in three same-session rounds.
6. Codex reruns tests, compile checks, document structural checks, and performs the final pilot/production gate.

## Source Packet

- Route D source profiles, schemas, expression library, builder, controller, runner, tests, rebuilt pilot manifests and three-stage probe archive.
- Corpus/Agent architecture decision records and Fact Pack v2 terminology-lock specification.
- SYN-RA-201 synthetic brief, frozen evidence manifest, competitor/decision/draftability matrices, bounded gap harness, direct/Agent comparison, v0.2 candidate and DOCX tests.
- Three participant outputs, GLM chair output, runner/session evidence, Codex review and conference metrics.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_route_d_v1_review_20260714/general_aishuo_minimax.md` |
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/medical_writing_route_d_v1_review_20260714/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_writing_route_d_v1_review_20260714/general_opencode_mimo.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_glm` | `buddy` | `glm-5.2` | `runs/conference/medical_writing_route_d_v1_review_20260714/general_chair_glm.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- All three participants completed Round 3 in resumable sessions and were incorporated.
- Teardown `event loop is closed` warnings occurred after substantive outputs were persisted; they are recorded as tool cleanup noise, not participant failure.
- GLM-5.2 chair completed three same-session rounds. The outer runner interruption/resume and exact final-content restoration are recorded in conference metrics.

## Codex Verification Checklist

- [x] Participant outputs preserved and read.
- [x] Applicability, binding, source-span, hash, metric, and probe-history findings checked and remediated.
- [x] RUX/PNH/MY009 complete; D001 blocks before model call.
- [x] SYN-RA-201 greenfield v0.2 generated and rendered; six pages inspected by Codex.
- [x] Direct/API and Agent routes compared under one exact contract.
- [x] GLM-5.2 chair completes three same-session rounds.
- [x] Full isolated test suites and compileall rerun after final record/test changes.
- [x] Codex production-boundary verdict.
- [x] Parent writing/system continuation logs and temporary-session archival.
