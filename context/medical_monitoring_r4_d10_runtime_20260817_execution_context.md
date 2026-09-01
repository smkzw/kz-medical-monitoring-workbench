# Execution Context: medical_monitoring_r4_d10_runtime_20260817

Created: 2026-08-17 21:34:03
Objective: 实现并独立验收 D10 synthetic/offline runtime
Task type: `long_horizon_code`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_opencode_flash` -> `pi` / `opencode-go` / `deepseek-v4-flash`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- Full task contract: `context/medical_monitoring_r4_d10_runtime_20260817_context.md`.
- Frozen D10 v0.6 contract and the corrected, independently accepted 312-case authority/artifact chain recorded in `context/medical_monitoring_r4_d10_authority_correction_worker01_acceptance_20260818.md` are authoritative.
- Accepted D09 runtime is implementation/anti-overfit precedent only; it does not override D10 semantics.
- Current filesystem is authoritative; frozen contract/artifacts and D01-D09 are read-only.

## Risk Boundaries

- Worker 01 may create/write only `poc/medical_monitoring_ai_native_r4/src/mm_r4/d10_contracts.py`, `d10_adapter.py`, `d10_evaluator.py`, `poc/medical_monitoring_ai_native_r4/tests/test_d10_adapter.py`, and `test_d10_runtime_contract.py`.
- Worker 02/03 remain locked until Codex accepts the preceding slice. Do not modify `__init__.py` in Worker 01.
- Runtime must not import/read D10 artifacts, generators, verifier, oracle, registry, quota or tests; the test-only adapter may read frozen artifact files.
- No production writes, UI/service/8911, real projects/models, medical-writing paths, or security design/testing.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. Worker01 typed contracts/test adapter/deterministic evaluator/parity — independently accepted 2026-08-18.
2. Worker02 projection/Query/visibility/deep-link/R2 handoff — independently accepted 2026-08-18.
3. Worker03 exports/anti-overfit/replay/closure/full regression — independently accepted 2026-08-18.

## Completion And Cleanup

Codex and an independent reviewer accepted all three work items and the synthetic/offline D10 runtime. Final pause authority: `context/medical_monitoring_r4_d10_runtime_final_acceptance_pause_20260818.md`. Archive prompts, worker reports and logs under `archives/execution/`; do not delete evidence.
