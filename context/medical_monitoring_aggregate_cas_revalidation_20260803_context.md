# Task Context: medical_monitoring_aggregate_cas_revalidation_20260803

Created: 2026-08-03 04:44:54
Objective: 为 B4 aggregate/CAS replay 证据增加源包、静态重放报告与文件完整性只读重验证；保留缺失 expected_version/CAS incomplete 残差，不授予 B6/C14、迁移、写入或医学权限。
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_aggregate_cas_replay.py`
- `tests/test_monitoring_aggregate_cas_replay.py`
- `records/active_slices/medical_monitoring_aggregate_cas_replay_contract_20260802/B4_AGGREGATE_CAS_REPLAY.json`
- `runs/execution/medical_monitoring_phase_b4_residual_decision_20260801/B4_RESIDUAL_DECISION_PACKAGE.json`
- Current B6/C14 and P10 evidence under `records/active_slices/medical_monitoring_goal_p10_20260730/`.
- No runtime, SQLite, provider, browser, API or real-project state is an authority source for this offline slice.

## Scope

- In scope: add a pure revalidation boundary; reopen the static B4 replay artifact and its
  source package by safe relative path, bytes and SHA-256; reconstruct the source chains;
  rerun deterministic aggregate/CAS replay; persist a diagnostic-only report and tests.
- Out of scope: aggregate apply, migrations, B6/C14 outcome inference, source-token
  closure, approved-input creation, provider calls, service/browser/API execution,
  frontend/medical-writing changes, or real project data writes.

## Success Criteria

- Current B4 artifact and source package replay exactly with fresh evidence and zero
  revalidation issues.
- Preserve the underlying `cas_replay_complete=false` and five missing
  `expected_version` findings; never infer a version or grant write authority.
- Detect artifact/source bytes or SHA drift, report tampering, malformed source chains,
  unsafe paths and authority-boundary mutations.
- Focused/adjacent tests, py_compile, Ruff, artifact replay and Hermes workflow review-gate pass.
- 8911/5174 remain stopped and protected frontend hashes remain unchanged.

## Risk Boundaries

- Do not write aggregate/CAS, migrate, approve, activate, call a provider, start a service,
  login through API/browser, or run any real project.
- This is direct Codex work; no delegated agent, conference, provider or browser is used.
- Evidence freshness is not CAS completion, B6 approval or medical authority.
- 8911 and 5174 must remain stopped.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 04:44:54: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 04:45-05:00: Reconstructed the two current B4 aggregate cases and five events;
  deterministic report SHA matched `2face7f0...57babfba`.
- 2026-08-03 05:00-05:20: Added read-only revalidation module, six focused tests and a
  persisted current-source evidence envelope. No external state was touched.
- 2026-08-03 05:20: Current report is `fresh` as evidence, with `metadata_chain_complete=true`,
  `cas_replay_complete=false`, `replay_issue_count=5`, `case_count=2`, `event_count=5`,
  all authority/write flags false. Next safe chain remains formal B6 outcomes before any
  controlled runtime sequence.
- 2026-08-03 05:25: Final focused/adjacent regression was **159 passed**; Ruff/compile and
  Hermes review-gate passed; protected frontend hashes and 8911/5174 stop state are unchanged.
