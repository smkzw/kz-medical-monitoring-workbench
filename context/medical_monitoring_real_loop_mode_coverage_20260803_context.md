# Task Context: medical_monitoring_real_loop_mode_coverage_20260803

Created: 2026-08-03 02:25:51
Objective: Add a read-only contract for commercial acceptance coverage of daily incremental, pre-lock total, and post-lock fixed-total monitoring modes; keep B6/C14/runtime/browser/provider/release authority blocked.
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `alibaba` / `qwen3.8-max-preview` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_release_dossier.py` names the closed commercial
  control `three_monitoring_modes`.
- `services/api/app/monitoring_real_loop_acceptance.py` and its persisted
  revalidator prove browser/scientific tester/role/project rounds but do not
  classify the three monitoring modes.
- The P10 requirements traceability and user goal define the modes as daily
  incremental monitoring, pre-lock total plus query-revision increments, and
  post-lock fixed-total/CFDI-precheck monitoring.

## Scope

- In scope: a pure offline mode-coverage evidence contract, focused tests, and
  one current blocked diagnostic artifact. It must bind each mode observation to
  a user-view acceptance run, enforce the frozen tester/role/project vocabulary,
  and require browser/scientific evidence with no P0-P4 issue.
- Out of scope: service/provider/browser/API login, real project/source access,
  B6/C14/CAS/source-token/runtime changes, frontend/medical-writing changes,
  clinical inference, and any UAT or release approval.

## Success Criteria

- The contract reports complete mode coverage only when all three canonical
  modes are represented for both engineer and senior-medical-monitor roles,
  every mode row is bound to a unique clean acceptance run, and every candidate
  project appears at least once across the mode evidence.
- Missing/duplicate/unknown modes, role/project drift, run mismatch, dirty or
  non-Playwright evidence, missing browser/scientific refs, and authority flags
  fail closed.
- Current filesystem diagnostic is blocked with zero fabricated mode results;
  report flags remain read-only/non-authoritative.
- Focused/adjacent tests, compile checks and Hermes review-gate pass; 8911/5174
  and protected frontend hashes remain unchanged.

## Risk Boundaries

- Only task-owned source/test/context/review/metrics/active-slice files may be
  changed. No provider, service, browser, API, SQLite, runtime, source registry
  or real-project writes.
- A complete mode-coverage report is evidence for later user acceptance only;
  it cannot grant medical confirmation, runtime write, UAT or release authority.
- This is a direct Codex implementation slice; no external runner or child
  agent is dispatched.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 02:25:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Direct Codex implementation selected after the P10 review found
  that the commercial dossier's three-mode control had no run-level evidence
  contract; no external route is dispatched.
