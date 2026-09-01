# Task Context: medical_monitoring_rereview_reason_hash_read_shape_revalidation_20260805

Created: 2026-08-05 06:54:08
Objective: Harden persisted monitoring rule re-review reason hash read shape without runtime activation
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rule_repository.py` (`_re_review_from_row`)
- `tests/test_monitoring_protocol_rule_repository_hardening.py` (re-review persistence tamper coverage)
- Current filesystem and the active read-only gate; no runtime or real-project data is in scope.

## Scope

- In scope: exact canonical validation of persisted re-review `reason_sha256`; extend its existing tamper test to cover uppercase hash and reason-content drift.
- Out of scope: re-review workflow policy, medical assessment, schema changes, runtime activation, services/ports, browser/Playwright, providers, real projects, B6/C14 and commercial-release claims.

## Success Criteria

- Uppercase/padded/non-hex reason hashes fail closed before re-review task reconstruction.
- Existing status mutability and reason-content mismatch behavior remains green.
- Compileall/Ruff pass and required ports remain empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not dispatch the guard-emitted route: authority remains read-only with provider/runtime activation forbidden. Codex performs this source-only slice directly.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 06:54:08: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: `_re_review_from_row` now rejects non-canonical reason hashes before comparing reason content; existing tamper coverage now asserts uppercase-hash rejection followed by reason-hash mismatch. Focused hardening suite: 25 passed in 0.81s. Filtered adjacent protocol/lifecycle/gold-shadow suite: 121 passed in 6.66s (`real_` excluded). Compileall and Ruff passed; ports 8911/5174/8910/4173 are empty.
