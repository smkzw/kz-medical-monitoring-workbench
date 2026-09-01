# Task Context: medical_monitoring_re_review_task_read_identity_revalidation_20260805

Created: 2026-08-05 04:03:51
Objective: Harden persisted monitoring re-review task read hydration with deterministic identity validation while preserving mutable review status and legacy behavior
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rule_repository.py` (`_re_review_from_row`, task persistence/list readers)
- `services/api/app/monitoring_protocol_rules.py` (`RuleReReviewTask.create`, `RuleRiskBinding`)
- `tests/test_monitoring_protocol_rules.py`, `tests/test_monitoring_protocol_rule_review_boundaries.py`, and `tests/test_monitoring_protocol_rule_repository_hardening.py`
- Current filesystem state and the prior P10 LOOP ledger under `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`.
- Existing real-loop/release gates remain authoritative and blocked; this slice is source-only and cannot activate runtime or external providers.

## Scope

- In scope: inspect the direct re-review task row hydrator; add deterministic read-side identity validation for persisted immutable fields, while preserving a separately mutable task status.
- In scope: add focused tamper and restart/idempotence regressions, run focused and adjacent source-only tests, compile/Ruff checks, hashes, evidence, and review gate.
- Out of scope: services, ports, browsers/Playwright, real project data, external providers, medical judgments, release activation, or changes outside the workbench.

## Success Criteria

- A persisted task whose immutable fields or deterministic task ID are tampered with fails closed on read.
- A valid task round-trips unchanged, including any supported mutable status; existing re-review lifecycle/boundary tests remain green.
- Focused and adjacent tests, compileall, Ruff, and reserved-port checks pass; evidence records exact commands, counts, hashes, warnings, and residual limits.
- Review gate reports `ok: true` with no warnings/errors.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Keep legacy rows readable only where the current schema explicitly allows them; do not silently weaken deterministic identity checks for complete modern rows.
- The task status is a lifecycle field and must not be included in immutable task-ID reconstruction; preserve it after validating immutable identity.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 04:03:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 04:04:00: Codex direct execution selected; no external provider or sub-agent dispatch is permitted in this turn.
- 2026-08-05: Added `reason_sha256` migration/backfill and canonical re-review task read validation; focused suite reached 58 passed.
- 2026-08-05: Final adjacent groups reached 337 passed; shadow/P7C completed after 722.08s with one pre-existing openpyxl warning; authoring group retained two pre-existing warnings.
- 2026-08-05: compileall and Ruff passed, reserved ports remained free, and no runtime/provider/browser/real-project action occurred.
- 2026-08-05: Review gate is ready for Codex direct completion with no warnings/errors; residual authority and commercial-release gates remain blocked.
