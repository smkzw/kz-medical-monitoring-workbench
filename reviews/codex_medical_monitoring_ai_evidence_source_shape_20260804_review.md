# Codex Review: medical_monitoring_ai_evidence_source_shape_20260804

Date: 2026-08-04
Reviewer: Codex (direct; no delegated agent)

## Verdict

**Pass for the declared source-only slice; P4/release authority remains blocked.**

## Boundary Check

- No delegated agent or external provider was used.
- Product change stayed inside `_source_from_payload` in the named revalidator;
  tests stayed inside its named contract file.
- Evidence was written under the named `records/active_slices/...` directory;
  context/review/metrics are workflow records only.
- The current coverage JSON and all runtime/medical-writing surfaces were
  untouched.

## Codex Verification

- Non-string `id`, `path`, `sha256`, and `role` values are rejected.
- String and boolean `bytes` values are rejected; actual non-negative integers
  retain existing byte/hash validation.
- Focused suite: 14 passed.
- Adjacent P4/release/source-token revalidation suites: 46 passed.
- Python compile: exit 0.
- Hermes `review-gate --require-verification`: run after this review and
  metrics record is complete.
- Live runtime/browser/provider/real-project verification was intentionally not
  run because B6/C14 and approved-input/host-attestation gates are closed.

## Delegated-Agent Output Review

Not applicable: direct Codex implementation. Evidence is traceable to the
pre/post hashes and command results in
`records/active_slices/medical_monitoring_ai_evidence_source_shape_20260804/TEST_EVIDENCE.md`.

## Residual Risk

This does not validate the truth of source bytes or hashes, the P4 model/
prompt evidence itself, independent AI behavior, or commercial release. It
only prevents malformed declaration shapes from being treated as valid input;
the current P4 and release diagnostics remain blocked and read-only.
