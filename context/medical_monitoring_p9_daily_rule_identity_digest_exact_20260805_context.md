# Task Context: medical_monitoring_p9_daily_rule_identity_digest_exact_20260805

Created: 2026-08-05 10:28:20
Objective: Harden daily-run runtime rule identity boundaries so all persisted and resolver-supplied SHA-256 identity fields are exact lowercase 64-hex values, without changing provider/runtime boundaries or clinical behavior
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_service.py`
- `services/api/app/main.py` (`_current_monitoring_rule_runtime` wiring)
- `tests/test_monitoring_daily_run_service.py`
- `tests/test_monitoring_rule_release_chain_p0_20260730.py` (isolated resolver mirror)
- `services/api/app/monitoring_record_rule_resolver.py` (aggregate identity producer)
- `services/api/app/monitoring_batch_repository.py` (canonical SHA-256 contract precedent)
- `context/medical_monitoring_p9_source_only_checkpoint_20260805.md`
- `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`

The current filesystem and these source contracts are authoritative for this
bounded source-only slice. No provider, runtime, browser, real-project or
medical-writing path may be activated while the formal gate is blocked.

## Scope

- In scope: strict validation of persisted and resolver-supplied SHA-256 rule
  identity fields at the daily-run service boundary; focused negative tests;
  source-only records and review evidence.
- Out of scope: provider/runtime activation, services or ports, Playwright or
  API login, real-project data, clinical interpretation, browser/visual
  acceptance, database migrations, and the medical-writing subsystem.

## Success Criteria

- Every SHA-256 identity field used by daily-run preparation or pre-execution
  revalidation is accepted only as an exact lowercase 64-hex string; no
  trimming, lowercasing or string coercion is used to make malformed identity
  bytes pass.
- Missing-value error semantics remain fail-closed and existing revision-token
  semantics are unchanged.
- Focused daily-run service tests cover padded, uppercase, non-string and valid
  digest cases in both project-effective and record-applicability paths.
- Focused regressions, adjacent Python checks, and source review pass; runtime
  and browser acceptance remain explicitly unverified under the formal gate.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This slice is performed directly by Codex; the route recorded by task
  initialization is not dispatched because no sub-agent/provider call is
  authorized or needed for the bounded change.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 10:28:20: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 10:31: re-anchored instruction hashes, previous review-gate, formal
  read-only gate and empty reserved ports; selected direct source-only work.
- 2026-08-05 10:36: implemented exact lowercase SHA-256 validation at the
  daily-run service boundary; removed digest trimming from runtime comparisons;
  hardened the main resolver wiring and added focused negative cases for
  project-effective, frozen-mapping, active-mapping, record-aggregate and
  persisted-run identity values.
- 2026-08-05 10:38: focused service/repository/record-resolver suite passed
  (96 tests, 41 subtests); compileall passed. Router/P0 adjacency collection
  remains unavailable because the current Python environment lacks
  `cryptography`; no dependency was installed and no runtime was activated.
- 2026-08-05 10:40: Codex review-gate returned `ok=true`; appended LOOP 5.274
  and the P9 source-only checkpoint. Runtime/provider/browser/real-project
  evidence remains prohibited by the formal gate.
