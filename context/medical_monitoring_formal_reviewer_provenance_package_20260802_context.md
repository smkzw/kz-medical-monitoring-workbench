# Task Context: medical_monitoring_formal_reviewer_provenance_package_20260802

Created: 2026-08-02 19:35:30
Objective: Assemble a current hash-bound formal B6 reviewer/provenance package including engineering defer state, source inventory/archive qualification, and read-only aggregate/CAS evidence without granting approval or runtime authority
Task type: `high_risk_contradiction_review`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `runs/execution/medical_monitoring_phase_b3_mapping_dryrun_20260801/MAPPING_REVIEW_AND_DRYRUN.json`
- `runs/execution/medical_monitoring_phase_b4_residual_decision_20260801/B4_RESIDUAL_DECISION_PACKAGE.json`
- `runs/execution/medical_monitoring_phase_b5_mapping_approval_gate_20260801/APPROVAL_GATE_ASSERTIONS.json`
- `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json`
- `runs/execution/medical_monitoring_phase_c14_b6_activation_gate_20260802/B6_TO_C13_ACTIVATION_GATE_REPORT.json`
- `records/active_slices/medical_monitoring_goal_p10_20260730/RELEASE_GATE_AUDIT_20260802.md`
- `records/active_slices/medical_monitoring_release_evidence_coverage_20260802/CURRENT_RELEASE_COVERAGE.json`
- `records/active_slices/medical_monitoring_my009_source_inventory_recheck_20260802/SOURCE_INVENTORY.json`
- `records/active_slices/medical_monitoring_my009_archive_member_inventory_20260802/ARCHIVE_MEMBER_INVENTORY.json`
- `records/active_slices/medical_monitoring_aggregate_cas_replay_contract_20260802/B4_AGGREGATE_CAS_REPLAY.json`

The generated package records byte counts and SHA-256 for every binding input;
the filesystem remains the source of truth. This is an evidence-reconstructed
continuation, not restoration of deleted parent JSONL or an original dialogue.

## Scope

- In scope: assemble a current hash-bound reviewer/provenance handoff for five
  B6 candidates; copy current engineering `pending_review` defer state; bind
  source inventory/archive and aggregate/CAS evidence; expose exact medical,
  source-lineage, aggregate-CAS and external-action fields still not provided.
- Out of scope: generating medical outcomes, approving/rejecting candidates,
  synthesizing source tokens, writing B6/C14/runtime state, aggregate mutation,
  migration, API/provider/browser/service execution, real projects, or product
  source/medical-writing changes.

## Success Criteria

- Package is JSON-valid, deterministic, read-only and hash-bound.
- All five current candidate IDs/fingerprints and current B6 `pending_review`
  engineering defer state are reproduced exactly; no medical outcome is
  fabricated.
- Eleven source/evidence inputs are listed with path, byte count and SHA-256;
  current B6/C14/release status and the two CAS replay cases are represented.
- Authority flags remain false, reviewer fields remain `not_provided`, and
  CAS evidence explicitly retains five missing-`expected_version` issues.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 19:35:30: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 19:36–19:42: Direct Codex assembled the package without dispatching
  the route suggested by the task initializer; the user requested autonomous
  execution and no execution/conference mechanism was started.
- 2026-08-02: Package construction bound eleven current source/evidence files,
  five B6 candidates, two aggregate cases and all current gate statuses. Every
  authority flag is false; required reviewer inputs are `not_provided`.
- 2026-08-02: JSON/hash assertions passed; after binding the 4.29 source-token
  scan, package SHA is
  `fa9f37fcc3c6314e7ddf743336a0b0ceb2e341ff5eb00fb415508212ac02710c` and
  file SHA is `a9e2664307dc5a7224e35fc7b57b0bd231c91959de5e925469411e311efffd68`.
