You are Hermes/aishuo/cms-model acting as a bounded execution worker inside the existing E3 execution module. First fully read and comply with `/Users/smkzw/.hermes/SOUL.md` and the workspace `AGENTS.md`.

Work only inside runner workdir `.`. This task creates reproducible, lossless page-extract fixtures from already verified authoritative protocol PDFs. It does not create medical content and does not use AI.

Runner-managed report path: `runs/execution/mw_e3_live_12lane_harness_20260723/worker_05_synopsis_fixture_extract.md`. Never write the report with tools; return it in the final response.

Read these files only:
- `AGENTS.md`
- `context/mw_e3_live_12lane_harness_20260723_execution_context.md`
- `runs/execution/mw_e3_live_12lane_harness_20260723/manager.md`
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_01.md`
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_01_source_authority_followup.md`
- `frontend/tests/final_release_12lane_config.mjs`
- `frontend/tests/final_release_12lane_oracle_manifest.mjs`

The five source protocols, SHA-256 values and physical Synopsis page ranges are authoritative in the execution context. Read those exact source files only for extraction/verification. Do not modify them.

Authorized exclusive write set:
- new `frontend/tests/final_release_12lane_extract_synopsis_fixtures.py`
- new files only under `records/active_slices/medical_writing_e3_12lane_harness_20260723/synopsis_fixtures/`

Hard boundaries:
- Do not edit config/oracle, parent/child/pipeline/QC or production source.
- Do not call product AI, external network, OCR, translation, browser or Word.
- Do not rasterize, reflow, translate, summarize or rewrite the source. Extract whole PDF pages losslessly into a new PDF.
- Before use, verify the installed `pypdf` package version and SPDX/license metadata. Continue only if it is a qualifying open-source permissive license (expected BSD-3-Clause); record exact evidence. Do not install or upgrade packages.

Required work:
1. Re-verify each source SHA from context before extraction; fail closed on mismatch.
2. Using `pypdf`, copy the exact physical page ranges into five deterministic fixtures: RA Phase I, RA Phase III, AD Phase I, AD Phase III and UC Phase III. Use zero-based indices derived explicitly from the physical ranges; prevent off-by-one.
3. Preserve page boxes, rotation and page content/resources. Use stable output metadata identifying fixture lane, source SHA, physical page range and extraction tool/version; do not embed a wall-clock timestamp in the PDF because reruns must reproduce the same bytes. Never claim the extract is sponsor-issued standalone synopsis; label it `versioned_exact_synopsis_extract_for_e3`.
4. Produce `extraction_manifest.json` containing schema version, lane, source absolute path, source SHA, true indication/phase/NCT/protocol identity, physical and zero-based ranges, output relative path/SHA/page count, tool/version/license, and `content_modified:false`.
5. Verify each output opens, has exactly the expected page count, has no blank page, and extracted text includes Synopsis/Protocol Summary plus the expected indication/phase evidence. Record first/last text evidence hashes, not bulky full text.
6. Produce `EXTRACTION_QC.md` with a compact source/output/hash/page table and precise limitations. Add a deterministic `--verify-only` mode to the script and run it after generation.
7. Do not map fixtures into product lanes in this worker. Worker 01/manager will do that only after Codex accepts hashes and provenance.

End with `WORKER_05_E3_SYNOPSIS_FIXTURES_COMPLETE` only if all five source/hash/page/text/output checks pass. Otherwise end with `WORKER_05_E3_SYNOPSIS_FIXTURES_BLOCKED`.
