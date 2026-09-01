# Task Context: medical_monitoring_aggregate_cas_replay_contract_20260802

Created: 2026-08-02 19:23:08
Objective: Add and verify a pure in-memory aggregate/CAS replay contract for canonical medical-risk disposition events; replay B4 metadata without persistence, expose missing expected_version evidence, and keep B6/C14 fail-closed.
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Canonical in-memory event/CAS semantics:
  `services/api/app/medical_risk_authority.py`, especially
  `MedicalRiskAggregate.apply`, `MedicalRiskEvent`, and the identity/source
  revision checks.
- Existing metadata-only chain replay:
  `services/api/app/monitoring_disposition_chain_replay.py` and its focused
  tests.
- Actual B4 residual package:
  `runs/execution/medical_monitoring_phase_b4_residual_decision_20260801/B4_RESIDUAL_DECISION_PACKAGE.json`.
- Current B6/C14 reports are read-only gate evidence; this task must not alter
  them or claim medical approval.

## Scope

- In scope: add a pure in-memory aggregate/CAS replay module and focused tests;
  validate event identity, source revision, previous state, duplicate event
  IDs, expected version/CAS sequence, and final-state drift; replay the B4
  metadata with an explicit `expected_version`-missing issue.
- Out of scope: SQLite/database access, runtime/API/provider/browser/service
  execution, aggregate mutation, migration, source-token synthesis, medical or
  engineering reviewer outcome, real-project writes, and release closure.

## Success Criteria

- A complete event case replays deterministically through the canonical CAS
  sequence and produces a final state without mutating a persisted aggregate.
- Any identity/source/version/state/duplicate defect becomes a typed issue;
  missing `expected_version` in B4 metadata is explicit rather than inferred.
- Reports always keep `aggregate_write_permitted=false` and
  `migration_ready=false`, including when a synthetic complete case passes.
- B6/C14 source bytes and statuses remain unchanged; focused and adjacent tests
  pass.

## Risk Boundaries

- Only the new module, focused tests, and task evidence surfaces under
  `services/api/app/`, `tests/`, `context/`, `records/active_slices/`,
  `reviews/`, and `metrics/` may be written. Do not write runtime stores or
  real-project files.
- Direct Codex work; no delegated agent/provider/conference.
- The contract is diagnostic/replay-only and cannot grant aggregate or
  migration authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 19:23:08: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Existing chain replay proves only metadata state continuity; the
  new bounded action must expose the absent B4 CAS version evidence.
- 2026-08-02 19:30 CST: Added the pure in-memory aggregate/CAS replay module,
  focused tests, and read-only B4 evidence. Static checks and 54 focused/
  adjacent tests passed. B4 produces two metadata-complete chains but five
  explicit missing-`expected_version` issues; CAS replay remains incomplete
  and write/migration authority remains false.
- 2026-08-02 19:31 CST: Codex review and Hermes review-gate passed for this
  bounded diagnostic slice. No runtime, database, service, browser, provider,
  or real-project action was performed.
