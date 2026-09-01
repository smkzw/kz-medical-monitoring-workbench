# Codex Execution Plan: mm_r6_runtime_slice_02_20260827

Objective: Implement the accepted R6 second synthetic/offline slice for immutable ReportSourceRevision registration, ReportUnit and Claim/Issue many-to-many identity, frozen reverse-review surface, and ClaimCoverageLedger coverage-closed versus full-review eligibility gates, within the exact create-only contract and without product, real reports/projects, OCR/models, or medical-writing changes.

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Source/object worker: implement immutable report source registration/dedup/revision lineage plus deterministic ReportUnit, ReportClaim and ReviewIssue object construction and cross-identity checks in the declared R6 slice-02 paths. | `runs/execution/mm_r6_runtime_slice_02_20260827/worker_01.md` |
| `worker_02` | Coverage worker: implement ReportReviewMatrix, frozen expected review surface, exact reverse coverage links, many-to-many claim/issue joins, ClaimCoverageLedger, complete blocking-reason accumulation, and the coverage_closed versus full_report_reviewed_eligible double gate. | `runs/execution/mm_r6_runtime_slice_02_20260827/worker_02.md` |
| `worker_03` | Verification worker: independently test positive/negative/boundary/tamper cases, duplicate/missing/orphan references, not_evaluable reasons, partial/truncated, anchors/cutoff/revision/comparisons, cross-project/revision isolation, canonical bytes, optimizer/hash seeds, R6 slice-01 adjacency, medical-writing boundary, exact allowlist, and stopped ports. | `runs/execution/mm_r6_runtime_slice_02_20260827/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
