# Task Context: medical_monitoring_phase_b6_review_gate_20260801

Created: 2026-08-01 23:43:55
Objective: Build a read-only B6 explicit review-outcome and approved-input dry-run gate for the five risk identity mapping candidates; accept only hash-bound residual-free external evidence and never write runtime state
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_risk_mapping.py`
- `services/api/app/medical_risk_mapping_approval.py`
- `tests/test_medical_risk_mapping_approval.py`
- `runs/execution/medical_monitoring_phase_b3_mapping_dryrun_20260801/MAPPING_REVIEW_AND_DRYRUN.json`
- `runs/execution/medical_monitoring_phase_b4_residual_decision_20260801/B4_RESIDUAL_DECISION_PACKAGE.json`
- `runs/execution/medical_monitoring_phase_b5_mapping_approval_gate_20260801/APPROVAL_GATE_ASSERTIONS.json`
- Phase B B1-B5 context/review/metrics records and the current project checkpoint.
- Current filesystem is authoritative; no runtime database or service is an allowed write target.

## Scope

- In scope: a strict B6 review-outcome schema/validator and a read-only approved-input
  dry-run harness that can consume explicit, hash-bound external outcomes without
  persisting a mapping or changing a disposition.
- In scope: an actual-clone assertion/report that remains `pending_review` when no
  independent review input exists, plus focused tests and evidence records.
- Out of scope: inventing medical/engineering approval; modifying B3/B4/B5 evidence;
  runtime migration, dual-read/dual-write, service start, API POST, UI work, or
  authoritative database writes; any v9-v12 job action; touching 18911/PID 43191.

## Success Criteria

1. Every input outcome is bound to the exact candidate record id and candidate
   fingerprint; candidate-set and B4 residual decision hashes must match.
2. `approve` is accepted only with reviewer, timezone-aware timestamp, source evidence,
   and an empty residual-blocker list; any missing/stale/ambiguous outcome fails closed.
3. The harness produces only an in-memory remap/dry-run projection and explicitly keeps
   `approved=false`/`write_permitted=false` unless valid external evidence is supplied.
4. With the current filesystem (no external review file), the actual result is
   `pending_review`, `migration_ready=false`, and no runtime state changes.
5. Focused tests, pycompile/Ruff, and the workflow review gate pass; records include
   evidence hashes, exact scope, uncertainty, and next action.

## Risk Boundaries

- This is a Codex-direct offline task; no external agent or conference is used.
- No approval may be synthesized from B4 package fields, candidate confidence, or
  historical source matching. The absence of an independent review input is a real
  pending state.
- Do not write to the authoritative runtime, migrate the clone, start 8911/5174, or
  touch 18911/PID 43191. Do not retry/reuse/salvage/reclassify v9-v12.
- Use only task-scoped source/tests/evidence paths and preserve unrelated user work.
- Codex remains final authority and must review all diffs and decisive checks.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 23:43:55: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01 23:44: direct task contract filled; B6 remains pending on independent
  explicit review outcomes and is limited to a non-writing gate.
- 2026-08-01 23:49: added the hash-bound review outcome model, strict gate evaluator,
  and actual-clone read-only harness. No review input was present, so the frozen result
  is `pending_review`, `migration_ready=false`, `write_permitted=false`; B1-B6 plus the
  existing risk compatibility set passed `117 tests, 17 warnings`. Next action remains
  authorized explicit review, not migration.
