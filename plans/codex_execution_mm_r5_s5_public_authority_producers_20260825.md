# Codex Execution Plan: mm_r5_s5_public_authority_producers_20260825

Objective: Implement and verify the exact eleven create-only R5-S5 public-authority producer paths unlocked by accepted v0.4.2. Public builders accept only frozen AuthorityBundleV02 internal authority and return packet only. Reconstruct subject temporal and AEMH match-history public packets, preserve source joins and history, fail closed, remain synthetic/offline/read-only. Keep port 8911 stopped and medical-writing untouched.

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Implement the three production modules and runtime fixtures on the exact accepted create-only paths, using stdlib-first immutable dataclasses and accepted recipe/typed authority only. | `runs/execution/mm_r5_s5_public_authority_producers_20260825/worker_01.md` |
| `worker_02` | Implement the six focused/adjacent/challenge test files on exact accepted paths, covering packet-only API, 272 joins, 192 replays, 236 runtime specs, read-only pins and side-effect absence. | `runs/execution/mm_r5_s5_public_authority_producers_20260825/worker_02.md` |
| `worker_03` | Perform a read-only independent audit of the completed eleven-path producer package against accepted v0.4.2, AST/import/call restrictions, source-join and sensitivity requirements; report defects without acceptance. | `runs/execution/mm_r5_s5_public_authority_producers_20260825/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
