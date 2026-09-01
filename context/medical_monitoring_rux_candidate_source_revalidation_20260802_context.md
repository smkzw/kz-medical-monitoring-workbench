# Task Context: medical_monitoring_rux_candidate_source_revalidation_20260802

Created: 2026-08-02 10:29:13
Objective: Revalidate current RUX and MY009 listing candidates and record source-eligibility evidence without onboarding, diff activation, or runtime writes
Task type: `multimodal_document_precheck`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current local RUX/MY009 workbook bytes, classified only through the existing
  `services/api/app/listing_file_parser.py` and
  `services/api/app/monitoring_source_classifier.py` contracts.
- Prior source-qualification records used for comparison, not as authority:
  `records/active_slices/medical_monitoring_goal_p2_20260729/REAL_BATCH_SOURCE_AUDIT.md`
  and
  `context/monitoring_p10_rux_incremental_source_validation_20260730.md`.
- Release requirement: a processed/restored/comparison workbook must not be
  promoted to an original full-snapshot baseline without parent/provenance and
  conservation evidence.

## Scope

- In scope: read-only classification of the current RUX historical candidates,
  RUX 2025-06-12 raw/processed pair, and MY009 2026-04/2026-03 candidates;
  record size/SHA/sheet/row counts, parser warnings, and source class.
- Out of scope: source registry writes, baseline confirmation, batch creation,
  diff activation, aggregate/CAS, API/SQLite/runtime writes, provider calls,
  browser/service startup, real-project execution, and medical-writing files.

## Success Criteria

- Every existing candidate in the bounded list has a deterministic classification
  or an explicit missing-file result.
- The result distinguishes raw candidate, processed, restored, mixed, and
  comparison sources and preserves exact hashes for re-identification.
- No classification is presented as B6 approval, P2 exit, or commercial readiness.

## Risk Boundaries

- Original project files are read-only; only task evidence surfaces under the
  workbench may be written.
- Do not synthesize reviewer outcomes or infer source provenance from filenames.
- Keep 8911 and 5174 stopped; do not touch 18911/PID 43191 or the parallel
  medical-writing lane.
- No delegated agent/provider/conference was dispatched; Codex performs and
  accepts the bounded read-only work directly.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 10:29:13: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Parsed and classified 12 existing RUX/MY009 candidates in memory;
  recorded only metadata, hashes, counts, classifications, and warnings.
- 2026-08-02: No candidate met the raw, provenance-complete baseline gate. The
  result remains a source-eligibility checkpoint, not a P2 exit or activation.
