# Codex Execution Plan: mm_r6_runtime_slice_06_final_verify_20260828

Objective: Read-only final verification of the frozen R6 slice-06 synthetic/offline candidate after preserving the original packet governance-audit failure evidence.

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Independently audit final source against the frozen slice-06 contract and conference closures; do not edit. | `runs/execution/mm_r6_runtime_slice_06_final_verify_20260828/worker_01.md` |
| `worker_02` | Run focused/full/optimizer-hash tests against final SHAs and report exact evidence; do not edit. | `runs/execution/mm_r6_runtime_slice_06_final_verify_20260828/worker_02.md` |
| `worker_03` | Verify receipt, medical-writing boundary, stopped ports, and acceptance exclusions; do not edit. | `runs/execution/mm_r6_runtime_slice_06_final_verify_20260828/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

Require exact SHA matches, worker reports with no edits, focused 351/full 728/9-grid evidence, protected medical-writing aggregate, stopped 8911/5174, and no unresolved contract-connected fail-open. This packet verifies the final frozen candidate only; it does not replace or rewrite the preserved original packet audit failure.
