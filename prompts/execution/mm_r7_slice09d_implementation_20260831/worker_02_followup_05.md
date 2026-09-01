Delegated mode. Continue the same bounded execution session for task `mm_r7_slice09d_implementation_20260831`, role `worker_02`.

## Hard boundaries

Stay inside `artifacts/mm_r7_slice09d_implementation_20260831/`; do not modify product source, real projects, services, browser/model paths, medical writing, or runner-managed reports. Preserve both completed full-run directories and their invalidation notes. Do not run the 30-cell/full-contract matrix. The runner owns the report file below; do not write it through tools.

Read these files only:

- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_runner.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/synthetic_corpus.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_schema.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/test_measurement_runner.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/source_copy_identity.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/source_copy_identity_v0_1.json`
- `artifacts/mm_r7_slice09d_implementation_20260831/consolidated_total_manifest.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/generate_fault_recovery_artifacts.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/README.md`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831_v2/raw_measurements.jsonl`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831_v2/stat_summary.json`
- `runs/execution/mm_r7_slice09d_implementation_20260831/worker_02_followup_04.md`

The corrected full run exposed a second measurement-runner defect. Codex independently observed:

- Screening and confirmation trial 0–9 are green.
- Confirmation trial 10 is the first trial using `seed + 1`; at exactly that boundary `first_backup.correctness.identity=false`, while digest/closure/atomicity/no-overwrite/terminal-state remain true.
- `_prepare_fixtures()` creates one fixture per profile using the initial seed, while `_run_child_trial()` passes each confirmation `trial_seed` into `_child_main()`, which recomputes `_fixture_info()`/oracle using that new seed against the old fixture bytes.
- The remaining workloads are truthfully marked `dependency_not_measured` after the first red.

Implement only the narrow seed/fixture correction:

1. Every executed trial must use a fixture generated from the same seed passed to `_child_main()`. Keep fixtures deterministic and inspectable. Reuse an already generated `(profile_id, seed)` fixture; do not regenerate per repeat and do not weaken identity checks.
2. Keep initial screening behavior and frozen 3-seed x 10-repeat confirmation allocation unchanged. Do not alter product accepted seams or capacity thresholds.
3. Add focused regression tests proving:
   - distinct confirmation seeds resolve to distinct deterministic fixture paths and matching oracle digests;
   - repeats within one seed reuse the same fixture;
   - an accepted-seam confirmation smoke crossing trial 9→10 remains green and both seeds have `identity=true`.
4. Run focused tests and the artifact suite. Regenerate source-copy identity and consolidated manifest after pinned changes. Run only the smallest multi-seed bounded smoke that crosses the seed boundary; do not run the 30-cell/full-contract matrix.
5. Return exact changed files, test counts, smoke record/seed/workload decisions, new source-copy SHA, and remaining uncertainty. Do not claim §3/§4 closure or 09D acceptance.

Use stdlib-only/minimal changes and preserve all evidence directories.

Write exactly one output file:

`runs/execution/mm_r7_slice09d_implementation_20260831/worker_02_followup_05.md`

The runner persists it; do not write this path directly through tools.
