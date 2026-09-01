# Task Context: medical_monitoring_assurance_durable_audit_20260803

Created: 2026-08-03 22:55:55
Objective: 将医学监查保障成功写入与既有不可变审计合约接入同一 SQLite 事务，持久化授权决策哈希链和高风险签署证据哈希，同时保持无真实认证时 fail-closed
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_audit_contract.py`: immutable, hash-linked
  monitoring audit event contract; currently intentionally in-memory.
- `services/api/app/monitoring_assurance_repository.py`: assurance SQLite
  transactions, CAS/idempotency and existing task events.
- `services/api/app/monitoring_assurance_service.py`: pre-lock/pre-inspection
  write orchestration and completion gates.
- `services/api/app/monitoring_assurance_router.py`: server-principal route
  authorization and high-risk reauthentication/signature evidence boundary.
- `services/api/app/monitoring_identity_authorization.py`: principal snapshot
  and authorization decision hashes.
- Official transaction references consulted: SQLite transaction semantics
  (https://sqlite.org/lang_transaction.html) and Python `sqlite3` transaction
  documentation (https://docs.python.org/3/library/sqlite3.html).

## Scope

- In scope: persist successful server-authorized assurance mutations as
  `MonitoringAuditEvent` records in a per-project hash chain, append them in
  the same `BEGIN IMMEDIATE` transaction as the task/proof/rollup/review/
  completion mutation, carry the route's authorization decision and signature
  evidence hash through service/repository, expose a read-only repository
  verifier/list helper for tests, and add rollback/replay/chain tests.
- Out of scope: authentication provider/session middleware, denied-attempt
  audit at the HTTP boundary, external signature provider verification,
  changing the ACL, raw clinical/risk data, source promotion, B6/C14, live
  service/browser/provider/real-project runs, or general audit refactors.

## Success Criteria

- Production server-principal writes include an immutable audit event with
  principal snapshot, decision hash, action, source/frozen identity hash,
  CAS versions, and only hash-safe payload fields.
- Audit append and domain mutation share the repository transaction; an audit
  failure rolls back the domain write.
- Exact idempotent replay produces no duplicate audit event; changed payload
  under one idempotency key remains rejected by the existing contract.
- Completion persists the server-bound signature evidence hash and does not
  treat client `confirmed_by` as authoritative.
- Existing legacy test harnesses with explicit `require_server_principal=False`
  retain their old event behavior without inventing production audit identity.
- Focused/adjacent tests, static checks and review-gate pass; no service or
  real-project gate is opened.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 22:55:55: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 22:58:00: Read-only audit/repository review confirmed the existing
  in-memory contract and SQLite transaction boundary. Direct post-write
  logging was rejected as non-atomic; the slice is scoped to same-transaction
  persistence only.
