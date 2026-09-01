# B4 前端单代化

## Goal

合并为单代 medical-monitoring feature，并只从 App.jsx 抽离医学监查路由和状态。

## Requirements

- Merge the latest usable r7/g6 UI into the feature root and remove superseded r5/root generations.
- Move only medical-monitoring routes and state from `App.jsx` into the feature.
- Preserve a horizontal visit/time axis, typed event/risk markers, source drill-down, and Chinese-native labels.

## Acceptance Criteria

- [ ] One medical-monitoring frontend generation remains.
- [ ] Frontend tests and Vite build pass.
- [ ] Wide-screen Journey chronology and key risk information are immediately legible.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
