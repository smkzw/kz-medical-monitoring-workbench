# Execution Context: mm_r5_s5_public_authority_producers_20260825

Created: 2026-08-25 21:51:13
Objective: Implement and verify the exact eleven create-only R5-S5 public-authority producer paths unlocked by accepted v0.4.2. Public builders accept only frozen AuthorityBundleV02 internal authority and return packet only. Reconstruct subject temporal and AEMH match-history public packets, preserve source joins and history, fail closed, remain synthetic/offline/read-only. Keep port 8911 stopped and medical-writing untouched.
Task type: `long_horizon_code`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_opencode_flash` -> `codex-subagent` / `codex` / `gpt-5.6-luna`
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

1. Implement the three production modules and runtime fixtures on the exact accepted create-only paths, using stdlib-first immutable dataclasses and accepted recipe/typed authority only.
2. Implement the six focused/adjacent/challenge test files on exact accepted paths, covering packet-only API, 272 joins, 192 replays, 236 runtime specs, read-only pins and side-effect absence.
3. Perform a read-only independent audit of the completed eleven-path producer package against accepted v0.4.2, AST/import/call restrictions, source-join and sensitivity requirements; report defects without acceptance.

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
