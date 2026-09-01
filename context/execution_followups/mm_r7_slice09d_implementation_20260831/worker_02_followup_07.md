Delegated mode. Continue the same bounded execution session for task `mm_r7_slice09d_implementation_20260831`, role `worker_02`.

## Hard boundaries

- Modify only `artifacts/mm_r7_slice09d_implementation_20260831/consolidated_total_manifest.py` and, only if necessary, `artifacts/mm_r7_slice09d_implementation_20260831/test_fault_recovery.py`.
- Do not modify product source, measurement runner/schema/tests, accepted seams, any v1–v4 measurement evidence file, source-copy identities, real projects/data, medical writing, services, models, browsers, or security surfaces.
- Do not run measurements. The runner persists the report; do not write it with tools.

Read these files only:

- `artifacts/mm_r7_slice09d_implementation_20260831/consolidated_total_manifest.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/consolidated_total_manifest_v0_2.json`
- `artifacts/mm_r7_slice09d_implementation_20260831/test_fault_recovery.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831_v4/capacity_statement.md`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831_v4/determinism_v0_2.json`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831_v4/environment_manifest.json`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831_v4/measurement_manifest.json`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831_v4/raw_measurements.jsonl`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831_v4/stat_summary.json`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831_v4/source_copy_identity_measurement_v4.json`
- `runs/conference/mm_r7_slice09d_implementation_acceptance_20260831/general_single_object_round7_reporting_fix.md`

Close only the remaining P4 total-manifest gap:

1. Add a `measurement_full_v4` section pinning exactly the seven listed v4 top-level evidence files.
2. Retain the existing bounded-final evidence, but name/describe its section as historical bounded adapter/self-test evidence rather than the decisive final capacity checkpoint. Prefer the smallest compatible section-key change.
3. Keep the manifest compact: do not enumerate v4 fixtures/workspaces because the v4 `measurement_manifest.json` already pins all 6675 files.
4. Add or adjust one focused assertion proving the v4 section is present, includes the archived measurement-time identity, and keeps the bounded section distinct.
5. Regenerate `consolidated_total_manifest_v0_2.json` with the existing deterministic builder and run the focused consolidated-manifest test. Do not run measurements or modify v4.

Return changed files, section/file counts, manifest inventory SHA, focused test count and remaining uncertainty. Do not claim R7/R8 acceptance.

Write exactly one output file:

`runs/execution/mm_r7_slice09d_implementation_20260831/worker_02_followup_07.md`

The runner persists it.
