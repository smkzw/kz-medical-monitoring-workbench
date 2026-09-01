# Task Context: medical_monitoring_structure_shape_matrix_20260804

Created: 2026-08-04 (Asia/Shanghai)
Objective: Validate a recorded five-project aggregate structure matrix without
reopening source files or granting mapping/runtime authority.
Task type: `code_scoped_patch_plan`
Risk: `medium`
Route: direct Codex; no delegation/conference

## Source of truth

- Existing read-only aggregate intake record:
  `records/active_slices/medical_monitoring_five_project_structure_intake_20260804/TASK_RECORD.md`.
- Current public source manifests and B6/C14/real-loop gates remain
  authoritative for identity and activation.

## Scope and assumptions

- The new JSON is a recorded evidence matrix, not a new parse and not a source
  admission artifact.
- It contains only project-scoped aggregate counts, observed neutral domains,
  unclassified-sheet counts, source revision hashes/bytes and relative evidence
  locators. It intentionally omits cells, subjects, fields and absolute paths.
- Candidate IDs `proj_my008_3_01_candidate` and
  `proj_my008_3_02_candidate` remain separate from canonical MY008 IDs.

## Acceptance

- Exact five-project set is present and unique.
- Canonical real versus candidate-only classes align with the recorded
  implementation status.
- Every source revision is basename-only and lowercase SHA-256-shaped.
- Unknown domains, narrowed project set, unsafe references, status drift and
  unsafe retention/AI flags fail closed.
- Clean output remains aggregate-only, diagnostic-only, and cannot permit
  structure mapping, adapter activation, provider, runtime, write or medical
  confirmation.

## Completed evidence

- `services/api/app/monitoring_structure_shape_matrix.py`
- `tests/test_monitoring_structure_shape_matrix.py`
- `records/active_slices/medical_monitoring_structure_shape_matrix_20260804/`
- `reviews/codex_medical_monitoring_structure_shape_matrix_20260804_review.md`
- `metrics/medical_monitoring_structure_shape_matrix_20260804_metrics.md`
- Focused suite: **9 passed**; compile and Ruff passed.

## Residual risk and next action

This matrix does not prove source bytes/currentness, full snapshots, field
mapping, adapter capability, independent-AI behavior, scientific correctness,
browser/UI acceptance or commercial readiness. Recheck B6/C14, source-token/CAS,
approved-input, host-attestation and real-loop gates before any controlled run;
keep 8911/5174/8910/4173 stopped.
