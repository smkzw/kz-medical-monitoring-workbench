# Codex Main-Venue Plan: safety_pv_dual_project_parity_20260713

Date: 2026-07-13
Objective: 基于MY009与RUX真实来源补齐安全信号与PV协同双项目全链路、来源版本、五动作、handoff与桌面验收

## Task Decomposition

1. Generalize deterministic listing layout/domain/field alias parsing and bind RUX real listing into its package.
2. Add RUX listing to source registry/admission requirements while preserving MY009 actual-source alignment.
3. Prove both manifests and all candidates against real files without making formal PV conclusions.
4. Run all five actions, source drift, restart persistence and handoff for both projects.
5. Rebuild desktop E2E around project switching and every visible control; route any visual changes through a separate visual conference.
6. Run focused/full regression, build, browser inspection, conference review and durable logs.

## Source Packet

See `context/safety_pv_dual_project_parity_20260713_conference_context.md` and `records/research/safety_pv_dual_project_20260713/EXTERNAL_AND_LOCAL_BASELINE.md`.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/safety_pv_dual_project_parity_20260713/general_aishuo_minimax.md` |
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/safety_pv_dual_project_parity_20260713/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/safety_pv_dual_project_parity_20260713/general_opencode_mimo.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_glm` | `buddy` | `glm-5.2` | `runs/conference/safety_pv_dual_project_parity_20260713/general_chair_glm.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

Record runner JSON duration, return codes, session ids, fallback and late-output incorporation in the conference metrics file.

## Codex Verification Checklist

- Inspect original RUX/MY009 workbook structures read-only.
- Verify public payload contains no local path, source hash or forbidden formal-PV claims.
- Test source admission and every state transition for both projects.
- Test source version drift and stale handoff removal.
- Run desktop Chrome at 1600x1000 and 1920x1080; inspect original screenshots.
- Run frontend build and full repository pytest suite.
