Continue the same Hermes/aishuo/cms-model Worker 05 session. Fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. This is one bounded completion pass after Codex/Worker 06 supplied the exact UNIFI local-authority source.

Work only inside runner workdir `.`. Do not call network, product AI, OCR, translation, browser or Word.

Runner-managed report path: `runs/execution/mw_e3_live_12lane_harness_20260723/worker_05_unifi_fixture_followup.md`. Never write it with tools; return final report text.

Read prior Worker 05 report, Worker 06 followup report/QC/receipts, the existing extractor, manifest/QC/four fixtures, and exact source `protocol-corpus/raw/NCT02407236/UNIFI_Protocol_Amendment2_local_archive.pdf`.

Authorized writes remain:
- `frontend/tests/final_release_12lane_extract_synopsis_fixtures.py`
- files under `records/active_slices/medical_writing_e3_12lane_harness_20260723/synopsis_fixtures/`

Required:
1. Change only the UC_III source subpath to the explicit selected canonical local-archive filename. Preserve expected SHA `f5d4e649...c923`, physical pp25-39, true UNIFI/NCT/Phase III identity and label `versioned_exact_synopsis_extract_for_e3`.
2. Re-run source SHA/page checks, generate the UC_III exact-page PDF losslessly, then regenerate the complete five-entry manifest and QC. Keep four previously valid fixtures byte-stable; fail if their hashes change unexpectedly.
3. Verify all five fixture PDFs open, page counts equal 4/11/7/8/15, no page is blank, first/last text evidence hashes exist, source hashes match, and `content_modified:false`.
4. Run the script `--verify-only` after generation. Record actual generation pypdf version/license and do not hard-code a different version.
5. Remove all stale “source missing”/blocked claims from current manifest/QC while retaining prior blocked report as historical evidence.

End `WORKER_05_E3_UNIFI_FIXTURE_COMPLETE` only if all five pass, otherwise `WORKER_05_E3_UNIFI_FIXTURE_BLOCKED`.
