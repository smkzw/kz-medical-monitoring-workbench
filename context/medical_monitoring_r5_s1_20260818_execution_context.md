# Execution Context: medical_monitoring_r5_s1_20260818

Created: 2026-08-18 12:37:47
Objective: 实现并独立验收 R5 S1：exact typed contracts/canonical hash、只读 R4 authority adapter/receipt、真实 S1 challenge tests 与 immutable R4 SHA gate；仅写 poc/medical_monitoring_ai_native_r5 和本任务记录，不启动 8911
Task type: `finite_code_task`
Risk: `high`
Execution module trigger: Codex identified 4 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `pi` / `cms-smk` / `deepseek-v4-flash`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

1. `context/medical_monitoring_r5_contract_acceptance_record_20260818.md` and its exact seven-SHA freeze.
2. `reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md`.
3. `artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json`, `challenge_registry.json`, `quota_ledger.json`, `manifest.json`.
4. Read-only R4 public dataclasses under `poc/medical_monitoring_ai_native_r4/src/mm_r4/`, especially `d10_contracts.py`, `d10_projection.py`, `ensemble_contracts.py`, and existing public tests/fixtures needed to construct real typed objects.
5. Current filesystem outranks worker assumptions. A deferred R5 leaf stays deferred in S1 unless this task explicitly implements its named authority contract.

## Risk Boundaries

- Sole implementation write domain: `poc/medical_monitoring_ai_native_r5/**`.
- Process records are runner-owned; workers return reports and do not edit `runs/**`, `logs/**`, `context/**`, `plans/**`, `reviews/**`, `metrics/**`, `prompts/**`.
- R1-R4, `frontend/**`, medical-writing paths, real project data, production and security work are read-only/out of scope. Any byte drift in R4 fails S1.
- Do not start 8911, a browser, Playwright or any service. S1 is offline Python only.
- Do not install packages, access credentials/accounts, call real models, or create hidden project/fixture/sentinel semantic branches.
- S0 registry rows are specifications. S1 must execute exactly R5C-001..R5C-016 through real typed fixtures and the real validator/adapter; string-label self-proof is forbidden.
- Worker outputs are evidence for Codex, not acceptance. Fresh isolated reviewer owns the final S1 verdict.

## Work Items

1. W1_exact_typed_contracts_and_canonical_hash
2. W2_r4_authority_adapter_and_receipt
3. W3_real_s1_challenge_tests_and_r4_sha_gate
4. W4_independent_acceptance_evidence

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
