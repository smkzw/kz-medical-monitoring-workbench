# Codex Main-Venue Plan: unified_risk_workbench_visual_20260713

Date: 2026-07-13
Objective: 设计统一项目医学风险核查工作台的三个衔接桌面场景：风险Checklist、原位证据工作区、Safety/PV摘要与PV文档审阅，并形成可直接实施的前端规格

## Task Decomposition

1. Capture the current live desktop workbench and authoritative Timeline/Profile references.
2. Ask each visual participant to independently design all three connected scenes within the current product shell.
3. Round 2 challenges density, evidence hierarchy, state coverage, Chinese clinical semantics, and implementation feasibility.
4. Round 3 returns corrected implementable screen specifications, not generic moodboards.
5. Codex synthesizes one target, builds it in the existing React application, and performs browser comparison/QC against source screenshots.

## Source Packet

- `context/unified_risk_workbench_visual_20260713_conference_context.md`
- Product Design Brief V2 and unified risk-workbench draft listed there.
- Four live 1440x1024 screenshots in `records/active_slices/unified_risk_workbench_20260713/visual_sources/`.
- Authoritative Timeline/Profile HTML references and CMS logo in the same bounded folder.
- Existing `frontend/src/App.jsx`, `frontend/src/styles.css`, and `frontend/AGENTS.md`.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/unified_risk_workbench_visual_20260713/visual_aishuo_minimax.md` |
| `visual_buddy_kimi` | `buddy` | `kimi-k2.7-code` | `runs/conference/unified_risk_workbench_visual_20260713/visual_buddy_kimi.md` |
| `visual_opencode_qwen` | `opencode-go` | `qwen3.7-plus` | `runs/conference/unified_risk_workbench_visual_20260713/visual_opencode_qwen.md` |
| `visual_fallback_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/unified_risk_workbench_visual_20260713/visual_fallback_mimo.md` |
| `visual_last_fallback_kimi26` | `buddy` | `kimi-k2.6` | `runs/conference/unified_risk_workbench_visual_20260713/visual_last_fallback_kimi26.md` |

## Sub-Venue Review

- No sub-venue chair. Codex leads the visual/design panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Record start/end time, session id, all three same-session rounds, provider/model, terminal failure, fallback, and whether output was incorporated.
- Kimi failure fallback order: OpenCode Go `qwen3.7-plus`, then `mimo-v2.5` only if a separate visual role remains uncovered. Do not duplicate the existing Qwen role without documenting the changed assignment.
- Qwen failed after round 1 without a resumable session; MiMo now covers Qwen's skeptical clinical-workflow/density assignment. Qwen remains failed evidence and is not counted as a completed role.
- MiMo then failed under the same terminal condition; Buddy `kimi-k2.6` is the final user-listed visual fallback. If it also fails, Codex proceeds only with completed outputs and explicitly records the reduced panel rather than blind retrying.

## Codex Verification Checklist

- All three outputs inspected the actual screenshots and current code, not filenames alone.
- Three outputs describe the three connected scenes and do not ask the user to choose one of them.
- Checklist, evidence workspace, Timeline, Profile, AE/MH, PD/Finding, source and disposition interactions have explicit focus/back-link semantics.
- CM and investigational-product changes remain separate; each timeline category uses a distinct but restrained color.
- Safety/PV is a read-only projection and collaboration route, not a parallel risk/state store.
- Text density, overflow, fixed dimensions, long Chinese labels and 1440/1920 desktop behavior are testable.
- Codex alone performs final browser comparison and visual acceptance after implementation.
