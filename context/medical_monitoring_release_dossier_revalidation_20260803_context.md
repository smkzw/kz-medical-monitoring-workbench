# Task Context: medical_monitoring_release_dossier_revalidation_20260803

Created: 2026-08-03 01:36:19
Objective: Add a pure read-only contract that reopens a persisted commercial release dossier JSON, reconstructs the canonical dossier object, verifies derived status/blockers/digest and safe file identity, and never grants release authority.
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_release_dossier.py` (canonical dossier dataclasses, sections, control partitions, signoffs and residual-risk rules)
- `services/api/app/monitoring_release_evidence_revalidation.py` (direct-file bytes/SHA and read-only report pattern)
- `records/active_slices/medical_monitoring_release_evidence_revalidation_20260803/RELEASE_EVIDENCE_REVALIDATION.json` (current release remains blocked)
- `AGENTS.md` and `/Users/smkzw/.codex/AGENTS.md` (safe filesystem, evidence and review-gate rules)
- Current workbench filesystem is authoritative. No service, provider, browser, SQLite, real-project or 8911/5174 interaction is in scope.

## Scope

- In scope: one pure Python module plus focused tests and task evidence. It reconstructs `MonitoringReleaseDossier` from a persisted JSON mapping, compares canonical derived status/blockers/release-ready/digest fields, and optionally reopens a direct workspace-relative JSON file with byte/SHA checks.
- In scope: synthetic complete and blocked dossiers only; the current real release remains a diagnostic blocked state.
- Out of scope: changing release decisions, B6/C14, source-token/CAS, runtime or migration, real-project sources, Playwright, providers/API/SQLite, frontend, medical-writing, or creating signoffs/UAT/operational evidence.

## Success Criteria

- Valid persisted dossier JSON can be reconstructed through the existing canonical dataclasses; all required sections/signoffs/residual-risk rules remain enforced by the existing contract.
- Missing/malformed sections, authority/readiness drift, derived status/blocker/digest drift, unsafe paths, missing/non-file/symlink/byte/SHA drift, and invalid JSON fail closed with typed issues.
- A valid dossier report is immutable/hash-bound, exposes `fresh` separately from observed dossier readiness, and forces `read_only=true`, `authority_granted=false`.
- Focused tests, compile, Ruff, and adjacent release regressions pass; 8911/5174 and protected frontend hashes remain unchanged.
- Evidence explicitly says that a fresh persisted dossier proves semantic/file identity only, not actual UAT, medical acceptance or release approval.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Never treat `release_ready=true` inside a persisted payload as permission; it must match the canonical object and the report remains non-authoritative.
- Reject absolute/traversal/symlink paths and do not read files outside the workbench.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 01:36:19: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Existing release dossier and release-evidence contracts inspected. Decision: add a persisted-payload/file boundary rather than trusting an in-memory dossier or a bare file hash.
- 2026-08-03: Added canonical reconstruction, derived-field/digest comparison, safe direct-file JSON identity and focused semantic/file drift tests. Current active slice has no declared persisted dossier and remains blocked.
- 2026-08-03: Full monitoring regression captured at 1712 passed/25 existing warnings; later focused-only edge-case hardening brought the current adjacent subset to 55 passed without product-code changes.
