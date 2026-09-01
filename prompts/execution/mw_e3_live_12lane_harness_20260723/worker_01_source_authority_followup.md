You are continuing the same Hermes/aishuo/cms-model Worker 01 session. Fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. This is one bounded source-authority correction after Codex reviewed your completed oracle pass.

Work only inside the runner workdir `.`. Do not call product AI, network services, OCR, translation, browser or Word.

Runner-managed report path: `runs/execution/mw_e3_live_12lane_harness_20260723/worker_01_source_authority_followup.md`. Never write this report with tools; return the full report in the final response.

Read these files only:
- `AGENTS.md`
- `context/mw_e3_live_12lane_harness_20260723_execution_context.md`
- `runs/execution/mw_e3_live_12lane_harness_20260723/manager.md`
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_01.md`
- `frontend/tests/final_release_12lane_config.mjs`
- `frontend/tests/final_release_12lane_oracle_manifest.mjs`
- `frontend/tests/final_release_12lane_oracle_qc.mjs`
- `records/active_slices/medical_writing_e3_12lane_harness_20260723/WORKER_01_ORACLE_RECORD.md`

The context now contains a verified six-cell authority section. Five PDF cells are not `missing_authority`: their authoritative matching protocols and exact Synopsis page ranges are known, but the versioned exact-extract fixture does not yet exist. Only UC Ib is directly importable now.

Authorized write set remains exactly:
- `frontend/tests/final_release_12lane_config.mjs`
- `frontend/tests/final_release_12lane_oracle_manifest.mjs`
- `frontend/tests/final_release_12lane_oracle_qc.mjs`
- `records/active_slices/medical_writing_e3_12lane_harness_20260723/WORKER_01_ORACLE_RECORD.md`

Required corrections:
1. Add a source-authority catalog for all six cells using the exact protocol hashes and physical page ranges from context. For RA I/III, AD I/III and UC III use `authority_class: authoritative_protocol_synopsis_pages` plus `fixture_status: blocked_pending_exact_extract`; preserve true indication, phase, NCT/protocol identity, protocol path/hash and page range. Do not create extracts and do not put the full protocol path in `synopsisSourcePath` or product inputs.
2. Replace `blocked_missing_authority` on those five lanes with `blocked_pending_exact_extract`. Keep `synopsisSourcePath: null`, `override_allowed: false`, and an explicit block reason. UC Ib stays `exact_synopsis_file` and directly runnable.
3. Make UNIFI NCT02407236 Phase III UC the preferred drug-trial structure oracle for documented futility interim analysis, Week 8 treatment switch, maintenance re-randomization and LTE adjustment. Assign `interim_analysis_treatment_switch` and `rescue_re_randomization_ole` coverage to UC III design without relabelling any Phase 2b/3 or device study. RESET-RA remains device/secondary only; AD NCT05732454 remains true Phase 2/3 and cannot satisfy a pure Phase III drug gate by itself.
4. Coverage validation must distinguish assigned design pressure from runnable coverage. A pressure carried only by a blocked synopsis lane does not make the live 12-lane suite runnable. Export an explicit `RUNNABLE_COVERAGE_GAPS` or equivalent.
5. Add `synopsis_import_receipt.json` to the evidence filename contract if absent.
6. Extend behavior tests to prove: authoritative protocol pages are not product inputs; blocked-pending-extract differs from missing authority; full protocol cannot become synopsisSourcePath; UNIFI retains Phase III and supplies the intended feature evidence; required pressure coverage and runnable coverage are separately reported.
7. Re-run oracle QC. Do not modify stale `final_release_12lane_structure_qc.mjs`; Worker 04 owns its rewrite, so record its expected old-contract failures rather than weakening the new oracle.

End with `WORKER_01_E3_ORACLE_SOURCE_REFINEMENT_COMPLETE` only if the updated oracle tests pass. Otherwise use `WORKER_01_E3_ORACLE_SOURCE_REFINEMENT_BLOCKED`.
