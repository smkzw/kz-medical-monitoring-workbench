Delegated mode. Conference role: independent acceptance reviewer. Continue the same read-only session for task `mm_r7_slice09d_implementation_acceptance_20260831`.

Review only the completed Slice-09D §3/§4 full-run evidence and whether the 09D checkpoint may now close. Do not write files, do not reopen accepted §5 or adapter-readiness decisions, and do not extend the result to R7, R8, real projects, medical quality, a general SLO, or commercial capacity.

Read these files only:

- `reviews/medical_monitoring_r7_slice09d_capacity_performance_recovery_contract_v0_2_20260831.md` (§2–§4, §7–§8)
- `context/medical_monitoring_r7_slice09d_full30_v3_interrupted_pause_20260831.md`
- `runs/execution/mm_r7_slice09d_implementation_20260831/worker_02_followup_04.md`
- `runs/execution/mm_r7_slice09d_implementation_20260831/worker_02_followup_05.md`
- `artifacts/mm_r7_slice09d_implementation_20260831/source_copy_identity_v0_1.json`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_runner.py`
- `artifacts/mm_r7_slice09d_implementation_20260831/measurement_schema.py`
- every top-level evidence file in `artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831_v4/`: `capacity_statement.md`, `determinism_v0_2.json`, `environment_manifest.json`, `measurement_manifest.json`, `raw_measurements.jsonl`, `stat_summary.json`

## Hard boundaries

- Read-only review; do not modify any workspace file or run services, models, browsers, real projects, real data, or additional measurements.
- Review only §3/§4 and the Slice-09D checkpoint from the listed evidence.
- Do not revive accepted §5 or adapter-readiness findings.
- Do not accept R7, R8, real-source admission, medical quality, a general SLO, or commercial capacity.
- Treat invalidated v1/v2 and interrupted v3 as excluded evidence.
- Return the complete review; do not write the runner-owned report with tools.

Write exactly one output file:

`runs/conference/mm_r7_slice09d_implementation_acceptance_20260831/general_single_object_round6_full30_v4.md`

The runner persists it.

Codex independently observed on the final `_v4` directory:

- runner exit 0;
- 2450 raw records, 30 cells, 15 profiles, two modes, seven workloads;
- trial kinds: 1470 screening, 140 calibration, 840 confirmation;
- three trial seeds 20260831–20260833;
- 2450/2450 `decision=observed_green`, correctness `ok=true`, identity true, accepted seam invoked, resource green;
- zero `dependency_not_measured` and zero `child_output_incomplete`;
- determinism 225/225 cells passed (15 profiles × 5 hash seeds × 3 optimization modes);
- source-copy post-validation verified 70/70 with both re-hashes matching SHA-256 `2b771fb1f3705241bda2ecbb35607a1f736c056eaa424cccd6f881c479be3ccd`;
- all `measurement_manifest.json` declared file sizes/hashes revalidated with zero mismatch;
- artifact unittest suite 53/53 passed after the run;
- 8911/5174/8984 had no listener, no measurement process remained;
- raw SHA-256 `6ca8e9def7bf48090bfa34d7be052d972b4260df7e93fd14c1639852a934a7a3`.

Challenge those observations against the actual files. In particular examine:

1. Whether the exact contract-directed screening/calibration/confirmation selection and 3-seed × 10-repeat confirmation semantics are satisfied, rather than merely the total count.
2. Whether each cell/workload decision can be recomputed from raw evidence, with no hidden red/yellow/inconclusive samples, downstream dependency omissions, or accepted-seam fallback.
3. Whether watchdog, progress, resource, environment, source-copy pre/post, determinism, statistical summary, capacity statement and manifest evidence satisfy §3/§4 and §8 without overstating the observed boundary.
4. Whether `accepted_09a_09c_product_capacity=false` and `product_capacity_status=adapter_readiness_bounded_only` in the final full-run summary/manifest/capacity statement are a truthful conservative scope guard, a misleading stale label that blocks acceptance, or an implementation/reporting defect. Distinguish evidence validity from wording/status defects and assign severity.
5. Whether v1/v2 invalidated runs and v3 interrupted evidence remain clearly excluded, and whether `_v4` is the only admissible full-run evidence.

Return a compact report with:

- P0–P4 findings, each tied to exact file/field evidence;
- `ACCEPT_09D_CHECKPOINT` or `REVISE_09D_CHECKPOINT`;
- explicit decisions for §3, §4 and 09D only;
- the precise capacity wording that may be recorded for this workstation/source/corpus;
- exact required fix/recheck if any;
- confirmation that R7/R8/real-source/model/browser/UI work remains outside this decision.

Do not infer acceptance from counts alone. Do not claim general product support or an SLO.
