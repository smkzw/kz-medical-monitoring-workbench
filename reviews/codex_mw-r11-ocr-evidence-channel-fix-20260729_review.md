# Codex Review: mw-r11-ocr-evidence-channel-fix-20260729

Date: 2026-07-29
Delegated-agent: subAgent Gibbs
(`019faa17-f9df-7433-9116-2937006b8573`); Codex independently accepted the
bounded patch.
Workflow boundary: Codex x Hermes tracked-task records and acceptance gate.

## Verdict

Pass

## Boundary Check

- The delegated write scope and the accepted product delta are limited to the
  OCR recovery implementation and its focused test file. Workflow task records
  were written only under `context/`, `runs/`, `reviews/`, and `metrics/`.
- No frontend, AI role settings, medical research pipeline, r11 runtime
  evidence/database, matrix, or generated deliverable was changed.

## Codex Verification

- `python3 -m pytest tests/test_writing_reference_ocr_evidence.py -q`: 9 passed.
- `python3 -m pytest tests/test_writing_reference_ocr_evidence.py tests/test_writing_reference_extraction.py tests/test_mw_round5_backend_contract.py tests/test_writing_reference_upper_layer_contracts.py -q`: 38 passed.
- `python3 -m py_compile services/api/app/writing_reference.py services/api/app/writing_reference_ocr_evidence.py tests/test_writing_reference_ocr_evidence.py`: passed.
- Source inspection confirmed `WRITING_REFERENCE_OCR_MIN_DPI=200`,
  `WRITING_REFERENCE_OCR_MODEL="GLM-OCR-bf16"`, and
  `WRITING_REFERENCE_OCR_MAX_CONCURRENCY=8` remain unchanged.

## Delegated-Agent Output Review

Gibbs correctly isolated the contradiction between an image-only anomaly page
and the reconciled-channel validator. Codex reviewed the exact source delta
against the frozen failure analysis, validator contract, related extraction
tests, and upper-layer lineage tests rather than accepting the agent's report
by confidence.

## Residual Risk

The no-native anomaly regression uses a controlled parser result to isolate the
channel contract; it does not claim that every real PDF parser anomaly will be
classified identically. A fresh isolated r11 E2E round remains outside this
local source/test task and must be run separately before any release claim.

An expanded oMLX-role suite currently contains three stale assertions that the
shared workload gate must select/override the OCR model. A concurrent,
separately scoped four-role AI configuration change intentionally changes that
contract so the gate owns only lease/concurrency. Those failures are not
attributed to this OCR evidence patch and must be adjudicated with that slice.
