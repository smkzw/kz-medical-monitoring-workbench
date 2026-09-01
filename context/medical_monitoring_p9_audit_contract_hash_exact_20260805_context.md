# Task Context: medical_monitoring_p9_audit_contract_hash_exact_20260805

Created: 2026-08-05 18:39:29
Objective: 在真实LOOP正式门保持阻断的前提下，使只读医学监查审计事件契约的决定哈希与前序事件哈希严格接受原始小写64位SHA-256，并以聚焦/相邻回归证明链路非法值失败关闭。
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_audit_contract.py`
- `tests/test_monitoring_audit_contract.py`
- `services/api/app/monitoring_identity_authorization.py` (decision-hash
  producer and principal binding reference)
- selected readiness/upstream and identity-authorization adjacency tests
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
- P9 checkpoint and P10 LOOP ledger.

## Scope

- In scope: exact raw lowercase 64-hex validation for
  `authorization_decision_sha256` and optional `prev_event_hash`, focused
  regressions, chain replay and selected identity adjacency.
- Out of scope: authentication, authorization policy changes, provider/runtime
  activation, services, browser/API login, source-token/CAS replay, real
  projects, dependency installation and medical-writing paths.

## Success Criteria

- Uppercase, padded and non-string decision/predecessor hashes fail closed.
- Canonical hashes and the empty initial predecessor remain valid.
- Focused audit-chain and selected identity/readiness adjacency tests pass;
  compile and review-gate pass.
- Formal gate remains `read_only / blocked`; ports remain empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- No provider, runtime, browser, API login or real-project action is allowed
  while the authoritative gate remains blocked.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 18:39:29: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Re-anchored from latest AGENTS.md, P9 checkpoint/ledger and the
  current formal gate. Selected this bounded source-only seam because the audit
  `_sha256()` helper coerced, stripped and lowercased identity hashes.
- 2026-08-05: Required raw lowercase 64-hex decision/predecessor hashes and
  added uppercase, padded, non-string and empty-initial-predecessor regressions.
  Focused audit suite passed 15 tests; selected identity/readiness/route/upstream
  adjacency passed 92 tests; compile passed. Review-gate returned `ok=true`;
  final gate recheck remained `read_only / blocked` and all reserved ports were
  empty.
