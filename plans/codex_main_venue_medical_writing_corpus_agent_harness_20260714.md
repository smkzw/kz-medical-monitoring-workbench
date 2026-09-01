# Codex Main-Venue Plan: medical_writing_corpus_agent_harness_20260714

Date: 2026-07-14
Objective: 评估扩大临床试验方案语料与有边界Agent harness能否在不引入竞品污染、事实漂移和不可复现性的前提下降低中文注册方案的从零生成比例与医学修改量，并收敛三真实项目A/B/C试验和生产路由边界

## Task Decomposition

1. Verify current architecture, prior ClinicalTrials.gov implementation, user-supplied repositories, relevant local skills, and primary external standards.
2. Define source tiers, corpus admission/use boundaries, conservative regulatory-language lint, and deterministic-vs-one-shot-vs-Agent task routing.
3. Have three independent participants challenge the evidence and the locked three-project A/B/C protocol from clinical-language, corpus-governance, experiment-design, and runtime-architecture perspectives.
4. Have GLM-5.2 compare completed outputs and explicitly identify false consensus, missing controls, and reruns.
5. Codex decides the final pilot design, runs the external-AI comparison without production writes, independently verifies outputs, and records the product decision.

## Source Packet

- `records/active_slices/medical_writing_corpus_agent_harness_20260714/TASK_RECORD.md`
- `records/active_slices/medical_writing_corpus_agent_harness_20260714/EVIDENCE_AND_ARCHITECTURE_REVIEW.md`
- `records/active_slices/medical_writing_corpus_agent_harness_20260714/ABC_PILOT_PROTOCOL.md`
- `records/research/medical_writing_ctgov_protocol_corpus_20260711/PRODUCTION_FEATURE_DECISION.md`
- `records/active_slices/medical_writing_competitor_corpus_20260712/TASK_RECORD.md`
- `services/api/app/ai_gateway.py`
- `services/api/app/ai_execution_policy.py`
- `services/api/app/medical_writing.py`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_corpus_agent_harness_20260714/general_aishuo_minimax.md` |
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/medical_writing_corpus_agent_harness_20260714/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_writing_corpus_agent_harness_20260714/general_opencode_mimo.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_glm` | `buddy` | `glm-5.2` | `runs/conference/medical_writing_corpus_agent_harness_20260714/general_chair_glm.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Record start/end time, provider/model/session id, round count, pending/failed/incorporated status, retry reason, fallback, and whether late output was used.
- Start the three participants in parallel. Start GLM only after the available participant outputs are complete or explicitly excluded under the failure rule.

## Codex Verification Checklist

- Preflight every prompt after source-list and role edits.
- Verify same-session continuation evidence for all three rounds.
- Check that no participant modified source/production files or claimed final medical approval.
- Compare participant recommendations against the actual AI gateway and current intake boundary.
- Run the locked three-project A/B/C pilot using independent external AI, not Codex-authored candidate text.
- Verify run manifests, deterministic metrics, target-gold exclusion, source citations, randomization, and blinded labels.
- Update task record, subsystem/system logs, metrics, Codex review, conference validation, and archive temporary Hermes sessions.
