# Task Context: medical_monitoring_mapping_draft_read_anchor_revalidation_20260805

Created: 2026-08-05 04:24:41
Objective: Harden persisted monitoring mapping-draft reads with deterministic anchor and input-revision validation while preserving editable fields and lifecycle status
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_mapping_draft_repository.py` (`_draft_from_row`, draft assembly/read paths)
- `services/api/app/monitoring_ai_contracts.py` (`MonitoringAiInputRevision.revision_sha256`)
- `tests/test_monitoring_mapping_draft_repository.py` and adjacent mapping,
  daily-run, AI, rule, and API suites.
- Current filesystem state and `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`.
- Real-loop/release gates remain authoritative and blocked; this slice is
  source-only and cannot activate runtime or external providers.

## Scope

- In scope: validate mapping-draft anchor fields and input-revision digest at
  read time, while preserving editable fields, version, status, and confirmed
  revision lifecycle state.
- In scope: add focused tamper regressions, run focused and adjacent mapping/
  daily-run/AI/rule/API tests, compile/Ruff checks, hashes, evidence, and
  review gate.
- Out of scope: services, ports, browsers/Playwright, real project data,
  external providers, medical judgments, release activation, or changes
  outside the workbench.

## Success Criteria

- A persisted draft whose deterministic anchor or input-revision JSON drifts
  fails closed on read.
- A valid draft with edited fields or mutable status round-trips unchanged;
  existing mapping lifecycle/semantic gates remain green.
- Focused and adjacent tests, compileall, Ruff, and reserved-port checks pass;
  evidence records exact commands, counts, hashes, warnings, and residual
  limits.
- Review gate reports `ok: true` with no warnings/errors.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not recompute the editable field content into `draft_id`; only the
  assembly anchor fields used by the existing ID contract are immutable.
- Do not require live AI source reassembly merely to read a valid draft; source
  freshness remains enforced at assembly/confirmation boundaries.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 04:24:41: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 04:25:00: Codex direct execution selected; no external provider or sub-agent dispatch is permitted in this turn.
- 2026-08-05: Centralized the existing draft-ID assembly seed and added read-side input-revision/anchor/lineage checks; focused mapping suite reached 47 passed.
- 2026-08-05: Mapping/AI/daily-run/rule/API adjacent group reached 709 passed; compileall and Ruff passed; reserved ports remained free.
- 2026-08-05: Review evidence is ready for Codex direct completion; no runtime/provider/browser/real-project action occurred and real-loop/release gates remain blocked.
- 2026-08-05 04:25:00: Codex direct execution selected; no external provider or sub-agent dispatch is permitted in this turn.
