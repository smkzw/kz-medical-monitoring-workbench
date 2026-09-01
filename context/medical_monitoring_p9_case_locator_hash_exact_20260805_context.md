# Task Context: medical_monitoring_p9_case_locator_hash_exact_20260805

Created: 2026-08-05 11:33:21
Objective: Harden gold and diagnostic evidence locator binding so source content digests remain exact lowercase SHA-256 bytes
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rules.py`: gold and diagnostic case factories and evidence-locator binding.
- `services/api/app/monitoring_protocol_rule_repository.py`: persisted case reconstruction through evidence and source-row locator JSON.
- `tests/test_monitoring_protocol_rules.py` and `tests/test_monitoring_protocol_rule_repository_hardening.py`: focused factory and SQLite tamper regressions.
- The active real-loop gate at `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` remains read-only/blocked.

## Scope

- In scope: require the exact raw lowercase source-content SHA-256 bytes to appear in gold/diagnostic evidence locators; add focused factory and persisted-read regressions.
- Out of scope: locator text normalization unrelated to the digest, clinical rule semantics, provider/runtime/browser activation, real projects, dependency installation, and medical-writing paths.

## Success Criteria

- Uppercase digest text in otherwise valid evidence locators fails closed rather than passing via `locator.lower()`.
- Valid canonical locators continue to load and case identity remains stable.
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

- 2026-08-05 11:33:21: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 11:34-11:36: Codex direct route selected; no external Hermes/provider dispatch. Replaced case locator digest membership checks with exact raw matching and added factory plus persisted locator tamper regressions.
- 2026-08-05 11:36: Focused rule/repository suite **65 passed**; protocol adjacency **57 passed, 1 warning**; gold-shadow plus shadow-sample adjacency **57 passed, 1 warning**; daily adjacency **96 passed, 41 subtests**.
- 2026-08-05 11:36: Gate remains `read_only / blocked`; authority flags remain false and ports 8911/5174/8910/4173 remain empty.
