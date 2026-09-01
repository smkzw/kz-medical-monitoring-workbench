# Task Context: medical_monitoring_nonfunctional_evidence_revalidation_20260803

Created: 2026-08-03 01:23:50
Objective: Add a pure, read-only, fail-closed contract that reopens declared commercial nonfunctional/install/rollback/security/SBOM/audit/operations evidence, verifies path/bytes/SHA/control coverage, and never grants release authority.
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_release_dossier.py` (canonical commercial dossier sections/control vocabulary)
- `services/api/app/monitoring_release_evidence_revalidation.py` (existing read-only filesystem/hash-bound evidence pattern)
- `records/active_slices/medical_monitoring_release_evidence_revalidation_20260803/RELEASE_EVIDENCE_REVALIDATION.json` (current release snapshot; fresh but blocked)
- `records/active_slices/medical_monitoring_release_dossier_contract_20260802/TEST_EVIDENCE.md` (existing dossier contract boundary and current stop conditions)
- `AGENTS.md` and `/Users/smkzw/.codex/AGENTS.md` (execution, evidence, and token rules)
- Current filesystem is authoritative; no real-project source, service, provider, browser, SQLite, or 8911/5174 interaction is in scope.

## Scope

- In scope: one pure Python revalidation module plus focused tests and task evidence. The module accepts a declared manifest of commercial evidence records, reopens direct files, verifies relative safe paths, bytes, SHA-256, typed control IDs/statuses, duplicate/unknown/missing controls, and read-only/non-authoritative flags.
- In scope: a diagnostic fixture using synthetic files only; it must report the current real nonfunctional evidence as absent/blocked rather than manufacture completion.
- Out of scope: changing the release gate/dossier status, B6/C14, source-token/CAS, runtime or migration, real projects, browser/Playwright, providers, API/SQLite, frontend, medical-writing subsystem, or creating production evidence.

## Success Criteria

- Required nonfunctional/install/rollback/security/SBOM/audit/operations control IDs form an explicit closed set and each declared record maps to exactly one allowed control.
- A complete synthetic manifest is fresh only when all declared direct files exist, are regular non-symlink files, and match both recorded byte length and SHA-256; missing, drifted, unsafe, duplicate, unknown, or malformed records fail closed with typed issues.
- The report is immutable/hash-bound, exposes fresh/match/unmet counts, and enforces `read_only=true`, `authority_granted=false`, and `release_ready=false`.
- Focused tests, compile, Ruff, and adjacent commercial-release regressions pass; 8911/5174 remain stopped and protected frontend hashes remain unchanged.
- Evidence records explicitly state that synthetic freshness is not real UAT, release approval, or a substitute for B6/real-loop gates.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Never interpret a fresh evidence manifest as approval or as proof that an operational rehearsal actually occurred; the contract only verifies declared artifact identity and control coverage.
- Do not use absolute paths, path traversal, symlinks, or arbitrary workspace escape in a manifest.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 01:23:50: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Existing dossier/release contracts inspected; no reusable filesystem contract currently validates the commercial nonfunctional/install/rollback/SBOM/operations controls. Decision: add the smallest pure diagnostic boundary without touching release authority.
- 2026-08-03: Added `monitoring_nonfunctional_evidence_revalidation.py` and focused tests. The synthetic complete manifest is fresh but forced non-authoritative; the current workspace diagnostic has zero records and sixteen missing controls.
- 2026-08-03: Added strict typed-field, symlink, uppercase/padded-SHA rejection checks; focused plus adjacent commercial subset passed 54 tests; compileall, Ruff and review-gate passed; release/B6/C14/runtime state unchanged.
