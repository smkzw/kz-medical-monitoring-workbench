# Task Context: medical_monitoring_batch_root_read_shape_revalidation_20260805

Created: 2026-08-05 04:34:22
Objective: Harden persisted monitoring batch root reads with normalized domain/proof shape and frozen-state consistency validation
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_batch_repository.py` (`BatchRecord`,
  `_batch_from_row`, batch creation/transition/evidence paths)
- `tests/test_monitoring_batch_repository.py` plus batch service/diff/rule-runner,
  field-profile, daily-run, AI, gold-case, mapping-lifecycle and API consumers.
- Current filesystem state and `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`.
- Real-loop/release gates remain authoritative and blocked; this slice is
  source-only and cannot activate runtime or external providers.

## Scope

- In scope: fail closed on malformed or non-canonical persisted expected-domain
  JSON, full-snapshot proof shape, invalid state/version, and frozen timestamp
  combinations when a batch root is read.
- In scope: add focused shape regressions, run focused and adjacent batch/
  mapping/daily-run/AI tests, compile/Ruff checks, hashes, evidence, and review
  gate.
- Out of scope: services, ports, browsers/Playwright, real project data,
  external providers, medical judgments, release activation, or changes
  outside the workbench.

## Success Criteria

- Valid batch roots round-trip unchanged across get/list/restart and existing
  state-machine gates remain green.
- Persisted domain/proof/timestamp shape tampering fails closed before a batch
  can feed field profiles, mapping, daily runs, or assurance.
- Focused and adjacent tests, compileall, Ruff, and reserved-port checks pass;
  evidence records exact commands, counts, hashes, warnings, and residual
  limits.
- Review gate reports `ok: true` with no warnings/errors.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not introduce a new batch identity scheme; this slice validates the
  existing persisted root shape and state contract only.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 04:34:22: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 04:35:00: Codex direct execution selected; no external provider or sub-agent dispatch is permitted in this turn.
- 2026-08-05: Implemented and verified the bounded root-read shape/state checks;
  focused 46 and adjacent 131 passed, compileall/Ruff passed, reserved ports
  remained free, and the Hermes review gate returned `ok: true`.
- 2026-08-05: Next action is another bounded source-only P7/P8/P9 integrity gap;
  provider/runtime/real-loop gates remain closed.
