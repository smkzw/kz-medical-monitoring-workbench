# B3 巨型文件拆分

## Goal

拆分新链医学监查巨型路由/评估器，保持医学写作和旧 monitoring_* 冻结。

## Requirements

- Split the R7 product router into cohesive domain routers and mount them through one thin API entry.
- Split migrated 5000+ line evaluators by cohesive risk domain.
- Keep files within the 800-line target and 1500-line hard limit unless a documented generated/vendor exception applies.

## Acceptance Criteria

- [ ] Medical-monitoring route logic no longer lives in `main.py` or one multi-thousand-line factory.
- [ ] Public routes and behavior tests remain compatible.
- [ ] Medical-writing route mounts are byte-for-byte unchanged unless separately authorized.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
