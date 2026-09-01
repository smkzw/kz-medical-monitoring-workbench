# Codex Main-Venue Plan: mw_author_end_to_end_20260715

Date: 2026-07-15
Objective: 以中国创新药临床方案医学撰写人员视角实际操作常驻医学写作工作台，审计从新建项目、两阶段反问、竞品Protocol/SAP与语料准备、PICOS、ICH M11章节写作、AI候选、文献引用到DOCX导出的端到端产品断点，并提出可验证的优先修复序列

## Task Decomposition

1. Open the stable desktop product and walk the current project and writing
   navigation without changing persisted state.
2. Compare the visible workflow with the persisted two-stage/dual-entry/corpus
   contracts and identify disconnected transitions.
3. Review the current real-project browser evidence and distinguish obsolete
   assertions from live defects.
4. Produce a prioritized repair/verification sequence; Codex decides and writes
   all production changes.

## Source Packet

The authoritative source packet is listed in
`context/mw_author_end_to_end_20260715_conference_context.md`. Participants may
read only those files and may perform the explicitly authorized read-only stable
browser/API interactions.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/mw_author_end_to_end_20260715/general_aishuo_minimax.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_author_end_to_end_20260715/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/mw_author_end_to_end_20260715/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Record start/end time, pending/failed/incorporated status, retry reason and
  whether late outputs were used in the metrics file.

## Codex Verification Checklist

- Reproduce every accepted P0/P1 defect.
- Reject findings based on stale selectors or old source-readonly semantics.
- Do not mutate the stable runtime during conference review.
- Verify accepted repairs in an isolated runtime before stable restart.
