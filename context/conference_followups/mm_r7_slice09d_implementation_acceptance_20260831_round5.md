Conference role: independent acceptance reviewer. Continue the same read-only conference session for task `mm_r7_slice09d_implementation_acceptance_20260831`.

Review the new accepted-seam capacity adapter and the next full-run admission decision only. Do not write files or revive closed §5 findings.

Read:
- frozen contract §2–§4 and §8
- `artifacts/mm_r7_slice09d_implementation_20260831/accepted_seam_measurement.py`
- current `measurement_runner.py`, `measurement_schema.py`, `test_measurement_runner.py`
- final bounded proof `measurement_bounded_t0_t1_20260831_final/{capacity_statement.md,stat_summary.json,environment_manifest.json,measurement_manifest.json}`
- `runs/execution/mm_r7_slice09d_implementation_20260831/worker_02_followup_02.md`

Codex independently observed: artifact 43/43; R7 526/526; bounded proof 98 records, C01 cold/warm, all correctness green, accepted backend name, status `inconclusive_environment_drift` because the workspace has no Git metadata.

Decide:
1. Does every accepted backend workload call the real 09A–09C seam and retain enough product state/correctness evidence, with no silent fallback to `synthetic_fixture_io`?
2. Are first/same-value backup and first/same-value restore semantically distinct and correctly measured; are public read, reopen/recovery-ready and progress observations real product reads?
3. Is the bounded proof enough to mark adapter readiness only (not capacity), or are there defects before any full run?
4. For this non-Git copied workspace, may a deterministic source-copy revision manifest (hashing all relevant accepted product/artifact source files, frozen contract, corpus, Python/SQLite/arch/memory facts) plus a pre/post unchanged verification serve as the contract's revision/clean evidence? Or does the frozen text strictly require a Git commit and dirty-tree=false? Give the smallest truthful route; unknown must remain inconclusive.
5. Should the full 30-cell run be launched now, or should a source-revision evidence artifact/runner fix occur first?

Return P0-P4 findings for adapter readiness, `ACCEPT_ADAPTER` or `REVISE_ADAPTER`, and the exact next command/evidence requirement. Do not accept §3/§4 capacity without the full run.
