# Task Context: medical_monitoring_b6_packet_freshness_20260803

Created: 2026-08-03 02:55:42
Objective: Revalidate the persisted B6 reviewer packet against current B6/C14 gates, formal provenance package, candidate fingerprints, and source manifest; fail closed on stale or mismatched evidence without granting reviewer or write authority.
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_monitoring_b6_reviewer_packet_20260802/B6_REVIEW_PACKET.json`
- `records/active_slices/medical_monitoring_formal_reviewer_provenance_package_20260802/B6_FORMAL_REVIEWER_PROVENANCE_PACKAGE.json`
- `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json`
- `runs/execution/medical_monitoring_phase_c14_b6_activation_gate_20260802/B6_TO_C13_ACTIVATION_GATE_REPORT.json`
- The formal package `source_manifest` and current filesystem bytes/SHA-256 observations for all 11 declared sources plus packet/package files.

## Scope

- In scope: pure revalidation module, focused tests, read-only freshness artifact, task record, review, metrics, and P10 loop trace.
- Out of scope: B6/C14/package/packet mutation, reviewer outcomes, medical or engineering approval, aggregate/CAS replay, source-token synthesis, migration, SQLite/runtime, service/provider/browser/API login, real project data, frontend, and 8911/5174.

## Success Criteria

- The revalidator must fail closed when the persisted packet is stale, while proving the current package source manifest and candidate/outcome bindings are intact.
- A synthetic packet with current explicit B6/C14/package bindings must validate as `fresh` without creating any reviewer outcome or authority.
- Focused tests, compile/lint checks, artifact replay, and workflow review-gate must pass.
- The current filesystem diagnostic must remain `stale` with authority/write/activation flags false and an explicit next safe action.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- No external agent, service, provider, browser, API/backend login, real project, or product source is started or modified.
- The revalidator is diagnostic only; a `fresh` packet is not a B6 approval and cannot grant medical, CAS, migration, activation, runtime, or write authority.
- The old packet is never overwritten; any future replacement requires a separately reviewed evidence-generation step.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 02:55:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Reopened latest global/workbench AGENTS, P10 ledger, B6 packet/package records, current B6/C14 files, and verified no service listeners on 8911/5174 in the surrounding checkpoint.
- 2026-08-03: Observed packet stale against current gate: old B6 SHA `758f5bd6...`, current B6 SHA `1f3df053...`; old C14 SHA `fe6c4686...`, current C14 SHA `44ea7c60...`; packet outcome count `0`, current B6 outcome count `5`.
- 2026-08-03: Added `services/api/app/monitoring_b6_reviewer_packet_revalidation.py` and focused tests. The contract replays 13 current file observations, package manifest, packet/package hashes, B6/C14 state, candidate fingerprints, outcome coverage, and authority flags without writes.
- 2026-08-03: Focused tests passed `10`; compile and ruff passed. Current historical packet artifact is `stale` with 15 explicit packet freshness issues; candidate/package/outcome/source-manifest identity is otherwise intact and all authority flags remain false.
- 2026-08-03: Parameterized the contract's four workspace-relative binding paths and added a 10th focused test for a new packet path.
- 2026-08-03: Built `B6_REVIEW_PACKET_REFRESH.json` without overwriting the historical packet. It binds current B6/C14/package hashes, has five exact candidates, no reviewer outcomes, and replays as `fresh` with zero issues. Refresh revalidation remains read-only and all authority flags are false.
- 2026-08-03: Final self-review added a gate-top-level `migration_write_permitted=true` injection test; focused regression is 11/11 and the adjacent B6/CAS/release/real-loop set is 137/137. Review-gate is green.
