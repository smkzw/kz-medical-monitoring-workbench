Delegated mode. Continue the same bounded execution session for task `mm_r7_slice09d_implementation_20260831`, role `worker_02`.

## Hard boundaries

- Modify only `artifacts/mm_r7_slice09d_implementation_20260831/measurement_runner.py` and `artifacts/mm_r7_slice09d_implementation_20260831/test_measurement_runner.py`.
- Do not modify product source, accepted 09A–09C seams, real projects/data, medical writing, services, models, browsers, security surfaces, or any existing measurement evidence directory.
- Do not rerun the 30-cell/full-contract matrix and do not rewrite `_v4` reporting files; Codex owns report-only regeneration and final acceptance.
- Do not regenerate `source_copy_identity_v0_1.json` or `consolidated_total_manifest_v0_2.json`; Codex will do that after reviewing the patch.
- Preserve invalidated v1/v2, interrupted v3 and completed v4 byte-for-byte.
- Return the full handoff; do not write the runner-owned report through tools.

Read these files only:

- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_runner.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/test_measurement_runner.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_schema.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831_v4/capacity_statement.md`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831_v4/stat_summary.json`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831_v4/measurement_manifest.json`
- `runs/conference/mm_r7_slice09d_implementation_acceptance_20260831/general_single_object_round6_full30_v4.md`

The independent reviewer accepted the v4 raw evidence for §3/§4 but found two conservative P3 reporting defects:

1. Full non-bounded accepted-seam runs are labeled `product_capacity_status=adapter_readiness_bounded_only` because the current expression checks only the backend.
2. `_capacity_statement()` always appends `(bounded proof only; not accepted)` for the accepted backend, even when `bounded=false`.

Implement the smallest reporting-only source correction:

1. Centralize the accepted-backend status decision so both summary and measurement manifest use exactly the same value:
   - accepted backend + `bounded=true`: `adapter_readiness_bounded_only`;
   - accepted backend + `bounded=false`: `contract_observation_complete_no_capacity_claim`;
   - synthetic backend: keep `not_evaluated_synthetic_fixture_io`.
2. Keep `accepted_09a_09c_product_capacity=false` in all cases. This is a scope guard, not a pass/fail flag.
3. Make `_capacity_statement()` bounded-aware:
   - bounded accepted run retains the existing bounded-only wording;
   - full accepted run states that accepted 09A–09C seams were observed in the recorded environment and explicitly says this is not a general capacity/support claim.
4. Add focused unit tests covering the exact bounded/full accepted status strings, synthetic status preservation, and absence of `bounded proof only` in the full accepted statement. Do not weaken any existing test.
5. Run only focused runner tests. Do not run full measurements or rewrite evidence artifacts.

Use stdlib-only/YAGNI changes. Return exact changed lines/files, focused test count, and residual risks. Do not claim 09D accepted.

Write exactly one output file:

`runs/execution/mm_r7_slice09d_implementation_20260831/worker_02_followup_06.md`

The runner persists it.
