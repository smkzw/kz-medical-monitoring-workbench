# Task Context: medical_monitoring_mgk10_source_revalidation_20260802

Created: 2026-08-02 21:20:48
Objective: Revalidate current MG-K10-SAR listing candidates and determine whether a second provenance-complete full snapshot exists without promoting variants
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

The current P10 readiness report blocks MG-K10 on `batch_coverage_insufficient`. The source folder contains several same-structure workbook candidates, so a read-only provenance/classification recheck is needed before retaining or changing that gate.

## Source Of Truth

- Current MG-K10-SAR DM source folder and the duplicated Patient Profile copy, read-only.
- `services/api/app/listing_file_parser.py` (`listing_file_parser_v3_ooxml_metadata_recovery`).
- `services/api/app/monitoring_source_classifier.py` (`monitoring_source_classifier.v2`).
- Existing P10 source-classification, readiness and release-gate records.

## Scope

- In scope: filename/size/SHA/core OOXML metadata, sheet/row counts, parser warnings, source classification and structural/value fingerprint comparison for the three current workbook candidates.
- Out of scope: source registration, batch creation, database/runtime writes, provider/API/service/browser/real-project execution, medical interpretation or promotion of a candidate.

## Success Criteria

- Determine whether a second provenance-complete full snapshot is present.
- Keep raw candidates, format-defect variants and generated copies distinct.
- Do not promote a file solely because it has the same sheet/row counts.
- Produce a hash-bound evidence record and leave the readiness gate unchanged unless the evidence is sufficient.

## Risk Boundaries

- Read source workbooks only; write only workbench evidence/context/review/metrics/ledger surfaces.
- Do not infer snapshot date, full-batch identity, source lineage, or medical validity from file mtime, OOXML core metadata, same row count, or generated filenames.
- No Hermes dispatch or external provider is used; Codex is final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 21:20:48: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Locked listing parsed as 62 sheets/148,788 rows and remains the only provenance-complete locked candidate. EDC variant has format-defect warnings; `work_files/__listing__.xlsx` and the Patient Profile copy share one SHA and are not a second batch.
