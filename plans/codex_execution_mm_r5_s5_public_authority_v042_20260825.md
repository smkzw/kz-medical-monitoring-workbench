# Codex Execution Plan: mm_r5_s5_public_authority_v042_20260825

Objective: Implement a new immutable R5-S5 public-authority implementation contract v0.4.2 on new paths. Consume the accepted typed-authority delta v0.1; reconstruct and execute 272 leaf closures, 192 accepted error replays, 58 active gates, 226 reject issue metadata and the exact future producer contract. Close all four v0.4.1 fail-open attacks. Do not modify v0.4.1 or accepted inputs, create 11 producers, touch medical-writing, or start 8911.

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Design and implement the v0.4.2 standard-library generator and generated registries on new paths, reusing accepted source authorities only. | `runs/execution/mm_r5_s5_public_authority_v042_20260825/worker_01.md` |
| `worker_02` | Design and implement an independent v0.4.2 verifier with primary-gate attacks for fake 272/192/58/226 registries and protected boundaries. | `runs/execution/mm_r5_s5_public_authority_v042_20260825/worker_02.md` |
| `worker_03` | Perform a read-only first-principles audit of v0.4.1 fail-open evidence, accepted typed delta, error replay sources and future producer contract; return exact integration requirements and likely defects. | `runs/execution/mm_r5_s5_public_authority_v042_20260825/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
