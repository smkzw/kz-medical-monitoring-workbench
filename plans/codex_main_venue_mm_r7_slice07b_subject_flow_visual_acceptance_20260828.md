# Codex Main-Venue Plan: mm_r7_slice07b_subject_flow_visual_acceptance_20260828

Date: 2026-08-28
Objective: 独立审阅医学监查项目/中心受试者阶段流向看板的真实宽屏视觉与交互质量，重点核查阶段先后、分支方向、风险层级、中文可读性、表图联动与不横向溢出；仅使用合成数据，不触碰真实项目与医学写作子系统。

## Task Decomposition

1. Independently inspect the 1920px and 1280px ego(lite) screenshots against the frozen flow contract.
2. Check whether a senior Chinese medical monitor can understand stage order, branching, current/reached counts, medium/high-risk emphasis, and drill-down affordances without reading implementation terminology.
3. Classify findings as release-blocking, adjacent regression, or later visual polish.
4. Codex compares the review with deterministic tests and live ego(lite) observations, remediates any accepted blocking issue, and reruns focused verification.

## Source Packet

- `context/mm_r7_slice07b_subject_flow_visual_acceptance_20260828_conference_context.md`
- Two retained ego(lite) screenshots listed in that context
- Frozen v0.2 + v0.3 §9 contracts
- Current flow page/CSS and focused render test

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_single_object` | `grok-build` | `grok-4.6` | `runs/conference/mm_r7_slice07b_subject_flow_visual_acceptance_20260828/visual_single_object.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Start: after prompt preflight on 2026-08-28 CST.
- Hard wait: 120 minutes; no fixed-interval polling.
- Status, route, session and any fallback are recorded by the runner and later copied to the metrics file.

## Codex Verification Checklist

- Reopen both screenshots at original detail.
- Confirm 1280px and 1920px page overflow is zero in ego(lite).
- Confirm project and center scopes, flow filters, detail expansion and Journey jump.
- Run focused render tests, the full medical-monitoring frontend test set, R5/R7 backend tests, synthetic-fixture tests, and Vite build.
- Preserve 8911 stopped; stop temporary 8978/5176 services after acceptance.
