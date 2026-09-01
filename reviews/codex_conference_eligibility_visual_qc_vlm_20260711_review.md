# Codex Conference Review: eligibility_visual_qc_vlm_20260711

Date: 2026-07-11

## Verdict

Final conference verdict: pass with Codex corrections and split authorization. The immutable-QC/CAS/effective-projection backend may proceed. VLM implementation remains gated. Unsafe override and stale v8 findings are excluded.

## Boundary Compliance

- Qwen, Mimo and Reasonix DeepSeek Flash wrote only their assigned participant outputs.
- The Hermes chair ran on `aishuo/MiniMax-M3`; two HTTP 529 runs were retained and a third same-route run completed. No silent substitution occurred.
- No delegated model wrote production code or inspected clinical images.

## Participant Outputs Reviewed

All three participant outputs were reviewed. Strong convergence exists on immutable QC records, separate effective projection, project/source/extraction/model binding, fail-closed VLM and QC not equaling medical confirmation.

Codex rejects these participant suggestions:

- Any `manual_review_required` override that makes evidence decisional. Human review must create a new immutable visual-QC record reaching `sampled_pass`; it must not reinterpret the prior state as pass.
- Any VLM fallback to another model/provider. A configured profile/model mismatch or unavailable approved route remains blocked/failed.
- VLM free-text, diagnosis, lesion-severity, efficacy, protocol-deviation, eligibility or treatment output.

## Hermes Sub-Venue Review

The 273-line aishuo chair package compares all participants and adds medical-manager, QA, privacy and regulator perspectives. Codex accepts the two-table immutable-record plus CAS-state direction, server-authoritative projection, explicit immutability triggers, audit events and strict VLM descriptor boundary.

Codex corrections:

- Reject the chair's endorsement of a `manual_review_override`; the valid path is a separate human `sampled_pass` QC record.
- Chair claims that MY009 page OCR expansion, profile digest and parent-child atomicity are still missing are stale. SQLite v10 now binds profile/model/prompt/gateway digest and atomically finalized D001 1-page plus MY009 14-page children. All 30 real GLM/Paddle child tasks succeeded and remained `needs_visual_qc/not_reviewed`.
- Existing span `quality_state` must remain historical worker output. Effective status comes only from the QC record/state projection; do not retrofit a CHECK that would invalidate historical values without a migration audit.
- Authentication remains `unverified_client_claim`; QC records are not electronic signatures.

## Main-Venue DeepSeek Pro Review

The 236-line Reasonix DeepSeek Pro review accepted the core two-table QC architecture and Codex corrections. It independently rejected `manual_review_override`, span mutation, free-text VLM output and CHECK retrofits on historical span state. It required Codex to verify four current-code claims before implementation.

Codex completed those checks:

- Current v10 medical review commit verifies current-source ownership but does not check effective QC status; the P0 gate is real.
- Active v10 has `trg_eligibility_evidence_span_no_update` but no span DELETE trigger; v11 must add it.
- The atomic PDF finalizer validates parent lease, complete page coverage, project/subject/source identity and full artifact hash before inserting all children and succeeding the parent in one transaction.
- OCR profile digest binds profile, actual local model, fixed prompt and gateway contract; worker startup rejects mismatches.
- VLM jobs still fail closed with `vlm_gateway_not_configured` and create no artifact.

## Codex Independent Verification

- Focused parent-child/worker/OCR/runtime regression: 48 tests passed.
- Cross-subsystem affected regression: 49 tests passed.
- Whole workbench regression: 463 tests passed in 201.213 seconds.
- Frontend production build passed with only the existing chunk-size warning.
- Real isolated D001 and MY009 PDF runs produced 15 rendered pages, 30 OCR children and 30 unreviewed evidence spans; temporary artifacts and OCR bodies were destroyed.
- Active runtime is schema v10 with clean integrity/FK/audit reports and zero evidence jobs/artifacts/spans/review records.

## Final Decision

Authorize schema v11 and backend enforcement only:

1. Immutable visual-QC records plus CAS current-state projection.
2. Span DELETE protection.
3. Server-authoritative effective evidence projection.
4. Decisive medical actions and AI drafts may cite only current `sampled_pass` evidence.
5. `manual_review_required` has no override; human review creates a new `sampled_pass` QC record.

Do not authorize VLM implementation or real clinical-photo processing yet. VLM remains fail-closed pending a closed-vocabulary contract, output-side clinical-inference rejection, non-clinical fixtures, PHI/log tests and Codex visual acceptance.
