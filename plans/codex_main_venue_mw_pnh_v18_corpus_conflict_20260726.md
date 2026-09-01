# Codex Main-Venue Plan: mw_pnh_v18_corpus_conflict_20260726

Date: 2026-07-26
Objective: 仅审查PNH v18绑定检索条件词修复、文档校验用户权限边界、语料适应症特异类型化集成的冲突和残余风险，不重复全量审计

## Task Decomposition

1. Compare the four documented v16/v17 failure NCT IDs against the immutable
   ClinicalTrials.gov condition arrays and the new v18 real-AI result.
2. Inspect only the v18 effective-condition helper, project-fact propagation,
   material-fact hashing and source-truth reconciliation tests.
3. Inspect only the typed corpus finding contract, target-layer construction,
   support-assessment call and focused tests.
4. Inspect only document-validation waiting states, explicit override,
   idempotent resume/reuse and frontend user actions.
5. Return conflict/risk deltas; no source writes.

## Source Packet

- Conference context and audit journal.
- PNH v16/v17 failure reports, immutable snapshot and v18 run/job/scientific
  evidence.
- v18 triage code plus focused acceptance log.
- Corpus policy/AI integration files plus compact integration evidence.
- Research-pipeline/API/frontend integration files plus the bounded subagent
  handoff and focused tests.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/mw_pnh_v18_corpus_conflict_20260726/general_aishuo_cms.md` |
| `general_codebuddy_deepseek_pro` | `codebuddy-cli` | `deepseek-v4-pro` | `runs/conference/mw_pnh_v18_corpus_conflict_20260726/general_codebuddy_deepseek_pro.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_pi_qwen38` | `alibaba` | `qwen3.8-max-preview` | `runs/conference/mw_pnh_v18_corpus_conflict_20260726/general_chair_pi_qwen38.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Start only after the document-validation subagent is terminal and the real
  PNH v18 run has terminal scientific evidence.
- One full participant pass each; no status prompts inside the hard wait.
- Same-session follow-up only for a specific missing locator or contradiction.

## Codex Verification Checklist

- Confirm declared provider/model/session evidence.
- Review only cited conflict/risk locators.
- Reproduce every proposed blocker with a focused source check or test.
- Do not accept technical completion as scientific correctness.
- Record incorporated and rejected objections plus residual risk.
