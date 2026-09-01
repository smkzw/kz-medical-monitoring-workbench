# Execution Context: mm_r5_s5_subject_workspace_runtime_v0_1_20260826

Created: 2026-08-26 06:06:54
Objective: Implement and independently verify the exact eleven create-only synthetic/offline R5-S5 Subject Workspace runtime/test/evidence paths unlocked by ACCEPT_R5_S5_CONTRACT, materially enforcing the accepted 265-leaf contract, 250 mutation/oracle registry, typed public-authority boundary, fail-closed domain/subtype identity/date/spine/history rules, while keeping 8911 stopped and medical-writing untouched.
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

- `AGENTS.md` in this workbench and the parent global operating rules already
  loaded by Codex. Coding follows the mandatory ponytail/YAGNI, stdlib-first,
  shortest-coherent-code discipline.
- `context/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_acceptance_record_20260826.md`
- `artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/exact_contract.json`
- `artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/source_leaf_matrix.json`
- `artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/challenge_registry.json`
- `artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/manifest.json`
- the accepted public-authority producer source/tests/evidence pinned by that
  manifest; current filesystem bytes are final truth.
- The accepted manifest's exact eleven `future_runtime_allowlist` paths are the
  entire write boundary. Do not write any twelfth product/runtime/test/evidence
  path and do not modify any pre-existing accepted file.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.
- Keep port 8911 stopped. Do not start a service, browser, real project, real
  model, production workflow, or security task.
- Do not read or modify the medical-writing subsystem except for the existing
  aggregate boundary check.
- Worker 01 may create only the four `src/mm_r5/s5_*.py` paths and
  `tests/s5_runtime_fixtures.py` from the manifest allowlist.
- Worker 02 may create only the five `tests/test_s5_*.py`/challenge paths from
  the manifest allowlist and the one allowlisted evidence JSON. It must not edit
  worker 01 source paths.
- Worker 03 is strictly read-only.
- Dispatch is serial: worker 02 starts after worker 01 completes; worker 03
  starts only after both implementation workers complete.

## Work Items

1. Implement s5_contracts.py, s5_authority_adapter.py, s5_projection.py, s5_validator.py, and synthetic runtime fixtures strictly from the accepted contract and exact allowlist.
2. Implement focused contracts/adapter/projection/validator tests plus materialized challenge tests covering all 250 structured mutation/oracle rows and the ten accepted public graph replays.
3. Independently audit the entire eleven-path runtime surface, run normal/-O/-OO focused and adjacent regressions, verify hashes/boundaries, and report accept-or-revise without modifying files.

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.

Done requires exact eleven-path closure, material execution of all 250 challenge
oracles plus ten accepted replays, normal/`-O`/`-OO` focused tests, adjacent R5
regression, stopped 8911, unchanged medical-writing aggregate, and Codex source
review. File existence or worker self-report is not acceptance.
