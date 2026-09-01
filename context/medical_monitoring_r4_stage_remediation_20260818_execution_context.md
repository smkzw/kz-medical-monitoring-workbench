# Execution Context: medical_monitoring_r4_stage_remediation_20260818

Created: 2026-08-18 09:14:45
Objective: 修复 R4 阶段关闭审阅的四项阻断并形成独立复验包
Task type: `long_horizon_code`
Risk: `high`
Execution module trigger: Codex identified 5 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_opencode_flash` -> `pi` / `cms-smk` / `deepseek-v4-flash`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `reviews/medical_monitoring_r4_stage_independent_review_20260818.md`
- `runs/execution/medical_monitoring_r4_stage_closure_20260818/grok_remediation_plan.md`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/`
- `poc/medical_monitoring_ai_native_r4/tests/`
- repository-root `tests/test_d07_artifact_generator.py` through `test_d10_artifact_generator.py`
- current filesystem is authoritative; existing user and parallel-work changes must be preserved.

## Risk Boundaries

- Synthetic/offline R4 POC only. No R5, UI, product runtime, real project, real medical-model, browser or service work.
- Port 8911 must remain stopped.
- Do not read or modify the medical-writing subsystem or its files.
- Do not modify D06-D10 frozen catalog/oracle/registry artifacts unless a work item explicitly says so; current work items do not authorize such byte changes.
- Reference baseline is challengeable and never a gold standard. Query remains a three-part draft; PD remains a verification lead, not a send/reply/close workflow.
- High-risk disagreement may not be hidden by merge, vote or adjudication.
- Production decisions may not branch on fixture IDs, case indexes, mutation IDs, `SYN-*` sentinels or one canonical synthetic scope.
- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. W1 Ruff hygiene 与 D07 stale artifact pin
2. W2 coverage matrix 差异分类与冻结动作
3. W3 shared ensemble/reference-baseline offline closure
4. W4 D06 typed authority scope 去 sentinel
5. W5 传播回归与同一 verifier 复验包

## Completion And Cleanup

Codex reviews worker outputs and final artifacts. Only the independent stage verifier can return `ACCEPT_R4_STAGE`; workers may report readiness only. After acceptance, run `cleanup-execution` to archive prompts, worker reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
