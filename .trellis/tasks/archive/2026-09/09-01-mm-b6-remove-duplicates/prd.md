# B6 删除平行应用与 POC 副本

## Goal

迁移测试全绿后删除 deploy/medical_monitoring_local 与八棵 poc 工作副本，git 可恢复。

## Requirements

- Verify all live imports and tests are detached from `deploy/medical_monitoring_local` and eight POC trees.
- Delete those versioned working copies only after the new package tests pass.

## Acceptance Criteria

- [ ] Repository search finds no live product import from deleted trees.
- [ ] Migrated tests pass after deletion.
- [ ] Git history can restore every deleted file.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
