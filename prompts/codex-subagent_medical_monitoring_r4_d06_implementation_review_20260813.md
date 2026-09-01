Fresh-context independent implementation review. Decide ACCEPT or REJECT for the exact R4-D06 synthetic/offline implementation snapshot.

Hard boundaries:
- Read-only inside the current workbench. Do not edit files, start services, access real projects/data/providers, medical-writing paths, product/R5 UI, statistical-analysis work or security paths.
- Do not write the runner-owned report with tools. Return the complete handoff for the runner/parent to persist.
- Green tests are evidence only if the actual runtime result—not expected/manifest metadata injected after execution—satisfies the oracle.

Output file:
Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d06_implementation_review_20260813.md`

Read these files only:
- `context/medical_monitoring_r4_d06_implementation_review_20260813_context.md`
- `context/medical_monitoring_r4_d06_implementation_20260813_context.md` SHA-256 `6097e54085a595fad92405db3148ad12b571e25c4556cd03b9a33c836114aaea`
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md` SHA-256 `721bdcc5ec0b24a462a3e9447ee5c6fcfa3e65885bd9430701b30281900b0d74`
- `context/medical_monitoring_r4_d06_contract_acceptance_record_20260813.md` SHA-256 `917b3c3bfd2381d3380f40978e9bbb9b827e9a462bc77913d7ef19176845855e`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json` SHA-256 `e12584660af3d0605e80a3aa9336f8a12372d0ff17e68f477871b1a396c7c832`
- `reviews/medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json` SHA-256 `64ff4976b586c6c26dd5c663178e1e8a643d78ac3f66bf200eecfa5df4abe77f`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json` SHA-256 `561f01a3cc14170165fd904b73f9aef57e0fb687319331851303ebd0ee6f4f98`
- `tools/generate_d06_challenge_registry.py` SHA-256 `9e5d285919302d7d94f11ac0b404dad01cb255ee31ff41a850905c93355e3ab4`
- `runs/pi_medical_monitoring_r4_d06_implementation_20260813.md` SHA-256 `fe73725651d673b98d8596c1db05418c0561e45847bbb4c5746b66ac9c9f7f8a`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/efficacy.py` SHA-256 `dd87deeeb67ac89e3ba309a62620122ea6231920b56a5ca4e8462bc713481ae1`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/efficacy_evaluator.py` SHA-256 `89d1fe7921005a62a46dfc59499c5559202a6e7c15ab8445ed1a9b3a21777ea2`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/efficacy_projection.py` SHA-256 `90832daa40c0e87333a394026ee4cb32cfa6aef8243af2aa25a3bad9fd3ffb5b`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/efficacy_fixtures.py` SHA-256 `defd2ac5139a0eec688c6b4351f6676ac987f2a135e3e658250ca3ee1067581d`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/__init__.py` SHA-256 `53bf4dcc42e8abd72c437cddb1a0c963492133ed893dcfa764e406c1807bdf24`
- `poc/medical_monitoring_ai_native_r4/README.md` SHA-256 `50fc76df4cfb18745dea9837cd1233eec1ca428f0a1d9701c0be955af5b5d048`
- `poc/medical_monitoring_ai_native_r4/tests/test_efficacy_contract.py` SHA-256 `4c1f4701727a5efec18c48271cb0b564d6402be2a6a2be6afc73249f387026f4`
- `poc/medical_monitoring_ai_native_r4/tests/test_efficacy_slice.py` SHA-256 `1f4a15958ed02a4c3b28f0400c25090dc16d434c7db5dcd516f576839f323c80`
- `poc/medical_monitoring_ai_native_r4/tests/test_efficacy_projection.py` SHA-256 `3b54c5a1698aa00746672ce0c34acd3c448f987b00e6fc9d3a12988dd9cba38b`
- `poc/medical_monitoring_ai_native_r4/tests/test_efficacy_challenge_matrix.py` SHA-256 `80a0c78794f2bc4adf2ad290626cf7f5f699f77ca3c0e1b38e4121ec6ec3c683`

Required review:
1. Recompute all hashes, run the four focused D06 test files with `PYTHONDONTWRITEBYTECODE=1` and pytest cache disabled, and run the generator `--check`. Do not treat counts alone as acceptance.
2. Trace every field of the assembled 219-case outcome to one of: runtime-derived result, deterministic input/content identity, or test-only annotation. Any medical disposition/subtype/count/state/trace/audience/identity/hash supplied from expected outcome or manifest rather than runtime is blocking.
3. Inspect `assemble_outcome`, the fixture adapter/matrix, the evaluator's `D06Fixture`, `_compute_trace_edges`, and the 219-row test. Prove whether the DSL/oracle comparison is circular.
4. Independently group catalog fixtures after removing `challenge_number`. For each duplicate semantic fixture, compare expected outcomes. In particular, cases 106 and 191 have otherwise identical inputs but different required trace edges; runtime currently returns the base three edges for both while assembled case 191 replaces them with manifest's `accepted_artifact`. Decide whether this violates the frozen contract and implementation task.
5. Check that `clinical_outcome_contract`, `challenge_assertion_code`, fixture/scope hashes and trace edges are classified correctly. Test annotation may be attached only if it is not represented as a runtime medical result; expected clinical text must not be proof of itself.
6. Search for any additional concrete case-identity branch, expected/oracle import into runtime paths, mutable or untyped objects, self-reported validation, swallowed error, hard-coded synthetic decision, ownership leak, invalid Chinese Query/Patient Journey payload, false source jump, untested public export, or tautological assertion path.
7. If practical, construct small in-memory mutations to demonstrate escapes without modifying files. Record exact commands/results.

Verdict:
- `VERDICT: REJECT` if any P0-P4 blocking issue remains. A frozen catalog contradiction is a blocker and should trigger contract/catalog corrective work rather than manifest injection.
- `VERDICT: ACCEPT` only if runtime-derived evidence independently satisfies the frozen contract with no P0-P4.
- Scope is this exact synthetic/offline snapshot only; never accept R4 overall, R5 UI, real projects, statistical analysis, product, medical writing, security or production.

Output schema:
1. `# Codex SubAgent Task: medical_monitoring_r4_d06_implementation_review_20260813`
2. `## Boundary Check`
3. `## Work Performed`
4. `## Evidence And Observations`
5. `## Verification And Gaps`
6. `## Findings (P0-P4)`
7. `## Verdict`
8. `## Next Action For Parent Codex`
