# Codex Conference Review: mw_protocol_p0_phase0b_readiness_challenge_20260801

Date: 2026-08-01

## Verdict

`READY_FOR_BOUNDED_SLICE / PHASE_0B_RUNTIME_GATES_OPEN`

## Boundary Compliance

- `DEVIATION`: a chair-run 18-test module imports
  `services.api.app.main as app_main`, contrary to the declared no-main and
  no-monitoring boundary. The chair report's contrary claim is rejected.
- No service, browser, Word, or medical-writing product-model runtime was
  started by this conference.
- Codex edits remained within seven connected product/test files and tracked
  records; the seventh is the aggregation frontend contract-test file.

## Participant Outputs Reviewed

- Luna: complete round 1, primary `codex/gpt-5.6-luna/max`, no fallback.
- DeepSeek: complete round 1, primary
  `deepseek/deepseek-v4-flash/max`, no fallback.

## Hermes Sub-Venue Review

- Qwen chair round 1 returned `REVISE` with three P1 findings and several P2
  findings.
- After bounded remediation, the same chair session returned slice-level
  `READY`; all P1 findings were independently closed.
- The chair left one low-practical-risk P2 create-hash gap and one P3 intent
  label; Codex closed both after the final chair pass.
- Runner-owned evidence records two same-session rounds. The report's
  “four-round” narrative is not treated as runner pass-count evidence.

## Main-Venue Codex Review

- Confirmed Pydantic cross-field failure, atomic same-resolution readiness
  preservation, and explicit post-merge revalidation.
- Confirmed document-control structural classification, blank
  project-decision anchor handling, working-copy-aware banner suppression,
  direct AI-first submit, Chinese labels, and deterministic frontend retry key.
- Added server-resolved section/template identity to backend semantic hashes
  and a conflict test; forced blank-draft intent to `章节起草`.

## Codex Independent Verification

- `182 passed` in focused protocol-template/fact-intake/frontend-contract
  tests.
- Python compileall passed.
- Frontend production build passed (existing large-chunk warning only).
- I/II/III applicable unclassified nodes 0; blocker body pollution 0.
- No browser/product-model/Word verification was attempted in this slice.

## Final Decision

Accept the typed drafting-readiness slice as offline READY. Do not claim
Protocol Phase 0B complete or runtime accepted. Next safe work is the
medical-writing-only runtime isolation gate, because document-level
unknown/deferred aggregation is now implemented and offline-tested.

The product-code verdict is separable from reviewer conduct: no P0-P2 product
defect remains in this bounded slice, while the conference receives a
boundary-compliance failure. Relative to the old r42 snapshot, concurrent
monitoring changes mean no causal logical-zero assertion is possible.
