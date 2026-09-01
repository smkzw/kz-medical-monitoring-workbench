# R4-D08 Contract Freeze Follow-up 1

Continue the same verifier session. Re-review only the two blocking defects you
reported and any directly adjacent oracle-leaf blind spot exposed by the
repair. Stay read-only.

Read these files only:

- `AGENTS.md`
- `reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_6_20260814.md`
- `reviews/medical_monitoring_r4_d08_typed_fixture_catalog_v1_20260814.json`
- `reviews/medical_monitoring_r4_d08_expected_outcome_oracle_v1_20260814.json`
- `reviews/medical_monitoring_r4_d08_challenge_manifest_registry_v1_20260814.json`
- `tools/generate_d08_challenge_registry.py`
- `tests/test_d08_artifact_generator.py`
- `runs/review/medical_monitoring_r4_d08_contract_freeze_luna_20260814.md`

## Hard boundaries

- Read-only; modify no file.
- Do not start services or port 8911.
- Do not read outside the exact list.
- Do not access runtime, product UI, real data, medical-writing or security
  surfaces.
- Return only an evidence-based verdict; do not accept because the parent says
  the defects were fixed.

Write exactly one output file:

`runs/review/medical_monitoring_r4_d08_contract_freeze_luna_followup1_20260814.md`

The runner persists it; return the complete report in the final response and
do not write it yourself.

New expected immutable hashes:

- contract `ff3d3a1bd9844ac8808ca7f9ada1466317763eb883e60d825f15bb3015ac4d64`
- catalog `d3cd694bcbe63d977d5ef332be3647fb1274293be6ec364021946ee610ffa82c`
- oracle `a40cbb509df2378804fd513a79467cbbc4e208d3b2b5c6f1a2410a63a12b8ac9`
- generator `63d610e82c385cbe906ecf8978622b9d534a64ef22b74a275832a0e07e8df100`
- tests `66f4cea7c7cbe8a71bba8833aad824d596a1a8980e7b860c2f05df5cda0ee0c1`
- registry `bf0142b36a60524d40d203e641c6fc0ef591c01069dd63caf6fc92da3ec96a9a`
  with content hash
  `55f1efbd7bfdb2ae7ea1e461b02eb732b792bba0140208ce4bfe3e6b4661ca9a`.

Confirm independently that:

1. Mutations of D08-CASE-203 `source.query_present`, `trace.node_set`,
   `l2.source_record_count`, and `all_units_disposed` are all rejected by
   `audit_case`, including before early-return branches.
2. The catalog-tamper mutation now writes the resealed catalog to the exact
   consumed temp path and fails specifically with D08 stale catalog hash.
   Unexpected exceptions can no longer be counted as a successful mutation.
3. The repair did not add oracle authoring/derivation or runtime imports.
4. Scan the directly adjacent generic oracle leaves for another mutation that
   still escapes the independent audit. If any reproducible blind spot remains,
   return `REVISE_D08_CONTRACT` with the smallest example.
5. Parent execution observed 52 focused tests, Ruff and compile passing, but
   challenge that evidence. Your read-only sandbox may prevent temp/write
   execution; distinguish sandbox limitation from artifact defect.

Final verdict must be exactly `ACCEPT_D08_CONTRACT` or
`REVISE_D08_CONTRACT`, followed by concise evidence.
