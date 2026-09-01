# Codex Main-Venue Plan: mm_r7_slice07a_progress_ui_visual_acceptance_20260828

Date: 2026-08-28
Objective: 独立审阅修复后的 R7 Slice-07A synthetic 进度界面是否满足中文原生医学监察员的视觉与交互合同；核对最终 v2 失败态层级、ego(lite) DOM/键盘证据、1280 宽屏、R5/R7 同页呈现及最小修复，不修改文件、不运行真实项目、不触碰医学写作，并给出 accept_limited 或 revise。

## Task Decomposition

1. Revalidate the final v2 failed-state still under the current governed visual
   role schema while reusing the original provider session.
2. Confirm the prior F1 hierarchy defect is closed without reopening withdrawn
   or out-of-scope items.
3. Codex runs final deterministic/browser gates and records the limited stamp.

## Source Packet

- Contract, current R7 source, `postfx_r5/` v2 PNG + ego JSON + disclosure,
  and the deterministic shared R5/R7 fixture.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_single_object` | `cursor` | `cursor-grok-4.6` | `runs/conference/mm_r7_slice07a_progress_ui_visual_acceptance_20260828/visual_single_object.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Current guard schema was refreshed after `validate-conference` detected the
  superseded role id. The same provider/model session is resumed; no new model
  session or fallback is permitted for this refresh.

## Codex Verification Checklist

- [x] 195 R7/product Python tests.
- [x] 16 shared-fixture tests.
- [x] 49/49 medical-monitoring frontend files; focused render 61 checks.
- [x] Vite build and ego(lite) 1280/browser interaction evidence.
- [x] Codex inspected the final 1920 v2 render.
- [ ] Current-schema same-session participant report.
