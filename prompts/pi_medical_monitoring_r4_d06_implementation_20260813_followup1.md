Same-session bounded correction of the rejected R4-D06 implementation. Correct the existing implementation against the now-frozen v1.17 validation-artifact contract and return a complete handoff. Do not claim acceptance.

Hard boundaries:
- Work only inside the runner-provided workbench working directory.
- Writes remain limited to `poc/medical_monitoring_ai_native_r4/src/mm_r4/`, `poc/medical_monitoring_ai_native_r4/tests/`, and `poc/medical_monitoring_ai_native_r4/README.md`.
- Do not change the frozen v1.17 contract, catalog, oracle, registry, generator, context/review/prompt/run files, R1-R3 packages, any product/frontend/service surface, real-project path, medical-writing path, or security implementation/test.
- Do not start 8911 or any service, run real projects/data/providers, install packages, or perform browser/UI work.
- The runner owns `runs/pi_medical_monitoring_r4_d06_implementation_20260813_followup1.md`; never write it with tools. Return the requested handoff only.
- Preserve unrelated changes. Before editing, recompute the listed initial implementation hashes; if any differs, stop and report concurrent drift rather than overwriting it.

Output file:
Write exactly one output file: `runs/pi_medical_monitoring_r4_d06_implementation_20260813_followup1.md`

