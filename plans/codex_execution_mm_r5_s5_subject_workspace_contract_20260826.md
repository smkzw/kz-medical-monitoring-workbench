# Codex Execution Plan: mm_r5_s5_subject_workspace_contract_20260826

Objective: Freeze and independently verify the renderer-neutral R5-S5 Subject Workspace and Patient Journey implementation contract now that both public-authority producers are accepted, while keeping 8911 stopped and medical-writing untouched.

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Design and generate the exact S5 typed contract and source-to-leaf authority mapping from the accepted R5 v0.3 stage contract plus accepted S1-S4 and public-authority producers. | `runs/execution/mm_r5_s5_subject_workspace_contract_20260826/worker_01.md` |
| `worker_02` | Build the deterministic verifier, challenge registry, negative/replay gates, and frozen source/path hashes for the exact S5 contract without creating S5 runtime. | `runs/execution/mm_r5_s5_subject_workspace_contract_20260826/worker_02.md` |
| `worker_03` | Independently audit the frozen S5 contract for deferred authority, fail-open mappings, temporal/domain/history identity gaps, protected boundaries, and exact unlock conditions. | `runs/execution/mm_r5_s5_subject_workspace_contract_20260826/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

Codex must verify generator determinism and `--check`, verifier normal/`-O`/`-OO`,
exact source hashes, zero deferred core leaves, challenge realization, forbidden
semantic branches, future-runtime absence, protected medical-writing inventory,
and stopped 8911. A fresh isolated conference must accept the immutable contract
before any S5 runtime path is created. Visual/browser checks are not applicable to
this renderer-neutral contract stage.
