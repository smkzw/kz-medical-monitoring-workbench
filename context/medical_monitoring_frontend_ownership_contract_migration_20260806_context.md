# Task Context: medical_monitoring_frontend_ownership_contract_migration_20260806

Created: 2026-08-06 05:35:19
Objective: 验证并记录共享 `App.jsx` 中“可删除遗留监查页面”的真实当前状态；仅在有明确活动调用点且不伤害医学写作/活动 feature 路由时迁移。当前审计结论为前提不成立，保留共享壳层，并修复一个因时间线检查实现已更新而失效的静态契约断言。
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

上一份 P0-05 记录基于历史扫描保留了“共享壳层含遗留 Timeline/Profile 定义”的未决项。本次先以当前文件系统为真相重新核对，而不是沿用历史描述直接删除。共享壳层和医学写作属于高影响边界，必须以静态调用点、测试契约和前后哈希共同决定是否可改。

## Source Of Truth

- Workbench root: `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`。
- Frontend boundary: `frontend/AGENTS.md`。
- Shared shell: `frontend/src/App.jsx`, `frontend/src/styles.css`, `frontend/src/main.jsx`。
- Active medical-monitoring feature: `frontend/src/features/medical-monitoring/`。
- Static contracts: `tests/test_frontend_monitoring_contract.py`, `tests/test_frontend_timeline_contract.py`, and the medical-monitoring Node test suite.
- Historical P0-05 evidence: `records/active_slices/medical_monitoring_frontend_ownership_contract_20260806/` and `records/active_slices/medical_monitoring_frontend_legacy_cleanup_20260806/`; historical claims are evidence to reconcile, not authority over current bytes.
- Current audit snapshot: `frontend/src/App.jsx` SHA-256 `de942af37999e708d124c99e1beb47fcd2c405ff23ed83fee6dbcc4cf5e0beed`; `frontend/src/styles.css` SHA-256 `dbd1a99c31cb4877c7f9b13dc8dee7804a39d20a3c0ee805eb4b4a70a76bcefd`.

## Scope

- In scope: read-only reconciliation of current App route/definition tokens; test-only repair of the stale chart-point assertion discovered while re-running the static acceptance suite; durable review/verification evidence.
- Out of scope: changing `frontend/src/App.jsx`, `frontend/src/styles.css`, `frontend/src/main.jsx`, medical-writing files, backend/API/database code, runtime/service/provider/browser/Playwright/login, source-token/CAS/B6/C14, or real-project execution.

## Success Criteria

- Confirm current `App.jsx` has feature-owned Timeline/Profile imports and route mounts, with no `SubjectTimelinePageLegacy`, `PatientProfilePageLegacy`, or local `function SubjectTimelinePage`/`function PatientProfilePage` definitions.
- Do not perform an unjustified shared-shell deletion; preserve the current App/styles/main hashes during this slice.
- Make the Python static assertion describe the current point-entry filtering contract rather than a removed implementation string.
- Focused Python contracts, full medical-monitoring Node suite, syntax/static scans, and listener checks pass; record residual runtime and clinical gates as unverified/blocked.

## Risk Boundaries

- No shared-shell or medical-writing source edits. The only product-adjacent edit permitted here is the focused test assertion in `tests/test_frontend_timeline_contract.py`.
- Keep 8911/5174/8910/4173 stopped. Do not start services, providers, browser, API login, real projects, SQLite/CAS writes, B6/C14 or release gates.
- Do not infer semantic ownership from import presence alone; absence of active call sites is a negative audit, not permission for cleanup without an owner/baseline manifest and independent review.
- Codex is final authority; this record does not claim browser, clinical, scientific, independent-AI, real-LOOP or commercial acceptance.

## Timeout Policy

- This is a bounded direct Codex audit; no delegated agent or external model was dispatched.
- A failed static check must be repaired or explicitly recorded before acceptance. Runtime gates remain blocked by the authoritative real-loop gate.

## Loop Log

- 2026-08-06 05:35:19: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 05:4x: Re-read current App source. Historical “legacy page definitions” were not present in current bytes; only feature-owned imports/mounts and App compatibility helpers remained. No App deletion was justified.
- 2026-08-06 05:5x: Focused Python run exposed one stale exact-string assertion for metric chart filtering. Updated only that assertion to the current `pointEntries` contract; no product source changed.
- 2026-08-06 05:5x: Re-ran focused Python contracts (73 passed), all medical-monitoring Node tests (37 files passed), hash/static/listener checks; no runtime started.