Read these changed authorities completely before editing:
- `context/medical_monitoring_r4_d06_implementation_20260813_context.md`
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md` frozen v1.17 SHA-256 `9c6a79814afbc11a69e54b7f7f421cc815c27bb645576fe48eb55ea52f1a4e6e`
- `context/medical_monitoring_r4_d06_contract_acceptance_record_20260813.md`
- `reviews/codex_conference_medical_monitoring_r4_d06_contract_acceptance_20260813_review.md`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json` SHA-256 `27dd45d4f17d4655be34711e6ad4d5a6b0c77871f0c01b8f8c53dee8ce19eb76`
- `reviews/medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json` SHA-256 `87dba011bfc484437914e3eb3040284bf195d5b6f60df9b3b26b072ea9b6f245`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json` SHA-256 `cb739ffbb0d7a8536fb528f8a7daf21b787d36fd8ce3bc0269884fb617c7d131`
- `tools/generate_d06_challenge_registry.py` SHA-256 `33bbfe3d97e0b34a805de393ba4110cfb500730caba4ee763e1e543cc6b67a55`
- `runs/codex-subagent_medical_monitoring_r4_d06_implementation_review_20260813.md` SHA-256 `26e55fd5abcc43dca16508a51ebf4abf2f6aedd77dcf61a3489a1b9a102f4136`
- Your prior implementation handoff at `runs/pi_medical_monitoring_r4_d06_implementation_20260813.md` for historical claims only; current files are authoritative.

Initial implementation hashes that must still match before editing:
- `src/mm_r4/efficacy.py` `dd87deeeb67ac89e3ba309a62620122ea6231920b56a5ca4e8462bc713481ae1`
- `src/mm_r4/efficacy_evaluator.py` `89d1fe7921005a62a46dfc59499c5559202a6e7c15ab8445ed1a9b3a21777ea2`
- `src/mm_r4/efficacy_projection.py` `90832daa40c0e87333a394026ee4cb32cfa6aef8243af2aa25a3bad9fd3ffb5b`
- `src/mm_r4/efficacy_fixtures.py` `defd2ac5139a0eec688c6b4351f6676ac987f2a135e3e658250ca3ee1067581d`
- `src/mm_r4/__init__.py` `53bf4dcc42e8abd72c437cddb1a0c963492133ed893dcfa764e406c1807bdf24`
- `README.md` `50fc76df4cfb18745dea9837cd1233eec1ca428f0a1d9701c0be955af5b5d048`
- `tests/test_efficacy_contract.py` `4c1f4701727a5efec18c48271cb0b564d6402be2a6a2be6afc73249f387026f4`
- `tests/test_efficacy_slice.py` `1f4a15958ed02a4c3b28f0400c25090dc16d434c7db5dcd516f576839f323c80`
- `tests/test_efficacy_projection.py` `3b54c5a1698aa00746672ce0c34acd3c448f987b00e6fc9d3a12988dd9cba38b`
- `tests/test_efficacy_challenge_matrix.py` `80a0c78794f2bc4adf2ad290626cf7f5f699f77ca3c0e1b38e4121ec6ec3c683`

Required correction outcomes:

1. Remove circular observed-output construction.
   - Raw evaluator/gate/schema/audience/registry entrypoint output is the object compared with the independent oracle/DSL.
   - `assemble_outcome` must not copy or replace any field from expected outcome, oracle, required manifest traces, challenge number, fixture/test IDs or annotations. Prefer deleting/bypassing that assembly layer. If a test adapter adds mechanically computed fixture/input hashes, prove those hashes depend only on the actual typed input and do not alter clinical, trace, audience, identity, disposition, count or error fields.
   - Derive `clinical_outcome_contract` from runtime L1/subtype/gate semantics and the frozen deterministic mapping, never from expected text.

2. Derive exact trace provenance from sources actually validated and consumed.
   - Close every previously observed raw mismatch: missing `accepted_artifact` in 74/78/136/191/197; extra `intercurrent_event_context` in 82; missing it in 84; extra `d08_relationship` in 102; and missing base traces in 170/171/172/189/214.
   - Case 106 remains shorthand and must not emit `accepted_artifact`. Case 191 must validate and consume the full typed `AcceptedMonitoringReportClaim`, `AcceptedIndividualTrendSource` and referenced accepted result before emitting `accepted_artifact`.
   - Trace output must remain sorted/unique and derived without case identity or manifest access.

3. Remove hard-coded clinical and lineage identities.
   - Baseline selection must resolve the supplied candidate records, bindings, policy and stable identities; mutations to candidates must change or fail the result.
   - Enrollment context, source events, rule/version, Query content and PD wording must be derived from the supplied typed enrollment decision/bindings.
   - Priority resolver/decision, D06 risk binding/public identity, subtype and hashes must derive from supplied policy, unit stable core and typed inputs; no canonical constant may hide input drift.
   - TTE event/censor interpretation, precedence binding/rule/event IDs must derive from typed input.
   - Journey projection, event/risk markers, priority, risk anchor and source jump must derive from actual typed runtime objects, not fixed fixture/page/variant constants.
   - Wrong-scope input must either fail closed with a hash of the actual rejected input or return the exact frozen error outcome; never report the canonical good-scope hash for mutated input.

4. Fail closed and preserve lifecycle ordering.
   - Do not swallow priority, projection, audience or binding exceptions and continue with a superficially successful result or static fallback.
   - Do not attach priority/clinical projection when fixture/schema/scope integrity failed or `evaluator_invoked=false`.
   - Audience payload must be built from validated runtime projection inputs only; invalid projection suppresses the payload with the correct error/gate state.

5. Make runtime inputs deeply immutable.
   - Frozen outer dataclasses containing mutable nested dict/list state are insufficient. Convert or defensively freeze/copy all nested structures that can influence evaluation, identity or provenance. Add a mutation test proving post-construction source-dict/list changes and direct nested mutation cannot change the fixture or outcome.

6. Add decisive non-circular tests.
   - For all 219 cases, execute the actual declared entrypoint and compare raw runtime output directly with the independent oracle/DSL. Assert raw trace set, audience state/payload, identity/hash fields, dispositions, counts and errors before any test annotation is attached.
   - Add negative tests showing tampered expected text/manifest trace does not change raw runtime output, and that case/test/challenge identity is inaccessible to the evaluator.
   - Add targeted mutations for case 191 accepted-report/source field removal, scope/endpoint/timepoint/hash/accepted-result drift; case 106 manifest trace injection; baseline candidates; enrollment rule/events; risk/public identity; TTE IDs; Journey source jumps; priority policy errors; wrong scope; and nested source mappings.
   - Test annotations and assertion descriptions must remain outside the clinical outcome object.

7. Keep all prior D06 contract behavior, Chinese three-part Query and renderer-neutral Journey semantics, existing D01-D05/R2/R3 behavior, root-export identity and user-language gates intact. Do not weaken the frozen contract or reseal any immutable artifact.

Verification to run with `PYTHONDONTWRITEBYTECODE=1` and pytest cache disabled:
- Focused D06 tests, including all 219 raw-runtime cases and targeted mutations.
- Full `poc/medical_monitoring_ai_native_r4/tests`.
- Frozen R2 and R3 suites using their existing local commands; do not edit them.
- Focused Ruff E/F if already available, compile/import/root-export identity and deterministic replay.
- `python3 tools/generate_d06_challenge_registry.py --check` and exact frozen SHA recheck.
- Confirm port 8911 is not listening; remove only task-created R4 caches.

Stop and report rather than using expected/manifest/case identity or weakening/resealing the frozen contract. No passing count is acceptance evidence unless the raw-runtime provenance assertions pass.

Final handoff schema:
1. `# Implementation Handoff: medical_monitoring_r4_d06_implementation_20260813`
2. `## Boundary Check`
3. `## Sources Read And Initial Hash Check`
4. `## Files Changed`
5. `## Corrections By Rejected Finding`
6. `## Raw Runtime Verification Evidence`
7. `## Full And Adjacent Regression Evidence`
8. `## Failed Paths And Remaining Gaps`
9. `## Exact Final Snapshot Hashes`
10. `## Next Action For Codex`
