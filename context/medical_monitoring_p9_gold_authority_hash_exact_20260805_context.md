# Task Context: medical_monitoring_p9_gold_authority_hash_exact_20260805

Created: 2026-08-05 11:37:03
Objective: Harden gold-case authority and release binding source hash comparisons so registered and attached source digests remain exact lowercase SHA-256 bytes
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_gold_case_authority.py`: source registry, attached batch and normalized-row hash authority.
- `services/api/app/monitoring_protocol_rule_repository.py`: release-binding evidence locator prechecks.
- `tests/test_monitoring_gold_case_authority.py`, `tests/test_monitoring_protocol_rule_repository_hardening.py`, and adjacent protocol/shadow suites.
- The active real-loop gate at `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` remains read-only/blocked.

## Scope

- In scope: make authority and release-binding source hash comparisons exact raw lowercase 64-hex values; make explicit normalized-row locator hashes exact; add focused regressions and evidence.
- Out of scope: clinical rule semantics, non-hash locator text normalization, provider/runtime/browser activation, real projects, dependency installation, and medical-writing paths.

## Success Criteria

- Uppercase, padded or non-string source hashes fail closed at authority/release boundaries rather than being normalized or crashing.
- Valid canonical source/row hashes continue to bind the same source and batch.
- Focused and adjacent suites pass; changed modules compile; preflight and review-gate pass.
- No services/providers/browsers/real projects or dependency activation while the gate is blocked.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 11:37:03: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 11:37-11:40: Codex direct route selected; no external Hermes/provider dispatch. Replaced authority and release-binding source hash normalization with exact raw comparisons and added authority/locator regressions.
- 2026-08-05 11:40: Authority plus rule/repository suite **104 passed**; protocol adjacency **57 passed, 1 warning**; gold-shadow plus shadow-sample adjacency **57 passed, 1 warning**; daily adjacency **96 passed, 41 subtests**.
- 2026-08-05 11:40: Gate remains `read_only / blocked`; authority flags remain false and ports 8911/5174/8910/4173 remain empty.
