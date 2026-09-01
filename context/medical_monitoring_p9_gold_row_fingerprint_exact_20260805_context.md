# Task Context: medical_monitoring_p9_gold_row_fingerprint_exact_20260805

Created: 2026-08-05 11:21:02
Objective: Harden gold source-row fingerprint admission and persisted read-back so row lineage hashes remain exact lowercase SHA-256 bytes
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rules.py`: gold source-row binding factory and legacy mapping reader.
- `services/api/app/monitoring_protocol_rule_repository.py`: persisted gold-case reconstruction through `source_row_bindings_json`.
- `tests/test_monitoring_protocol_rules.py` and `tests/test_monitoring_protocol_rule_repository_hardening.py`: focused admission and SQLite tamper regressions.
- The active real-loop gate at `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` remains read-only/blocked.

## Scope

- In scope: make gold source-row fingerprints exact raw lowercase 64-hex SHA-256 values at both factory and persisted read boundaries; add focused regressions and evidence.
- Out of scope: clinical rule semantics, other source hashes, provider/runtime/browser activation, real projects, dependency installation, and medical-writing paths.

## Success Criteria

- Padded, uppercase and non-string row fingerprints fail closed rather than being normalized.
- Valid canonical fingerprints continue to load and gold/diagnostic case identity remains stable.
- Focused and adjacent suites pass; changed modules compile; prompt preflight and review-gate pass.
- No services/providers/browsers/real projects or dependency activation while the gate is blocked.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 11:21:02: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 11:22-11:25: Codex direct route selected; no external Hermes/provider dispatch. Replaced row-fingerprint normalization with exact raw validation and added factory plus SQLite read-back shape regressions.
- 2026-08-05 11:25: Focused suite 63 passed; protocol adjacency 57 passed with one existing deprecation warning; shadow/sample adjacency 56 passed with one existing deprecation warning; daily adjacency 96 passed with 41 subtests; collect-only inspection of the MY008 real fixture collected one test but was not executed under the gate.
- 2026-08-05 11:25: Gate rechecked as `read_only / blocked`; authority flags remain false and ports 8911/5174/8910/4173 remain empty.
