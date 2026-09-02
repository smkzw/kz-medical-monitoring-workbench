# B2 后端分层迁移

## Goal

按 domain→graph→intelligence→risks→projections→reports→runtime→api 搬迁，行为变更与搬迁分离。

## Requirements

- Move code in the order domain, graph, intelligence, risks, projections, reports, runtime, API.
- For each layer, migrate tests, update imports, run focused behavior tests, and commit before the next layer.
- Preserve behavior; defer redesign and optimization to separate commits.

## Acceptance Criteria

- [ ] Product medical-monitoring imports resolve only through `packages/medical_monitoring`.
- [ ] Migrated behavior tests pass after each layer.
- [ ] No medical-writing or frozen legacy `monitoring_*` behavior changes.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
