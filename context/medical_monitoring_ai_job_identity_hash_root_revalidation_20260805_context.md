# Task Context: medical_monitoring_ai_job_identity_hash_root_revalidation_20260805

Created: 2026-08-05 05:47:09
Objective: Fail closed on malformed persisted monitoring AI job identifiers and SHA root fields
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_repository.py` (`_job()` and persisted job
  schema/lifecycle fields).
- `tests/test_monitoring_ai_repository.py` and the adjacent monitoring-AI,
  module-contract and risk-bridge suites.
- Current filesystem state and
  `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`.
- Real-loop and release gate records remain authoritative and blocked; this
  slice is source-only and cannot activate runtime or external providers.

## Scope

- In scope: require non-empty persisted job identity/contract text, canonical
  lowercase input hashes and optional output hash; preserve list reads with
  `strict_input_identity=False`; add focused/adjacent verification, hashes and
  evidence records.
- Out of scope: services, ports, browsers/Playwright, API login, real project
  data, external providers, medical judgments, schema migration, runtime/
  release activation and B6/C14 authority changes.

## Success Criteria

- Valid AI jobs round-trip unchanged across get/list/lifecycle reads.
- Missing identity text or non-canonical persisted hashes fail closed before a
  job is returned, without changing the existing list revision policy.
- Focused/adjacent tests, compileall, Ruff and reserved-port checks pass; the
  evidence records exact counts, hashes, warnings and residual limits.
- Hermes review gate reports `ok: true` with no warnings/errors.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 05:47:09: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Codex direct source-only implementation selected; no Hermes
  execution session, provider call or sub-agent dispatch.
- 2026-08-05: Added strict job identity/contract text and canonical hash reads,
  preserving empty output-hash compatibility; added two persisted-root
  regressions. Focused 94 and adjacent 839 passed; compileall/Ruff passed;
  reserved ports remained free.
- **Residual/next**: AI-job root integrity does not prove queue/provider
  quality, clinical correctness, browser usability, formal B6 review, C14
  activation or commercial release. Keep runtime gates closed and proceed only
  with another bounded structural source-only gap.
