You are continuing the same Hermes/aishuo/cms-model Worker 01 session. Fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. This is one final bounded clinical-design alignment correction after Codex reviewed the source-authority refinement.

Work only inside runner workdir `.`. Do not call product AI, network services, OCR, translation, browser or Word.

Runner-managed report path: `runs/execution/mw_e3_live_12lane_harness_20260723/worker_01_design_alignment_followup.md`. Never write this report with tools; return the full report in the final response.

Read:
- `AGENTS.md`
- `context/mw_e3_live_12lane_harness_20260723_execution_context.md`
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_01.md`
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_01_source_authority_followup.md`
- `frontend/tests/final_release_12lane_config.mjs`
- `frontend/tests/final_release_12lane_oracle_manifest.mjs`
- `frontend/tests/final_release_12lane_oracle_qc.mjs`
- `records/active_slices/medical_writing_e3_12lane_harness_20260723/WORKER_01_ORACLE_RECORD.md`

Authorized write set remains exactly the four Worker 01 files above.

Codex found a material mismatch: SELECT-COMPARE is an active-comparator RA Phase III source, but TRuE-AD1 is vehicle controlled and UNIFI is placebo controlled with switch/re-randomization. The current lane matrix wrongly labels AD_III_SYNOPSIS and UC_III_SYNOPSIS as `active_comparator` and even invents dupilumab/etrasimod comparator facts that are not supported by those source synopses. Correct this without changing source authorities or page ranges.

Required corrections:
1. Keep `active_comparator` assigned only to source-backed RA_III_SYNOPSIS / SELECT-COMPARE (adalimumab). Remove invented dupilumab and etrasimod active-comparator facts.
2. Give AD_III_SYNOPSIS a source-faithful vehicle/placebo-controlled Phase III design-pressure label. Give UC_III_SYNOPSIS a source-faithful placebo induction/maintenance plus switch/re-randomization design-pressure label. Reuse an existing truthful pressure only if semantics match; otherwise add compact explicit pressure constants and coverage tests.
3. Keep UC_III_SCRATCH as the main runnable interim-analysis/switch/re-randomization/OLE pressure lane based on UNIFI structure oracle. Do not claim the blocked synopsis lane is runnable until its exact fixture exists.
4. Make `RUNNABLE_COVERAGE_GAPS` and the record table internally consistent. Active comparator has one assigned blocked lane before extract and must become runnable after fixture mapping; no AD/UC lane may be counted as active comparator.
5. Add deterministic assertions that reject any active-comparator assignment unless the source/oracle explicitly names the active comparator. Assert TRuE-AD1 and UNIFI retain their actual comparator semantics.
6. Run oracle QC and update the record. Do not edit stale structure_qc.

Do not weaken tests to `>=` merely to absorb wrong assignments. End with `WORKER_01_E3_DESIGN_ALIGNMENT_COMPLETE` only if all checks pass; otherwise `WORKER_01_E3_DESIGN_ALIGNMENT_BLOCKED`.
