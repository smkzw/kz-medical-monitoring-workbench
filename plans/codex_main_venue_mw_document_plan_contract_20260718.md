# Codex Main-Venue Plan: mw_document_plan_contract_20260718

Date: 2026-07-18
Objective: Design a production-safe document-level ClinicalTrials.gov protocol chapter planning contract that avoids LLM echo of thousands of span IDs, preserves deterministic complete ordered mapping, stops batch-wide repeated planner failures, and exposes honest progress for AD/PNH/obesity/SLE writing-reference translation.

## Task Decomposition

1. Audit the observed AD failure against planner, validator, batch and progress
   contracts.
2. Compare candidate architectures: LLM span echo, LLM boundary indices,
   deterministic anchor/heading runs with AI confirmation, and hierarchical
   hybrid planning.
3. Specify the preferred request/response schema, deterministic expansion and
   validation rules.
4. Specify document-level failure/fuse/retry behavior and user-visible progress.
5. Define a surgical implementation sequence and high-risk regression tests.

## Source Packet

- Conference context file and active cross-indication task record.
- Production planner, validator and translation-batch source listed in the
  context.
- Fresh AD product evidence summarized in the context; models may inspect the
  referenced local source but must not edit it.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/mw_document_plan_contract_20260718/general_aishuo_cms.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_document_plan_contract_20260718/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/mw_document_plan_contract_20260718/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Participants start once in parallel. Slow output remains pending under the
  current global timeout policy.
- Grok chair starts after participant outputs exist or are explicitly pending.
- Same-session follow-up only if Codex finds a concrete unresolved contract gap.

## Codex Verification Checklist

- Confirm the proposal preserves full ordered coverage without LLM ID echo.
- Confirm document plan generation is one call per immutable identity.
- Confirm failure is persisted once per document and does not fan out per span.
- Confirm Protocol+SAP, repeated headings, unmapped spans and table continuity
  are covered.
- Implement only after source-level review; run focused and broad tests.
- Re-run AD from fresh product search and inspect real plan/chapter/chunk lineage.
