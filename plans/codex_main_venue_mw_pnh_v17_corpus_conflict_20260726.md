# Codex Main-Venue Plan: mw_pnh_v17_corpus_conflict_20260726

Date: 2026-07-26
Objective: 仅审查PNH v17完整condition修复、文档校验用户权限边界、语料适应症特异类型化集成的冲突和残余风险，不重复全量审计

## Task Decomposition

1. PNH v17: compare the four v16 failure NCT IDs against the immutable
   ClinicalTrials.gov condition arrays and the new real-AI classifications.
2. Corpus: inspect only the typed finding contract, target-layer construction,
   support assessment call and focused tests.
3. Document validation: inspect only state transitions, explicit override,
   resume/reuse behavior and frontend user-action rendering.
4. Return conflict/risk deltas; no source writes.

## Source Packet

- Conference context and audit journal.
- PNH v16 failure report, immutable snapshot, v17 run/job evidence.
- Corpus policy/AI integration files and focused tests.
- Research-pipeline/API/frontend integration files and focused tests.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/mw_pnh_v17_corpus_conflict_20260726/general_aishuo_cms.md` |
| `general_codebuddy_deepseek_pro` | `codebuddy-cli` | `deepseek-v4-pro` | `runs/conference/mw_pnh_v17_corpus_conflict_20260726/general_codebuddy_deepseek_pro.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_pi_qwen38` | `alibaba` | `qwen3.8-max-preview` | `runs/conference/mw_pnh_v17_corpus_conflict_20260726/general_chair_pi_qwen38.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Start after the two resumed subagent repairs and PNH v17 terminal evidence
  are present.
- One full participant pass each; no status prompts within the hard wait.
- Same-session follow-up only for a specific missing locator or contradiction.

## Codex Verification Checklist

- Confirm declared provider/model/session evidence.
- Review only cited conflict/risk locators.
- Reproduce every proposed blocker with a focused source check or test.
- Do not accept technical completion as scientific correctness.
- Record incorporated/rejected objections and residual risk in the review.
