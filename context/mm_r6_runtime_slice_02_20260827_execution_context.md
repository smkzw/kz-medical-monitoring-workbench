# Execution Context: mm_r6_runtime_slice_02_20260827

Created: 2026-08-27 15:50:54
Objective: Implement the accepted R6 second synthetic/offline slice for immutable ReportSourceRevision registration, ReportUnit and Claim/Issue many-to-many identity, frozen reverse-review surface, and ClaimCoverageLedger coverage-closed versus full-review eligibility gates, within the exact create-only contract and without product, real reports/projects, OCR/models, or medical-writing changes.
Task type: `finite_code_task`
Risk: `medium`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `pi` / `mtplx` / `mtplx-qwen38-27b-optimized-quality`
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

1. Source/object worker: implement immutable report source registration/dedup/revision lineage plus deterministic ReportUnit, ReportClaim and ReviewIssue object construction and cross-identity checks in the declared R6 slice-02 paths.
2. Coverage worker: implement ReportReviewMatrix, frozen expected review surface, exact reverse coverage links, many-to-many claim/issue joins, ClaimCoverageLedger, complete blocking-reason accumulation, and the coverage_closed versus full_report_reviewed_eligible double gate.
3. Verification worker: independently test positive/negative/boundary/tamper cases, duplicate/missing/orphan references, not_evaluable reasons, partial/truncated, anchors/cutoff/revision/comparisons, cross-project/revision isolation, canonical bytes, optimizer/hash seeds, R6 slice-01 adjacency, medical-writing boundary, exact allowlist, and stopped ports.

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
