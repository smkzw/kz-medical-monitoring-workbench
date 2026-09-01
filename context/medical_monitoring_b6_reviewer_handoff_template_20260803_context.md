# Task Context: medical_monitoring_b6_reviewer_handoff_template_20260803

Created: 2026-08-03 01:57:29
Objective: Add a deterministic read-only B6 reviewer-resolution template generator bound to the current formal reviewer package and B3/B4 hashes; keep reviewer decisions empty and all authority flags false.
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_formal_reviewer_resolution.py` (canonical submitted-resolution validator)
- `records/active_slices/medical_monitoring_formal_reviewer_provenance_package_20260802/B6_FORMAL_REVIEWER_PROVENANCE_PACKAGE.json` (current package and candidate fingerprints)
- `records/active_slices/medical_monitoring_b6_reviewer_packet_20260802/B6_REVIEW_PACKET.json` (current gate state and required reviewer fields)
- Current B6/C14 gate files and P10 ledger; current filesystem is authoritative.
- Global `/Users/smkzw/.codex/AGENTS.md` and workbench `AGENTS.md` govern evidence, review-gate and no-authority boundaries.

## Scope

- In scope: a pure helper that generates a deterministic `medical_monitoring_formal_reviewer_resolution_v1` template from a hash-verified package, carries candidate IDs/fingerprints and B3/B4 source hashes, leaves all reviewer/medical/lineage/CAS/evidence/rationale fields empty, plus focused tests and an active-slice template artifact.
- Out of scope: filling reviewer decisions, inferring medical conclusions, revalidating source tokens, replaying aggregate/CAS, modifying B6/C14, writing SQLite/API/runtime, starting services/providers/browser, or changing real projects/frontend/medical-writing.

## Success Criteria

- Template generation rejects non-mapping or package-hash-invalid packages and requires unique candidate identities and exactly one B3/B4 source hash.
- Every current candidate appears once with exact fingerprint and source hashes; all authority fields are explicit false and no decision is prefilled.
- Passing the template through the existing validator returns `invalid` with explicit missing reviewer/outcome evidence issues, never a valid or authoritative report.
- Template output is deterministic/hash-bound and the current package hash is visible; focused and adjacent tests, compile/Ruff/review-gate pass.
- Evidence states clearly that the artifact is a reviewer handoff, not a B6 outcome or approval.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Never default a candidate to approve/reject/defer; blank fields are intentional and must remain human-supplied.
- Never set medical, engineering, write, migration or activation authority true.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 01:57:29: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Current B6 packet was re-opened; five candidate outcomes are still absent. Decision: add a deterministic handoff template to reduce reviewer input friction without changing the pending gate.
- 2026-08-03: Added the template generator and current five-row artifact. Replay through the existing validator returned `invalid` with 40 explicit missing-input issues; all authority flags remained false.
