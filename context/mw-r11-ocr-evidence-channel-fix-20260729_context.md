# Task Context: mw-r11-ocr-evidence-channel-fix-20260729

Created: 2026-07-29 02:59:35
Objective: Fix r11 OCR evidence channel selection for anomaly pages while preserving native text reconciliation, OCR recovery behavior, 200 DPI, GLM-OCR default, immutable PNGs, concurrency, and audit fields; add focused regressions and verify with pytest and py_compile.
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `context/mw_r11_document_preparation_failures_20260729.md`
- `services/api/app/writing_reference.py` OCR recovery/reconciliation path
- `services/api/app/writing_reference_ocr_evidence.py`
- `tests/test_writing_reference_ocr_evidence.py`
- Frozen user evidence: three public Protocol/SAP extraction failures with
  `reconciled OCR evidence must retain the native text channel`.

## Scope

- In scope: anomaly-page OCR channel/status selection and focused regression
  coverage.
- Out of scope: frontend, AI role settings, medical research pipelines, r11
  runtime evidence/databases, matrices, generated deliverables, and OCR
  rendering/model/concurrency/audit-field contracts.

## Success Criteria

- `ocr_reconciled` and span status `ocr_reconciled` require both native spans
  and non-empty OCR text.
- Anomaly pages without native spans use ordinary `ocr`/`ocr_recovered` while
  retaining the anomaly `selection_reason`.
- Anomaly pages with native spans and empty OCR retain native spans and emit
  empty OCR evidence without reconciliation.
- Existing 200 DPI, GLM-OCR-bf16, immutable PNG, eight-way concurrency, and
  audit lineage behavior remain covered.
- Focused pytest and `py_compile` pass.

## Risk Boundaries

- Modify only `services/api/app/writing_reference.py` and
  `tests/test_writing_reference_ocr_evidence.py` for the product change.
- Do not mutate frozen r11 runtime evidence or databases.
- A bounded subAgent may implement within the two-file write scope; Codex owns
  verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 02:59:35: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29: Inspected the validator and recovery path. Root cause confirmed:
  anomaly plus non-empty OCR selected reconciliation before checking native
  spans.
- 2026-07-29: Changed reconciliation eligibility to require native spans and
  non-empty OCR; added native+OCR and no-native+OCR regressions; strengthened
  native+empty assertions.
- 2026-07-29: Focused suite passed 9 tests; related extraction/contract suite
  passed 38 tests; targeted `py_compile` passed.
- 2026-07-29 03:14: Codex independently reran the exact 38-test suite and
  `py_compile`; both passed. Three failures observed only in an expanded
  oMLX-role suite assert the previous gate-owned-model contract and belong to
  the concurrent four-role configuration migration, not this evidence-channel
  change.
