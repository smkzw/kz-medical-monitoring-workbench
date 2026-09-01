# Task Context: medical_monitoring_real_loop_acceptance_contract_20260802

Created: 2026-08-02 22:52:05
Objective: Create a fail-closed offline contract for serial Playwright dual-role tester rounds, prompt variation, P0-P4 issue closure and two-round acceptance
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User's explicit tester/role/login/round/severity requirements in the current
  task message.
- Current readiness/execution/prompt contracts under
  `services/api/app/monitoring_real_loop_{readiness,execution,prompt_manifest}.py`.
- Candidate project matrix:
  `records/active_slices/medical_monitoring_candidate_matrix_20260802/CANDIDATE_MATRIX.json`.
- The new acceptance module is an evidence validator only; source files and
  runtime outputs remain authoritative when a future controlled run occurs.

## Scope

- In scope: a pure offline Python contract for five requested tester routes,
  two roles, candidate projects, unique prompt refs/hashes, Playwright-only
  login evidence, repair/retest evidence, P0-P4 issue capture and two final
  consecutive clean rounds.
- Out of scope: provider/model dispatch, route-policy approval, browser login,
  API/backend login, source ingestion, B6/CAS, runtime/SQLite, application
  writes, medical adjudication or release approval.

## Success Criteria

- The contract rejects missing tester/role rounds, duplicated prompt refs,
  non-Playwright/API login, unverified routes, invalid route windows, missing
  browser/scientific evidence, untraceable P0-P4 issues and non-consecutive
  clean rounds.
- A synthetic complete fixture can be structurally marked
  `accepted_for_user_acceptance` while all medical/runtime authority flags stay
  false; no synthetic row is treated as a real result.
- Focused/adjacent tests, compileall, Ruff and record review-gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- The five tester routes are requested catalog entries, not proof of current
  availability or authorization. Future route manifests must be validated by
  the executable workflow guard before dispatch.
- `accepted_for_user_acceptance` is structural evidence only; it cannot imply
  clinical correctness, medical confirmation, commercial readiness or release.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 22:52:05: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 22:55 CST: Added the fail-closed acceptance module and focused
  tests; no provider/browser/runtime was invoked.
- 2026-08-02 23:25 CST: Focused 12, adjacent 38 and full monitoring 1,670-test
  regression passed with 25 visible warnings after prompt-manifest binding,
  duplicate-hash rejection and strict boolean evidence validation; ports,
  protected hashes and B6 pending state were rechecked.
