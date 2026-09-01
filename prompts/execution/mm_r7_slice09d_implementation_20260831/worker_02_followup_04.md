Delegated mode. Continue the same bounded execution session for task `mm_r7_slice09d_implementation_20260831`, role `worker_02`.

## Hard boundaries

Stay inside `artifacts/mm_r7_slice09d_implementation_20260831/`; do not modify product source, real projects, services, browser/model paths, medical writing, or runner-managed reports. Do not delete or overwrite the completed first full-run directory `measurement_full_30cell_accepted_09a_09c_20260831/`. Do not run the 30-cell/full-contract matrix. The runner owns the report file below; do not write it through tools.

Read these files only:

- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_runner.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/accepted_seam_measurement.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_schema.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/test_measurement_runner.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/source_copy_identity.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/source_copy_identity_v0_1.json`
- `artifacts/mm_r7_slice09d_implementation_20260831/consolidated_total_manifest.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/generate_fault_recovery_artifacts.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/README.md`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831/raw_measurements.jsonl`
- `runs/execution/mm_r7_slice09d_implementation_20260831/worker_02_followup_03.md`

The first full accepted-seam run exposed a measurement-runner defect. Codex independently observed:

- Non-balanced profiles run `calibration` and then `screening` with `trial_index=0`.
- `run_measurement()` currently maps both to the same workspace path `trial_000`.
- The screening pass therefore reuses calibration state: `first_restore` returns `replayed=true`, and the adapter reports `no_overwrite=false` even though source/target semantic digest, atomicity, identity, closure, and terminal state all pass.
- `_child_main()` stops on that red; `_run_child_trial()` then fabricates red terminal records for all unexecuted downstream workloads with `child stopped before workload terminal state`.

Implement only the narrow measurement correction:

1. Make every trial workspace unique across `calibration`, `screening`, and `confirmation` while retaining deterministic, inspectable names. Do not change product restore behavior and do not weaken the correctness oracle.
2. Preserve truthful dependency semantics. When a child intentionally stops after a red workload, do not label unexecuted downstream workloads as independently observed product-red failures. Use the smallest schema-compatible representation that keeps aggregation fail-closed and explicitly identifies dependency-not-measured. If the frozen schema cannot support this without broad changes, keep the existing fail-closed records but add an unambiguous `backend_evidence.failure_class=dependency_not_measured` and `blocked_by_workload`; do not claim their product seams ran.
3. Add focused regression tests proving:
   - calibration and screening trial zero receive different workspaces;
   - a non-balanced accepted-seam profile can complete calibration plus screening without first-restore replay caused by workspace collision;
   - a deliberately red prerequisite does not masquerade downstream workloads as independently observed product failures.
4. Run the focused artifact tests and then the artifact suite. Regenerate source-copy identity and consolidated manifest if pinned files changed. Run only a bounded smoke sufficient to exercise a non-balanced calibration+screening profile; do not run the 30-cell/full-contract matrix.
5. Return exact changed files, test counts, smoke record counts/decisions, new source-copy SHA, and any remaining uncertainty. Do not claim §3/§4 closure or 09D acceptance.

Use stdlib-only/minimal changes and preserve all existing evidence directories.

Write exactly one output file:

`runs/execution/mm_r7_slice09d_implementation_20260831/worker_02_followup_04.md`

The runner persists it; do not write this path directly through tools.
