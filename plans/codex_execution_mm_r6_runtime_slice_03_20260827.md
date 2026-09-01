# Codex Execution Plan: mm_r6_runtime_slice_03_20260827

Objective: 按 context/medical_monitoring_r6_runtime_slice_03_contract_20260827.md 实现 synthetic/offline ReportReviewBundle 三件套共享身份、批注锚点门、可选 DRAFT 清洁稿 provenance 与跨修订 IssueTransition/diff；严格限制在合同允许路径，保护 slice-01/02 与医学写作，保持 8911/5174 停止。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现 Bundle/批注投影：共享 identity envelope、issue/evidence/locator 一致性、sidecar 或已证明无损的 in_place_copy、原始字节 hash 保持、matrix/anchor map hash 与 verified anchor 失败关闭门。 | `runs/execution/mm_r6_runtime_slice_03_20260827/worker_01.md` |
| `worker_02` | 实现清洁稿/修订 diff：可选且可见 DRAFT、非 final/非 user-confirmed、before/after 与 issue provenance，IssueTransition merge/split/reclassified 及完整状态迁移，不可比时 not_evaluable。 | `runs/execution/mm_r6_runtime_slice_03_20260827/worker_02.md` |
| `worker_03` | 独立验证：新增正反/tamper/锚点/身份混用/冲突保留测试，normal/-O/-OO 与 3 个 hash seed，相邻回归、医学写作边界和端口停止证据。 | `runs/execution/mm_r6_runtime_slice_03_20260827/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
