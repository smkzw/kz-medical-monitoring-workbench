# Codex Execution Plan: medical_monitoring_r4_d02_cm_slice_20260811

Objective: Implement and verify the frozen isolated synthetic R4-D02 CM medication rationale, prohibited/restricted medication, cross-domain evidence, Query and journey contract without touching product, medical-writing, real projects or frozen R1-R3

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Serial shared-surface prerequisite: add RiskDomainUnitResult, neutral priority/identity accessors and CrossDomainEvidenceRef in contracts.py; adapt AEMHUnitResult/lifecycle with no D01 behavior change; run D01 224 before proceeding | `runs/execution/medical_monitoring_r4_d02_cm_slice_20260811/worker_01.md` |
| `worker_02` | Implement D02 CM domain engine and deterministic tests for inputs, unit expansion, five L1 dispositions, identity, Query, and cross-domain evidence in new cm.py/tests | `runs/execution/medical_monitoring_r4_d02_cm_slice_20260811/worker_02.md` |
| `worker_03` | Implement D02 CM journey/projection payloads and bidirectional joins in new cm_projection.py/tests | `runs/execution/medical_monitoring_r4_d02_cm_slice_20260811/worker_03.md` |
| `worker_04` | Implement synthetic fixtures/challenge matrix 1-30, N-to-N+1 lifecycle and adjacent regression evidence in cm_fixtures.py/tests | `runs/execution/medical_monitoring_r4_d02_cm_slice_20260811/worker_04.md` |

## Ordered Gates

1. Dispatch `worker_01` alone. Codex reviews its exact diff and reruns the original D01 `224 passed` baseline plus the new shared-protocol test.
2. Only after Gate 1 passes, dispatch `worker_02`–`worker_04` on disjoint new files.
3. Codex integrates root exports and documentation, then runs focused D02, full R4, adjacent R2/R3 and static checks.
4. A fresh-context independent conference owns the D02 acceptance recommendation; Codex applies any bounded repair and records final evidence.

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `finite_code_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/medical_monitoring_r4_d02_cm_slice_20260811/manager.md` |

## Codex Acceptance

Verify every frozen v1.1 clause against executable tests, inspect all worker diffs, preserve the frozen D01/R2/R3 baselines, confirm synthetic-only isolation and 8911 stopped, then update the R0-R8 recovery point. This slice does not include product UI, Patient Journey rendering, real-project data, live providers, dictionaries, services, browser E2E, or security/safety work.
