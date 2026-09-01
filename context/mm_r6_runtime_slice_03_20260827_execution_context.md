# Execution Context: mm_r6_runtime_slice_03_20260827

Created: 2026-08-27 22:57:37
Objective: 按 context/medical_monitoring_r6_runtime_slice_03_contract_20260827.md 实现 synthetic/offline ReportReviewBundle 三件套共享身份、批注锚点门、可选 DRAFT 清洁稿 provenance 与跨修订 IssueTransition/diff；严格限制在合同允许路径，保护 slice-01/02 与医学写作，保持 8911/5174 停止。
Task type: `finite_code_task`
Risk: `medium`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `cursor` / `cursor-cli` / `auto`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- TODO: Codex must add authoritative source files, screenshots, datasets, or URLs before dispatch.
- Do not add production paths without explicit Codex authorization.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. 实现 Bundle/批注投影：共享 identity envelope、issue/evidence/locator 一致性、sidecar 或已证明无损的 in_place_copy、原始字节 hash 保持、matrix/anchor map hash 与 verified anchor 失败关闭门。
2. 实现清洁稿/修订 diff：可选且可见 DRAFT、非 final/非 user-confirmed、before/after 与 issue provenance，IssueTransition merge/split/reclassified 及完整状态迁移，不可比时 not_evaluable。
3. 独立验证：新增正反/tamper/锚点/身份混用/冲突保留测试，normal/-O/-OO 与 3 个 hash seed，相邻回归、医学写作边界和端口停止证据。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
