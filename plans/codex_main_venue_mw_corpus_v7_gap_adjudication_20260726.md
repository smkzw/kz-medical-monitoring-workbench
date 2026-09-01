# Codex Main-Venue Plan: mw_corpus_v7_gap_adjudication_20260726

Date: 2026-07-26
Objective: 仅裁决CORPUS_V7_GENERALIZATION_GAP中的G1-G10哪些是上线阻断、哪些可保持fail-closed延后，并把重叠缺口合并为最小修复/测试簇；禁止重复审阅已通过v7/PNH范围

## Task Decomposition

1. Participants independently test current reachability and severity for
   G1-G10 against the same implementation and accepted tests.
2. Distinguish false admission/high confidence from conservative fail-closed
   or low-recall behavior.
3. Chair resolves conflicts and merges root causes into at most four
   repair/test clusters.
4. Codex reads chair conflicts and cited locators, then decides the minimum
   Slice C prerequisite.

## Source Packet

- `records/handoffs/codex_retake_20260726/CORPUS_V7_GENERALIZATION_GAP.md`
- `services/api/app/medical_writing_corpus_analysis_ai.py`
- `services/api/app/medical_writing_corpus_policy.py`
- the two directly corresponding test files
- current v7 integration and 49/40 acceptance evidence listed in context

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/mw_corpus_v7_gap_adjudication_20260726/general_aishuo_cms.md` |
| `general_codebuddy_deepseek_pro` | `codebuddy-cli` | `deepseek-v4-pro` | `runs/conference/mw_corpus_v7_gap_adjudication_20260726/general_codebuddy_deepseek_pro.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_pi_qwen38` | `alibaba` | `qwen3.8-max-preview` | `runs/conference/mw_corpus_v7_gap_adjudication_20260726/general_chair_pi_qwen38.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- One complete participant pass; no status prompts while pending.
- Chair starts after both participant outputs complete or reach terminal
  failure/fallback state.
- Same-session follow-up only for a specific unsupported disposition or
  missing locator.

## Codex Verification Checklist

- Verify route, session and fallback identities.
- Read chair conflicts and locators rather than all participant prose.
- Reproduce only contested negative tests or production locators.
- Reject “all gaps are blockers” without a reachable false-admission mechanism.
- Record merged clusters and Slice C boundary in the audit journal.
