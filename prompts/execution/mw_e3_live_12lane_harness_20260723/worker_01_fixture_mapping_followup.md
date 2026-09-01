Continue the same Hermes/aishuo/cms-model Worker 01 session. Fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. This is the final bounded fixture-mapping pass after Codex accepted all five exact synopsis extracts.

Work only inside runner workdir `.`. Do not call product AI, network, OCR, translation, browser or Word.

Runner-managed report path: `runs/execution/mw_e3_live_12lane_harness_20260723/worker_01_fixture_mapping_followup.md`. Never write it with tools; return final report text.

Read:
- prior Worker 01 reports and current four Worker 01 files
- Worker 05 UNIFI fixture followup report
- Worker 06 UNIFI local-authority followup and receipt wording reports
- `records/active_slices/medical_writing_e3_12lane_harness_20260723/synopsis_fixtures/extraction_manifest.json`
- `records/active_slices/medical_writing_e3_12lane_harness_20260723/synopsis_fixtures/EXTRACTION_QC.md`
- `records/active_slices/medical_writing_e3_12lane_harness_20260723/PROTOCOL_ACQUISITION_RECEIPTS.json`

Authorized writes remain exactly:
- `frontend/tests/final_release_12lane_config.mjs`
- `frontend/tests/final_release_12lane_oracle_manifest.mjs`
- `frontend/tests/final_release_12lane_oracle_qc.mjs`
- `records/active_slices/medical_writing_e3_12lane_harness_20260723/WORKER_01_ORACLE_RECORD.md`

Required:
1. Update UC III protocol authority path to the real selected canonical file `protocol-corpus/raw/NCT02407236/UNIFI_Protocol_Amendment2_local_archive.pdf`, preserving source SHA `f5d4...c923`, physical pp25-39, local-archive provenance and true UNIFI Amendment 2 identity. Do not call it `Prot_000`.
2. For RA_I, RA_III, AD_I, AD_III and UC_III synopsis-import lanes, map `synopsisSourcePath` to the corresponding accepted PDF under `records/active_slices/medical_writing_e3_12lane_harness_20260723/synopsis_fixtures/`. Use the exact output SHA/page count/source SHA from extraction_manifest, mark ready, non-overridable, and authority/role `versioned_exact_synopsis_extract_for_e3`. Keep a provenance locator to extraction_manifest and source protocol authority. The full protocol never becomes product input.
3. Preserve UC_I standalone DOCX source unchanged. Result: all six synopsis-import lanes are runnable with exact indication/phase-compatible input.
4. Recompute DESIGN_PRESSURE_ASSIGNMENTS runnable lanes and remove resolved fixture gaps. Active comparator must still be RA_III_SYNOPSIS only; AD/UC comparator semantics remain corrected. No broad waiver.
5. Oracle manifest product_inputs must include only UC Ib DOCX or the five accepted extract PDFs, with exact hashes and declaration that extracts are task-created lossless page selections, not sponsor-issued standalone synopses.
6. Add tests that read extraction_manifest/receipts, verify every mapped fixture exists and hashes exactly, page counts are 4/11/7/8/15, protocol paths are absent from product_inputs, UC local archive path is exact, and all six synopsis lanes are runnable. Reject any stale `blocked_pending_exact_extract`, wrong UNIFI `Prot_000`, or output hash mismatch.
7. Run oracle QC. Update record with exact fixture hashes and acquisition provenance. Do not edit structure_qc.

End `WORKER_01_E3_FIXTURE_MAPPING_COMPLETE` only if all checks pass, otherwise `WORKER_01_E3_FIXTURE_MAPPING_BLOCKED`.
