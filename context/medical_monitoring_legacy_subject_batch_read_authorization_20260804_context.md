# Task Context: medical_monitoring_legacy_subject_batch_read_authorization_20260804

Created: 2026-08-04 02:46:31
Objective: 为 main.py 旧版受试者画像及医学监查批次/会话读取面接入现有 READ_MONITORING 服务器 principal/ACL，保持写入与其他跨模块旧面不变
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

The previous slice closed identity for five legacy risk/data reads. Source
inventory shows the older subject profile and batch/session reads still bypass
the same boundary. This slice extends only the read side of those monitoring
surfaces and leaves every monitoring write route unchanged.

## Source Of Truth

- `services/api/app/main.py` route definitions for subject profile,
  `monitoring/batches`, batch detail, batch-diff and intake-session reads.
- Existing `MonitoringAction.READ_MONITORING`, host principal adapter, runtime
  route context and ACL implementation.
- `tests/test_monitoring_batch_api.py`, `tests/test_contracts.py`, and the
  real-project subject consumer suites.
- Closed upstream gates:
  `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json`
  (`pending_review`) and
  `runs/execution/medical_monitoring_phase_c14_b6_activation_gate_20260802/B6_TO_C13_ACTIVATION_GATE_REPORT.json`
  (`blocked_pending_b6_review`).

## Scope

- In scope: protect `GET /subjects/{subject_id}/monitoring`, batch list,
  batch detail, batch-diff, and monitoring intake-session reads with the
  existing `READ_MONITORING` server principal/ACL; preserve downstream
  canonicalization and response shape; update affected offline API harnesses
  to inject explicit project-scoped test principals; add no-principal tests.
- Out of scope: all monitoring writes (intake, batch file, validation,
  transition, confirm/verify), dashboard, workbench inbox, AI legacy routes,
  source registration, risk disposition, auth middleware/provider, frontend,
  DB/schema/migration, B6/C14, real-project LOOP, browser/provider/login.

## Success Criteria

- Each named read fails with HTTP 503 and
  `monitoring_principal_unavailable` before repository/service lookup when no
  host principal is present.
- A verified medical-manager principal scoped to the canonical project can
  reach existing subject/batch/session read behavior without client actor
  fallback or path leakage.
- Focused, adjacent and full monitoring tests pass; changed Python compiles;
  Hermes review-gate passes with verification required.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Do not add a new action, role, offline production bypass, or authentication
  parser merely to satisfy tests.
- Do not protect the write routes in this slice; they require a separate exact
  action inventory.
- No service/browser/provider/API login/runtime DB/real project/external agent.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 02:46:31: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Read-only route inventory selected the five read groups in this
  slice; writes and cross-module legacy surfaces remain explicitly out of scope.
