# Task Context: medical_monitoring_project_admission_contract_20260803

Created: 2026-08-03 00:02:02
Objective: 新增只读、fail-closed的医学监查项目准入合同，校验项目身份、监查适配器、来源绑定、两批全量证据、prompt覆盖与上游B6/CAS/runtime gate；不接入运行时、不改变canonical集合
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max-preview` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_real_loop_readiness.py` and its focused tests.
- `services/api/app/monitoring_real_loop_prompt_manifest.py` and its frozen 24-row artifact.
- `services/api/app/monitoring_real_loop_acceptance.py` and five-project acceptance metadata.
- `records/active_slices/medical_monitoring_project_source_adapter_reconciliation_20260802/PROJECT_SOURCE_ADAPTER_RECONCILIATION.json`.
- `services/api/app/monitoring_project_registry.py`, `main.py` static registrations and `project_source_manifest.py` static builders.
- Current B6/C14/readiness JSON reports.

## Scope

- In scope: add a pure, fail-closed validator that reconciles one declared monitoring project admission against identity, adapter registration, source/module binding, explicit full batches, prompt coverage and upstream gate booleans; add focused tests and evidence.
- Out of scope: changing canonical IDs, adding candidate adapters, registering sources, calling providers, launching services/browser, touching runtime/SQLite/CAS, or changing medical-writing surfaces.

## Success Criteria

- The validator returns deterministic issue codes and never grants runtime/provider/write/medical authority.
- It rejects candidate-only roots, non-monitoring aliases, missing source/module bindings, duplicate/incomplete batches, missing project prompt rows, and any false upstream gate.
- It accepts only a structurally complete diagnostic admission record; acceptance is not a production registration or medical approval.
- Focused tests prove positive and fail-closed cases; existing protected files and the canonical readiness/prompt artifacts remain unchanged.

## Risk Boundaries

- Only add a new pure module and focused test file under the product source/tests, plus task evidence files.
- Do not import or mutate runtime stores; no service/provider/browser execution.
- The validator is a diagnostic gate only; it must not be wired to activation or silently promote a project.
- The delegated route is not used in this parent-owned turn; Codex remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 00:02:02: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 00:02:40: Parent Codex selected a direct pure-contract implementation; no external provider or subagent dispatch.
- 2026-08-03 00:05:00: Added the pure admission contract and five focused tests; focused/adjacent tests, compileall and Ruff passed; review-gate `ok=true`.
