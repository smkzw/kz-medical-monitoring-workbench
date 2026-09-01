# B5 产品 synthetic profile

## Goal

把合成 fixture 外置 JSON，并由产品本体 --synthetic profile 加载，替代平行应用。

## Requirements

- Extract useful synthetic fixtures from Python literals into `tests/fixtures/medical_monitoring/` data files.
- Add a product-native `--synthetic` profile that loads those fixtures without a parallel runtime/observer stack.

## Acceptance Criteria

- [ ] Product startup with `--synthetic` produces a deterministic usable smoke dataset.
- [ ] No fixture literal longer than 200 lines remains in product Python code.
- [ ] The profile reuses product runtime, API, and frontend paths.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
