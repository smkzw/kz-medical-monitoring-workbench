# B7 测试归一与清理

## Goal

迁移行为测试，删除冻结哈希 pinning、optimizer/hash-seed 门与平行应用测试。

## Requirements

- Remove whole-file frozen SHA pinning, digest-refresh gates, optimizer/hash-seed matrices, and tests whose only subject is the deleted parallel app.
- Retain behavioral digest validation, identity/lifecycle semantics, and representative synthetic behavior tests.

## Acceptance Criteria

- [ ] Test suite contains no whole-file hash pinning for migrated monitoring code.
- [ ] Normal focused and integration runs pass without digest refresh steps.
- [ ] Medical semantic contracts retain explicit behavior coverage.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
