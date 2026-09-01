# Codex Execution Plan: mm_r6_runtime_slice_06_20260828

Objective: Implement and verify the synthetic/offline R6 slice-06 post_lock_pre_cfdi fixed-total outputs exactly under context/medical_monitoring_r6_runtime_slice_06_contract_20260828.md, preserving all accepted slice-01 through slice-05 behavior and boundaries.

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Implement the four post_lock_pre_cfdi payload builders and validators by reusing the existing ModeOutput and Run-gate identity framework. | `runs/execution/mm_r6_runtime_slice_06_20260828/worker_01.md` |
| `worker_02` | Add deterministic positive and fail-closed tests for fixed locked identity, totals, nested identities, cross-output reconciliation, no overwrite, tamper, and mode isolation. | `runs/execution/mm_r6_runtime_slice_06_20260828/worker_02.md` |
| `worker_03` | Run focused/full/optimizer-hash verification, update the slice-06 receipt and allowed documentation only, and return a compact evidence handoff. | `runs/execution/mm_r6_runtime_slice_06_20260828/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

Codex 必须逐行审查差异与失败开放边界，独立重跑 focused/full/9 宫格、邻接、医学写作
aggregate 和端口停止检查；随后完成独立 conference、review-gate、validate-conference、
execution audit。全部通过后才可记录 limited synthetic/offline slice-06 acceptance。
