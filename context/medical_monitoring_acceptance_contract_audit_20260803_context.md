# Task Context: medical_monitoring_acceptance_contract_audit_20260803

Created: 2026-08-03 17:14:37
Objective: 只读审查五测试者两角色两轮 Playwright/scientific acceptance 契约与 real-loop readiness，发现并修正可证明的误报或 fail-open 缺口，不执行运行时
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Workbench filesystem only. Primary contracts/artifacts:
  - `services/api/app/monitoring_real_loop_acceptance.py`
  - `services/api/app/monitoring_real_loop_acceptance_revalidation.py`
  - `services/api/app/monitoring_real_loop_readiness.py`
  - `services/api/app/monitoring_real_loop_execution.py`
  - `services/api/app/monitoring_real_loop_prompt_manifest.py`
  - `records/active_slices/medical_monitoring_real_loop_readiness_contract_20260802/REAL_LOOP_READINESS.json`
  - `records/active_slices/medical_monitoring_real_loop_acceptance_contract_20260802/ACCEPTANCE_CONTRACT.json`
  - `records/active_slices/medical_monitoring_real_loop_acceptance_revalidation_20260803/REAL_LOOP_ACCEPTANCE_REVALIDATION.json`
- The `clinical-web-e2e-testing` skill was read to align the audit with role-by-role Login → Project List → Project → action-page evidence, Playwright-only user-view login, screenshots, and structured gap analysis.
- Current filesystem is final truth; no service, browser, provider, API login, or real project may be started in this slice.

## Scope

- In scope: static contract review, persisted readiness/acceptance artifact re-open, focused deterministic tests, negative bypass probes, and documenting whether the structural contract can be promoted to real evidence safely.
- Out of scope: generating synthetic acceptance rows as real results, Playwright login, provider/model calls, service startup, raw project ingestion, medical confirmation, release authority, or changing the protected product/medical-writing runtime.

## Success Criteria

- Confirm the five tester × two role × two clean-round matrix is frozen and cannot be narrowed, duplicated, or satisfied with API login, missing evidence, dirty streaks, prompt reuse, route-window drift, or overlapping sessions.
- Confirm readiness remains blocked by source/batch/B6/CAS/runtime prerequisites and acceptance revalidation cannot infer missing real-run evidence.
- Identify and repair only a proven contract defect; if the current contract is intentionally structural-only, preserve source and record the remaining evidence-integrity gap for the controlled real run.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- A structurally clean fixture is not browser/scientific/UAT evidence and cannot be reported as commercial acceptance.
- Do not treat opaque evidence refs or route flags as proof that a browser session actually occurred; the future controlled run must produce independently reviewable artifacts.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 17:14:37: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Reopened the planning readiness artifact: `blocked`, 3 canonical projects, 24 scenarios, 10 explicit issues, no provider/runtime/write permission. Reopened the acceptance planning contract: 5 tester routes, 2 roles, 5 candidate projects, 2 consecutive clean rounds, Playwright-only login and all authority false.
- 2026-08-03: Reopened persisted acceptance revalidation: `blocked`, no persisted Playwright/scientific JSON declared, 0 tester/role/run counts, no authority. The structural module's synthetic fixture remains a test contract only.
- 2026-08-03: Focused acceptance/readiness/execution/prompt-manifest tests passed `54 passed in 0.17s`; negative probes blocked missing browser/scientific refs, API login and non-contiguous rounds. No source defect justified a patch. Opaque evidence refs are recorded as a mandatory future hash-bound artifact gate.
