# Codex Review: mw_source_reference_reindex_20260722

Date: 2026-07-22
Delegated-agent output: `runs/codex_mw_source_reference_reindex_20260722.md`

## Verdict

Pass for the scoped scanner/root-cause repair. RUX remains intentionally blocked at the controlled reindex decision, not at scan integrity.

## Boundary Check

- Product code changes are limited to the scanner and the two allowed scanner test files.
- No exporter/literature/main/models/repository/frontend file was modified by this task.
- RUX and D001 source hashes remained unchanged.

## Codex Verification

- Real pre/post manifests were generated from immutable RUX and D001 bytes.
- Ruff check passed for all changed code/test files.
- 99 scanner/source-preserving/legacy/citation/literature/candidate tests passed.
- `PytestUnhandledThreadExceptionWarning` was elevated to an error and did not occur.
- D001 in-memory transform was idempotent, retained identical ZIP part names, changed only `word/document.xml`, and did not write the source file.

## Delegated-Agent Output Review

Codex executed and reviewed the route directly; Hermes was not dispatched because the workflow guard selected the high-risk Codex-direct scoped patch route. No model self-report was used as acceptance evidence; counts and issue codes came from actual manifest objects.

## Residual Risk

- RUX cannot be physically reindexed without refreshing/rebinding three EndNote citation fields because first-occurrence ordering moves source references 18 and 19 around orphan 17.
- Citation-manager behavior was verified at OOXML level, not by opening and refreshing fields in Microsoft Word/EndNote/Zotero/Mendeley desktop plugins.
- Existing FastAPI `on_event` deprecation warnings remain unrelated; no thread-exception warning occurred.
