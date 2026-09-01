# Codex Execution Plan: medical_monitoring_r4_d07_artifacts_20260813

Objective: Generate the synthetic/offline R4-D07 144-case typed fixture catalog, independent expected-outcome oracle, manifest, closed assertion DSL, registry and deterministic generator exactly from the accepted semantic contract, without writing D07 runtime or touching product, real projects, port 8911 or medical-writing.

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Implement a deterministic D07 artifact generator and exact schema/hash/integrity validation, reusing only proven D06 infrastructure patterns without copying D06 clinical semantics. | `runs/execution/medical_monitoring_r4_d07_artifacts_20260813/worker_01.md` |
| `worker_02` | Materialize exactly 144 synthetic D07 typed fixtures and an independently authored exact-leaf oracle covering every matrix row, ownership, scope, medical, lifecycle and Journey boundary. | `runs/execution/medical_monitoring_r4_d07_artifacts_20260813/worker_02.md` |
| `worker_03` | Generate manifest/registry/DSL, run bijection/hash/duplicate/independence/mutation-style static validations, and return hashes plus an auditable handoff; do not implement runtime. | `runs/execution/medical_monitoring_r4_d07_artifacts_20260813/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `finite_code_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/medical_monitoring_r4_d07_artifacts_20260813/manager.md` |

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
