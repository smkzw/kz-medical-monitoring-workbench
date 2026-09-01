# Codex Review: monitoring_p10_protocol_legacy_startup_recovery_fix_20260801

Date: 2026-08-01
Delegated-agent output: `runs/pi_monitoring_p10_protocol_legacy_startup_recovery_fix_20260801.md`

## Verdict

**Pass for the bounded startup-recovery correction.**

The live v5 startup/canary gate remained separate and was not accepted by this
review.

## Boundary Check

- Pi changed the three authorized implementation files and three authorized tests
  only; the runner persisted its own report.
- The worker did not start services, read/write runtime databases, call a provider,
  retry a job, or decide a candidate.
- The first faulty live startup was stopped before any canary POST. Codex restored
  only `medical_monitoring_ai.sqlite3` from the pre-canary consistent backup and
  verified integrity plus the `2 completed / 6 failed / 8 proposed` v4 baseline.

## Codex Verification

- Codex independently ran:
  `tests/test_monitoring_ai_repository.py`,
  `tests/test_monitoring_ai_startup_recovery.py`, and
  `tests/test_monitoring_protocol_preparation.py` -> **55 passed**, 0 failed.
- Python compilation of repository, preparation service, and `main.py` passed.
- A second real start through `scripts/start_stable_backend.zsh` proved the change
  against the restored runtime DB: all eight v4 terminal jobs and eight proposed
  candidates survived; protocol status returned to
  `2 candidate_review / 6 failed`.
- Readiness was ready, schema 16, missing capabilities empty; independent product AI
  remained configured without a Codex runtime dependency.

## Delegated-Agent Output Review

- The repository default remains unchanged when no legacy-terminal set is supplied.
- Only protocol-clause startup receives the explicit legacy set; other AI task types
  retain the normal prompt-cutover retirement behavior.
- Active legacy queued/running/blocked work still retires fail-closed, while only
  completed/failed v3/v4 history survives this cutover.
- Pi's first SQL construction error was corrected in the same pass and covered by
  focused tests; no fallback was used.

## Residual Risk

- Future prompt bumps must deliberately update the public legacy set.
- User-triggered retry semantics for preserved failed legacy jobs were not changed.
- This review accepts startup preservation only; it does not accept any provider
  candidate or protocol scientific result.
