# Codex Main-Venue Plan: mw_editor_refs_conference_20260715

Date: 2026-07-15
Objective: 从医学经理真实写作视角审阅文档/表格统一富文本与全屏交互、主台垂直空间重构、项目级文献引用和GB/T 7714-2015/Word导出架构

## Task Decomposition

1. Codex verifies current rendered/browser behavior and authoritative external product/API/standard sources.
2. MiniMax-M3 independently reviews medical-manager workflow, information density and failure modes.
3. DeepSeek V4 Flash independently reviews contracts, persistence, citation numbering and Word export architecture.
4. GPT-5.5 chair compares both outputs after they exist and identifies contradictions or missing work.
5. Grok 4.5 receives an independent architecture critique; it is not routed through Hermes and is not chair. Give each call enough internal Agent turns (20 for the current code-and-prompt review). Codex evaluates the first complete pass and stops when it is sufficient; otherwise Codex continues the same session for a bounded challenge or correction pass. Do not hard-code either one external round or mandatory extra rounds.
6. Codex decides implementation, writes source, tests in isolated runtime, performs original-resolution browser and DOCX XML acceptance, and persists the LOOP record.

## Source Packet

See `context/mw_editor_refs_conference_20260715_conference_context.md`. Conference participants do not browse current web and do not perform final visual acceptance.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/mw_editor_refs_conference_20260715/general_aishuo_minimax.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_editor_refs_conference_20260715/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_aishuo_gpt55` | `aishuo-gpt55` | `gpt-5.5` | `runs/conference/mw_editor_refs_conference_20260715/general_chair_aishuo_gpt55.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Participants start independently. Chair starts only after participant outputs exist or are explicitly pending under the timeout policy.
- Record provider/model/session/fallback evidence in `logs/conference/mw_editor_refs_conference_20260715/`.

## Codex Verification Checklist

- Browser: both full-screen modes, every formatting control, state density, no console/API errors.
- Persistence: body and table rich text save/reload across restart.
- Literature: DOI, PMID, PubMed URL and publisher URL import/deduplication/error/override paths.
- Citation: insert/edit/delete/reorder/repeat, references regeneration, project isolation, AI binding validation.
- Word: styles, marks, tables, bookmarks, hyperlinks, references, compatibility for documents without citations.
