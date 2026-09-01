You are continuing the SAME Pi execution session for `medical_monitoring_r4_aemh_slice_20260810`, role `worker_02`, requested effort `high`. Codex has completed an independent source review and REJECTS the current worker_02 snapshot pending the corrections below. This is a same-session remediation pass, not a new scope.

Runner-managed report path: `runs/execution/medical_monitoring_r4_aemh_slice_20260810/worker_02_round2.md`.
Never write or edit that report path through tools. Return the complete seven-heading execution report in your final response; the runner persists it.

## Hard boundaries

- Modify only worker_02-owned R4 files: `src/mm_r4/aemh.py`, `src/mm_r4/projection.py`, `tests/test_aemh_slice.py`.
- Use the current worker_01 common contract as-is. Do not edit R1-R3, worker_01 files, product/runtime, medical writing, or real projects.
- No lifecycle establish/close/transition. No service start, network/provider calls beyond this already-running session, dependency installation, or security work. Port 8911 stays stopped.
- Runtime modules must not mutate `sys.path`.

## Codex review findings that must be repaired

1. **Required-role contract is not enforced.** `has_subject = ... or subject_ref` makes subject identity always pass; any event date substitutes for `temporal_anchor`; `site_identity` is not checked. `reported_ae`/`reported_mh` availability cannot be represented when a mapped source has zero rows. Add an explicit immutable role-availability/coverage surface on `SemanticRecordSet` (or an equivalent robust design) so an empty-but-covered semantic role differs from a missing role. All five frozen required roles must be available for an evaluable D01 unit. Missing any one yields L1 `not_evaluable` with a specific reason. Validate recognized semantic roles and reject mixed subject/site records. Allow an empty record collection so a missing subject in slice evaluation returns a fail-closed result instead of crashing.

2. **Protocol boundary is decorative.** `reporting_start_anchor` and `reporting_end_anchor` are never resolved to actual subject anchor values and never constrain events. Make the boundary operational: the record set/input must resolve both named descriptors to actual raw anchor dates; normalize them through R3. Exact inside/outside comparisons must affect applicability; partial dates crossing a boundary yield `boundary`; missing/invalid/incomparable anchors yield `not_evaluable`; no silent first/last-day imputation. A versioned explicit `applicable=False` plus a non-empty reason may also define a genuinely out-of-scope unit. Add tests for inside, exact outside, partial crossing, missing anchor, and explicit non-applicability.

3. **The fifth disposition is falsely claimed.** The current `test_not_applicable_protocol_exclusion` actually asserts `negative`. Replace it with a true `not_applicable` assertion under the versioned protocol applicability/boundary contract. Keep protocol-excluded individual concepts as explained context/counterevidence unless the whole unit is genuinely out of scope.

4. **R2 candidates are discarded and IDs diverge.** The current code creates a custom `RiskCandidateRef.candidate_id`, later constructs a distinct R2 `RiskCandidate` ID, then drops all R2 candidates from `AEMHUnitResult`/slice aggregation. Construct the real R2 candidate once, use its exact `candidate_id` in `RiskCandidateRef`, expose immutable `r2_candidates` on each unit result, and aggregate them without loss in `AEMHSliceResult`. Tests must prove one-to-one ID equality and that all candidates from multiple units survive. No candidate may be established here.

5. **Common-contract joins are not exercised.** Add a bounded conversion/validation surface (for example `AEMHUnitResult.to_unit_evaluation(...)`) that builds worker_01 `UnitEvaluation` from the result using caller-supplied L0/provenance. Test positive and boundary Query joins against the real common contract, including exact source locator and candidate IDs.

6. **NCS and alternative diagnosis are not implemented.** The present NCS test succeeds only because a lab clue matches an existing AE; the free-text `note="NCS"` is ignored, and no confirmed alternative-diagnosis path exists. Add explicit normalized fields/semantics. NCS is only combination counterevidence when there is no associated symptom, medical action/treatment, serious clue, or repeat worsening; NCS alone must not become an absolute exclusion. A confirmed alternative diagnosis may be counterevidence but must remain source-linked. Add tests for isolated NCS negative, NCS plus symptom/action remaining a clue, and confirmed alternative diagnosis.

7. **AI assertion can still masquerade as a reported source.** An `ai_assertion=True` record with role `reported_ae`/`reported_mh` currently enters `source_record_refs`. Ensure any AI assertion remains evidence/candidate and never an accepted reported source fact. Add a direct adversarial test for an AI-asserted `reported_ae` role.

8. **Risk markers are over-broad.** `_is_risk_marker` currently marks every event in a positive/boundary unit. Risk markers must attach only to the actual candidate locator, a boundary-supporting locator, or a high-priority/SAE/AESI/death locator. Add a test with an unrelated recorded AE plus an unmatched symptom: only the symptom (and any independently serious event) is marked as risk.

9. **Query and Chinese labels need correction.** Query `basis` must be audience-readable and identify the versioned protocol boundary and match strategy, not only a raw rule-lineage token. Query `source_locator_ids` must be the smallest relevant locator set, not every record in the unit. Change negative audience text from the semantically inverted “当前 AE/MH 中未发现对应记录” to a clear non-risk conclusion such as “当前证据范围内未发现需核实的 AE/MH 问题”. Keep the positive finding “当前 AE/MH 中未发现对应记录” in the Query where it belongs. Add exact tests.

10. **Nested strategy versions must be real.** Validate that `ConceptEquivalence` and `TemporalTolerance` carry non-empty versions compatible with the containing versioned `EventMatchStrategy`; validate booleans/types and protocol exclusion members. No default concept aliases or default day window.

Run the full isolated R4 test suite, focused R2 risk tests, focused R3 normalization tests, Ruff on worker_02 files, compile/import checks, frozen R2/R3 digests, and port 8911 check. Do not claim worker_02 accepted unless every finding above is covered by executable tests. In the report, enumerate old-vs-new test counts and explicitly state the candidate-ID equality, true `not_applicable`, operational boundary, exact risk-marker behavior, and remaining uncertainty. Codex remains final authority.
