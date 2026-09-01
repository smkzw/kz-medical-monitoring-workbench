# Execution Context: mm_r5_s5_public_authority_v042_20260825

Created: 2026-08-25 20:42:57
Objective: Implement a new immutable R5-S5 public-authority implementation contract v0.4.2 on new paths. Consume the accepted typed-authority delta v0.1; reconstruct and execute 272 leaf closures, 192 accepted error replays, 58 active gates, 226 reject issue metadata and the exact future producer contract. Close all four v0.4.1 fail-open attacks. Do not modify v0.4.1 or accepted inputs, create 11 producers, touch medical-writing, or start 8911.
Task type: `finite_code_task`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `cursor` / `cursor-cli` / `auto`
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

1. Design and implement the v0.4.2 standard-library generator and generated registries on new paths, reusing accepted source authorities only.
2. Design and implement an independent v0.4.2 verifier with primary-gate attacks for fake 272/192/58/226 registries and protected boundaries.
3. Perform a read-only first-principles audit of v0.4.1 fail-open evidence, accepted typed delta, error replay sources and future producer contract; return exact integration requirements and likely defects.

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
