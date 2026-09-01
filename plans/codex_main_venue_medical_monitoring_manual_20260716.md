# Codex Main-Venue Plan: medical_monitoring_manual_20260716

Date: 2026-07-16
Objective: 编制医学监查子系统全量中文正式说明书，覆盖日常医学监查、锁库前整体医学监查、实时与总结性风险预警、增量diff、Subject Timeline、Patient Profile、AE/MH漏报、PD与CFDI核查前自查，并输出多章节Markdown和康哲规范交互式HTML

## Task Decomposition

1. Build a source/evidence packet separating binding requirements, authoritative guidance, implemented behavior, project examples and design rules.
2. Ask aishuo MiniMax-M3 to produce the complete first manuscript and explicit risk-rule matrix.
3. Apply `humanizer-zh` to remove formulaic AI prose without weakening scientific precision.
4. Run the user-requested Reasonix `deepseek-v4-pro` independent review outside the default conference participant route; record it as an additional advisory review, not final authority.
5. Codex reconciles all findings, verifies abbreviations and clinical boundaries, and writes the canonical multi-chapter Markdown.
6. Generate a single-file interactive HTML book from the canonical content using the Kangzhe streaming-report design rules.
7. Run structural, link, text, browser and visual checks, then update task records and conference review/metrics.

## Source Packet

- `context/medical_monitoring_manual_source_packet_20260716.md`.
- Authoritative local and external sources listed in the conference context.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_monitoring_manual_20260716/general_aishuo_minimax.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/medical_monitoring_manual_20260716/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/medical_monitoring_manual_20260716/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- The standard conference mode has no Reasonix second-review role. The user's explicit request adds a separate Reasonix CLI `deepseek-v4-pro` manuscript review after the first draft and humanization pass; Codex remains final authority.

## Timeout And Retry Tracking

- Record start/end time, provider/model/session id, pending/failed/incorporated status, fallback and late-output handling in the conference metrics.

## Codex Verification Checklist

- Verify all required chapters and workflows are present.
- Verify abbreviation first-use expansions and terminology consistency.
- Verify AE/MH/PD/IP/CM boundaries and configurable-threshold caveats.
- Verify rule tables include trigger, exclusion, evidence and disposition.
- Verify references are authoritative, current and queryable.
- Verify Markdown headings, anchors, tables and internal links.
- Verify HTML official logo embedding, left TOC, search, progress, responsive desktop reading, no overlap/overflow, no external runtime dependencies and no absolute local paths.
- Inspect original-resolution desktop screenshots and test interactions.
