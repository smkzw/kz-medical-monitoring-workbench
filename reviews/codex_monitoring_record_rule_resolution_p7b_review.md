# Codex Review: monitoring_record_rule_resolution_p7b

Date: 2026-07-29
Execution mode: Codex direct; no delegated-agent output was used.
Hermes: not invoked because the workflow guard selected direct execution.

## Verdict

Pass for the P7B backend slice. This is not a release verdict for the full
medical-monitoring subsystem.

The initial pass was reopened after Codex found that record anchors still relied
on hard-coded field names and generic date suffixes. The final pass applies only
to the mapping-driven implementation described below.

## Boundary Check

- Product changes are limited to the allowed medical-monitoring batch/mapping,
  daily-run, and record-resolution backend files and their corresponding tests.
- No medical-writing, shared AI configuration, frontend, or `main.py` file was
  modified by P7B.
- Pre-change source backups and final SHA-256 values are recorded in the P7B
  handoff.
- Concurrent edits were observed in monitoring AI field-mapping files and their
  tests; P7B did not modify, revert, or merge those edits.

## Codex Verification

- Read global and workspace `AGENTS.md`, the P7B contract, P7A repository/runtime,
  daily-run persistence/service, rule runner, and adjacent tests.
- Python compilation passed for all P7B backend files.
- Delegated implementation evidence: focused `75 passed`, adjacent mapping and
  lifecycle `125 passed`, P7 backend `320 passed`, and all monitoring tests
  `601 passed`.
- Codex independent targeted combination after handoff: `132 passed`.
- Codex added one identity-completeness regression and reran the focused
  combination: `76 passed`.
- No browser check was required because frontend changes were prohibited.
- No production database was migrated; additive migration was verified on a
  temporary SQLite database with pre-column rows and snapshots.

## Contract Review

- Each resolved record is bound to exact assignment and protocol version identity.
- Centre, subject, and event-date anchors are driven by the exact frozen confirmed
  mapping revision. Generic date-suffix inference is prohibited.
- Mapping revision, repository hash, formal mapping content hash, source batch,
  and source profile identity are frozen in the resolution hash and rule snapshot.
- Administrative modification dates such as `PAGELMDT` and birth dates are
  explicitly excluded from event-date resolution.
- Exact protocol-version pack lookup fails on zero or multiple complete published
  packs.
- Multi-pack snapshots retain actual per-record pack identities and never invent
  a composite ID.
- Resolution identity is hash-validated at persistence time.
- Existing project-effective runs remain the default for old records and pure
  project-effective projects.
- A post-snapshot crash resumes from the frozen snapshot instead of re-resolving
  mutable assignment state.

## Residual Risk

- Subject-less records resolve centre-level applicability but cannot enter the
  current subject-grouped deterministic rule runner; they close with a diagnostic.
- Non-ISO source dates must be normalized upstream.
- Repair/supersede UX for a pre-AI `analysis_partial` run remains a later P7 flow.
- `ruff` and `mypy` are not installed; pytest and `py_compile` are the available
  verification evidence.
