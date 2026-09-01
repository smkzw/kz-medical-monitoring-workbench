# B4 前端单代化

## Goal

合并为单代 medical-monitoring feature，并只从 App.jsx 抽离医学监查路由和状态。

## Requirements

- Merge the latest usable r7/g6 UI into the feature root and remove superseded r5/root generations.
- Move only medical-monitoring routes and state from `App.jsx` into the feature.
- Preserve a horizontal visit/time axis, typed event/risk markers, source drill-down, and Chinese-native labels.
- Preserve the R7 product setup/progress/result/continuity path and the G6 subject-flow presentation that is already incorporated into the latest R5 page.
- Keep medical-writing imports, state, routes, assets and visible behavior unchanged.
- Keep the feature desktop-first for 1080p-to-4K wide screens; mobile-specific redesign is out of scope.
- Do not redesign medical semantics while moving code: candidate/fact separation, accepted-snapshot identity, risk lifecycle and source provenance remain backend-owned contracts.

## Acceptance Criteria

- [ ] One medical-monitoring frontend generation remains.
- [ ] Frontend tests and Vite build pass.
- [ ] Wide-screen Journey chronology and key risk information are immediately legible.
- [ ] `App.jsx` delegates medical-monitoring route parsing, browser synchronization, project isolation and render selection to the feature boundary without changing medical-writing code.
- [ ] No user-facing r5/r7/g6 generation label or internal implementation term remains.
- [ ] Existing medical-monitoring deep links continue to resolve to project, center, subject, risk, event and source targets.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
