# Task Context: medical_monitoring_diff_snapshot_proof_20260806

Created: 2026-08-06 01:11:37
Objective: 修复医学监查批次 diff 对 full_snapshot_proof 的无条件信任，基于当前批次证据 fail-closed 处理删除，保持项目中立且不启动运行时
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` P0-03：删除/撤回只有在当前批次全量性已证明时才可进入风险迁移。
- `services/api/app/monitoring_batch_diff.py`：`full_snapshot_proven` 控制 removal eligibility。
- `services/api/app/monitoring_batch_repository.py`：不可变 batch state、proof、source binding、normalized rows 和 `load_diff_ready_batch`。
- `services/api/app/monitoring_batch_service.py`：canonical detailed diff orchestration。
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`：真实运行仍 `read_only / blocked`。

## Scope

- In scope: 重新校验 frozen batch 的 full-snapshot proof；让 repository/service 仅在前后批次都具备完整证据时将删除标为 removal-eligible；保留 additions/changes，并输出 blocked deletion evidence。
- Out of scope: 真实导入、来源/批次写入、SQLite migration、provider/AI、风险处置、B6/C14、source-token/CAS、浏览器/Playwright、医学写作。

## Success Criteria

- `load_diff_ready_batch()` 不再仅凭 `state=frozen` 认为全量性已证明；proof 缺失、字段不一致或来源/行/域证据不一致均返回 `full_snapshot_proven=false`。
- `MonitoringBatchService.detailed_diff()` 同时要求 previous/current proof；未证明删除进入 `removal_blocked_keys` 而不是 `removal_eligible_keys`。
- low-level `BatchDiff` 公开 removal eligible/blocked 与 proof 状态，避免旧消费者误把 removed 当作 resolved。
- 既有批次/diff/daily-run 回归、编译与门禁检查通过；工作台 8911/5174/8910/4173 保持停止。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 01:11:37: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: 发现 `MonitoringBatchService.detailed_diff()` 无条件传入 `full_snapshot_proven=True`，与 P0-03 fail-closed 要求冲突。
- 2026-08-06: repository 增加 proof 重验与 `DiffReadyBatch.full_snapshot_proven`；service/repository diff 改为 previous/current 双证据判定。
- 2026-08-06: 聚焦 removal/proof、batch diff/service/repository、canonical route 和 daily-run 回归通过。
