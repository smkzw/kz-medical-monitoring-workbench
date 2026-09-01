# Task Context: monitoring_p10_protocol_legacy_startup_recovery_fix_20260801

Created: 2026-08-01 01:35:18
Objective: Preserve terminal v3/v4 RUX protocol jobs and proposed candidates as read-only legacy audit evidence across backend startup while still retiring queued/running/blocked obsolete prompt work; add repository and startup recovery regressions; do not start services or write runtime data.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `deepseek` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem is authoritative.
- Parent canary context:
  `context/monitoring_p10_loop316_protocol_v5_visit_canary_20260801_context.md`.
- Reproduction:
  - before startup, RUX v4 protocol jobs were 2 completed / 6 failed and all 8
    candidates were proposed;
  - after one normal backend startup, all 8 v4 jobs became
    `stale_input/superseded_prompt_contract`, all 8 candidates became superseded and
    protocol status became 8 ready/no-job;
  - no canary POST occurred;
  - Codex stopped 8911 and restored `medical_monitoring_ai.sqlite3` from the exact
    pre-canary backup; integrity is OK and the 2 completed / 6 failed / 8 proposed
    baseline is restored.
- Relevant sources:
  - `services/api/app/monitoring_ai_repository.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
  - `services/api/app/main.py`
  - `tests/test_monitoring_ai_repository.py`
  - `tests/test_monitoring_ai_startup_recovery.py`
  - `tests/test_monitoring_protocol_preparation.py`
- Baseline SHA-256 values:
  - repository: `532d688075c52eff1b58b31412ac1c78ce5191674b5eef7e88281c09f272f197`
  - protocol preparation service:
    `97f2a50c61e71d2bffbc90b33de3e1a9cc005df0542b759519cbea77d1938713`
  - main: `e00da4ec5d7c0e0a98c4ad9e280eacb7654f42eaeeeba17ab6ff61f6da3f4a06`
  - repository tests:
    `d9a441a83ed46e9ab6a4a8899537695bd2032bedf36341448f850eda1183027b`
  - startup tests:
    `7ffa6817576e0d6a7a17512cbbb6ae34fb51824992b8de5eab773cbfb7469af6`
  - protocol preparation tests:
    `8c8cfae53e57dd50d7fb63fd8aaf4db8b2a08265518aa17ad2b8eec08c08d7e6`

## Scope

- Writable paths are exactly the six source/test files above.
- In scope:
  - extend the repository prompt-cutover primitive with an explicit terminal legacy
    preservation contract;
  - preserve only completed/failed jobs for explicitly supplied legacy prompt versions;
  - continue retiring obsolete queued/running/blocked work and terminal versions not in
    the supplied legacy set;
  - preserve proposed candidates only for the preserved terminal legacy jobs;
  - have startup pass the protocol preparation v3/v4 legacy set only for
    `PROTOCOL_CLAUSE_STRUCTURING`;
  - keep all other task types' current cutover behavior unchanged;
  - add repository-level and startup-level positive/negative regressions;
  - retain existing protocol status tests.
- Out of scope:
  - no service start, runtime database access/write, provider call, real canary, job
    retry or candidate decision;
  - no change to prompt v5, typed repair, job identity, medical validators or medical
    writing;
  - no broad refactor.

## Success Criteria

- Repository API takes an explicit immutable collection of terminal legacy prompt
  versions; default empty collection preserves existing behavior.
- For an explicitly preserved legacy version:
  - completed and failed jobs remain terminal;
  - their proposed candidates remain proposed;
  - queued, running and blocked jobs still become stale and cannot wake after restart.
- Obsolete completed/failed jobs outside the preserved set still become stale and their
  proposed candidates become superseded.
- Current-version work remains unchanged.
- Startup passes exactly v3/v4 only for protocol clause structuring and passes no legacy
  exemption for other monitoring AI task types.
- Focused repository, startup recovery and protocol preparation tests pass.

## Risk Boundaries

- Edit only the six authorized paths and preserve unrelated concurrent work.
- Do not solve this by skipping protocol prompt cutover entirely; obsolete active work
  must still fail closed.
- Do not treat `blocked` as preserved terminal audit evidence; the status compatibility
  contract permits only completed/failed v3/v4.
- Do not restore or mutate runtime data; Codex already restored the exact pre-start
  backup and owns live verification.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 01:35:18: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01: Six current files and hashes frozen; 8911/5174 both stopped.
