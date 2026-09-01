# Task Context: medical_monitoring_p7c_20260729

Created: 2026-07-29 22:06:38
Objective: Implement the P7C medical-monitoring gold/shadow validation contract without production gold data or API/frontend/runtime changes
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `context/monitoring_gold_shadow_p7c_implementation_context.md`
- `reviews/monitoring_gold_shadow_p7c_inventory.md`
- `records/active_slices/medical_monitoring_goal_p7_20260729/TASK_CONTEXT.md`
- Current rule models, repository, lifecycle service, gold authority and adjacent tests.

## Scope

- In scope: the four P7C backend files named by the implementation contract,
  P7C-focused tests, and P7C handoff/metrics/review records.
- Out of scope: frontend, medical writing, shared AI, current API process,
  production runtime databases, real gold data, and P7B record-resolution files.
- No external dependency is needed. The change extends the existing dataclass,
  SQLite migration, repository and lifecycle patterns.

## Success Criteria

- Boolean cases have closed positive/negative/boundary labels in identity/hash.
- Diagnostic indeterminate cases use a separate immutable model/table/result set.
- Shadow runs freeze complete Boolean and diagnostic sets, coverage counts and
  authoritative project sets.
- Publish recomputes per-rule and first-family gates and fails closed on drift.
- SQLite migration is idempotent/readable and legacy rows remain ineligible.
- Focused, adjacent lifecycle and full medical-monitoring tests pass.

## Risk Boundaries

- Never create or write real production gold cases or touch runtime SQLite files.
- Preserve CM as non-study medication and EX/EC/DA/IP as study treatment.
- Do not infer live/attenuated vaccine status from J07 alone.
- Preserve unrelated concurrent work; baseline SHA-256 values were recorded
  before edits because this workspace is not a Git repository.
- Codex owns final verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 22:06:38: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29: Read all named contracts and the complete current model,
  repository, service and authority implementations. Chosen design keeps
  diagnostics separate and recomputes cross-project family authority from the
  existing immutable case registry instead of adding a duplicate qualification
  registry.
- 2026-07-29: Implemented closed Boolean coverage labels, independent diagnostic
  cases/results, complete-set and coverage hashes, idempotent migration, shadow
  revalidation, per-rule gates, and initial-family two-project authority gates.
- 2026-07-29: Preserved the legacy template `RULE_FAMILIES` contract and added a
  separate closed P7C extension for laboratory abnormality and CTCAE
  longitudinal worsening after direct extension caused a template-catalogue
  invariant failure.
- 2026-07-29: Final verification passed: 117 focused/adjacent tests and all 639
  medical-monitoring tests. Existing real-listing candidates remain explicitly
  ineligible for production release.
- 2026-07-29: Conflict review tightened family project qualification. A project
  now counts only when one exact family rule revision has positive, negative,
  boundary, and diagnostic evidence and every case for that revision passes the
  configured source/mapping/freeze authority validator. Negative-only and
  authority-invalid second projects do not count.
- 2026-07-29: A completed second-project shadow run was not made a prerequisite
  of the family evidence set because family coverage is hashed into the current
  run before that run can be persisted. The family set is therefore a frozen
  complete-coverage evidence gate; actual execution remains the responsibility
  of each publishing project's complete, all-pass repository shadow run.
- 2026-07-29: Post-review verification passed: 119 focused/adjacent tests and
  all 644 current medical-monitoring tests.
