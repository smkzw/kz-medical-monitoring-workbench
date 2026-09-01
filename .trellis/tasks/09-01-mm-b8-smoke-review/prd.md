# B8 产品冒烟与阶段评审

## Goal

产品 synthetic profile 启动，关键页主力分辨率冒烟，fresh-context 独立评审与用户确认。

## Requirements

- Start the real workbench with the product-native synthetic profile.
- Inspect dashboard, center graph, Subject Workspace/Journey, and progress page in ego(lite) at the primary wide-screen resolution.
- Run one independent fresh-context stage review focused on behavior loss and medical-semantic preservation.

## Acceptance Criteria

- [ ] Core pages load through the real product path and support required drill-down.
- [ ] Screenshot review finds no P0/P1 visual issue.
- [ ] Independent findings are resolved or explicitly accepted, followed by user stage confirmation.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
