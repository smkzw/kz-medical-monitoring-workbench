# Codex Main-Venue Plan: mw_ad_translation_fidelity_review_20260718

Date: 2026-07-18
Objective: 基于AD真实端到端证据，审阅ClinicalTrials.gov方案翻译、Flash整合QC与确定性忠实度门的架构，区分真实翻译缺陷与规则假阳性，提出不降低科学性和监管规范性的可执行修复与复测方案

## Task Decomposition

1. Participants independently audit the complete v10 evidence and code path.
2. Each classifies true translation defects versus deterministic false
   positives and proposes a fail-closed remediation.
3. Grok chair compares participant findings, resolves conflicts and identifies
   missing evidence.
4. Codex verifies recommendations against source/code, implements only
   supported changes, reruns focused tests and fresh AD E2E.

## Source Packet

- Conference context and active task record.
- v10 lane report and `translation_fidelity_evidence.json`.
- Production adapters, document pipeline, batch orchestration and deterministic
  fidelity implementation.
- E2E gate source and current gate definitions.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/mw_ad_translation_fidelity_review_20260718/general_aishuo_cms.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_ad_translation_fidelity_review_20260718/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/mw_ad_translation_fidelity_review_20260718/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Participant pass start: pending.
- Do not poll frequently; use the 120-minute hard wait and same-session recovery
  policy from the conference context.
- Chair starts after available participant reports are complete or explicitly
  terminal; a slow participant remains pending.

## Codex Verification Checklist

- Reproduce every claimed false positive with the v10 text.
- Do not remove a fidelity code solely because a model labels it noisy.
- Add regression fixtures for HTML markup, Chinese measure words, `周岁`,
  citation/section numbering and clinically material comparator/unit changes.
- Require a fresh isolated AD E2E after code changes.
- Confirm stable runtime hash invariance and archive conference records.
