# Execution Context: mm_r6_runtime_slice_01_20260827

Created: 2026-08-27 13:56:26
Objective: Implement the accepted R6 v0.1 contract as a synthetic/offline deterministic runtime slice with frozen fixtures, 11 validators, 86 metadata-oracle mutations, reproducibility tests, and a read-only evidence receipt, without touching product frontend, medical writing, real projects, services, browsers, OCR, or models.
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

1. Contract and fixture worker: read the frozen prose/machine contract/challenge matrix and implement deterministic baseline fixture catalog plus pointer preconditions only within the declared R6 create-only paths.
2. Validator worker: implement the minimal Python-stdlib 11-validator dispatcher and one-replace-per-row challenge executor with canonical failure, blocking, and projection outputs only within declared R6 create-only paths.
3. Verification worker: independently test 86/86 oracle parity, 49 diagnostic mappings, positive rows, deterministic bytes, normal/-O/-OO/hash seeds, source immutability, ports stopped, and protected medical-writing boundary; report findings without claiming final acceptance.

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
