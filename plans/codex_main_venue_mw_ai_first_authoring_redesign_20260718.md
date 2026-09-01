# Codex Main-Venue Plan: mw_ai_first_authoring_redesign_20260718

Date: 2026-07-18
Objective: 审议医学写作AI前置撰写器重构合同：极简建项、证据化AI预填、正交研究设计、I期复合研究、IB利用、用户采用即确认及人因易用性硬门

## Task Decomposition

1. Audit the independent research contract against the current product state.
2. Challenge the workflow from a first-time, low-patience senior medical writer
   perspective and remove work that does not improve scientific control.
3. Validate Phase I taxonomy/combination boundaries and IB-to-protocol use.
4. Validate content confirmation, audit and future release-state separation.
5. Produce a minimal compatible implementation and test sequence.

## Source Packet

- Current requirement/task record and the 1,413-line research contract.
- Existing project-creation, authoring journey, PICOS, study-definition,
  candidate-adoption and approval-state code.
- Existing rendered journey QC showing the present form burden.
- No raw confidential IB content is sent to conference prompts or web queries.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/mw_ai_first_authoring_redesign_20260718/general_aishuo_cms.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_ai_first_authoring_redesign_20260718/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/mw_ai_first_authoring_redesign_20260718/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Participants start in parallel after prompt preflight.
- Each substantive role uses the guard-defined high turn budget and 120-minute
  hard wait; latency alone is not failure.
- Grok chair starts after both usable participant outputs exist or are terminal.
- Session IDs, fallback and late-output use are recorded in the run reports.

## Codex Verification Checklist

- Verify participant claims against local source and primary regulatory sources.
- Reject any plan that merely adds more form fields or static templates.
- Verify no repeated medical approval after user adoption.
- Verify imported synopsis facts are not re-asked and minimal from-zero facts
  are inherited across all three steps.
- Verify Phase I multi-part choices propagate to PICOS, SoA, chapters and Word.
- Verify IB facts retain source/version and do not silently override user facts.
- Verify measurable usability gates and clean-room real-project E2E scenarios.
