You are Hermes/aishuo/cms-model acting as a bounded source-acquisition execution worker inside E3. Fully read and comply with `/Users/smkzw/.hermes/SOUL.md` and workspace `AGENTS.md`.

Work only inside runner workdir `.`. This task obtains already identified authoritative protocol PDFs into the canonical E3 source paths. It does not create, translate, summarize or medically interpret content.

Runner-managed report path: `runs/execution/mw_e3_live_12lane_harness_20260723/worker_06_official_protocol_acquisition.md`. Never write this report with tools; return the complete report in final text.

Read:
- `AGENTS.md`
- `context/mw_e3_live_12lane_harness_20260723_execution_context.md`
- `frontend/tests/final_release_12lane_config.mjs`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/protocol_structure_corpus/candidate_manifest.json`
- existing local source `records/research/medical_writing_autoimmune_phase1_biologic_corpus_20260716/raw/documents/NCT03156023/Prot_000.pdf`
- existing local source `records/research/medical_writing_autoimmune_phase1_biologic_corpus_20260716/raw/documents/NCT04668066/Prot_000.pdf`

Authorized exclusive write set:
- new files only under `protocol-corpus/raw/NCT03156023/`, `protocol-corpus/raw/NCT02629159/`, `protocol-corpus/raw/NCT04668066/`, `protocol-corpus/raw/NCT03745638/`, `protocol-corpus/raw/NCT02407236/`
- new `records/active_slices/medical_writing_e3_12lane_harness_20260723/PROTOCOL_ACQUISITION_RECEIPTS.json`
- new `records/active_slices/medical_writing_e3_12lane_harness_20260723/PROTOCOL_ACQUISITION_QC.md`

Hard boundaries:
- Do not edit config/oracle, fixture extractor, harness, production source, credentials or existing source files.
- Do not call product AI, OCR, translation, browser automation or Word.
- Network is allowed only for the three exact official ClinicalTrials.gov URLs below. No search and no third-party mirrors.
- Download to a task-owned temporary filename in the target directory, verify, then atomically rename to `Prot_000.pdf`. Never expose a partial canonical file.
- If a canonical file already exists, verify SHA and reuse only on exact match; otherwise fail closed without overwrite.

Source contract:
1. NCT03156023: copy the named local file; expected SHA-256 `83c13414a14b6ea445016f005627177cb5dc4d6ab974aadaf74e3df049bf3f85`.
2. NCT04668066: copy the named local file; expected SHA-256 `3bbbbeeaf2d1ee8012ae1c28a0199ef46df471ee20a2bdd0ce607a79f9861a4a`.
3. NCT02629159: `https://clinicaltrials.gov/ProvidedDocs/59/NCT02629159/Prot_000.pdf`; expected SHA-256 `48b6154c0e1f0fd9e05938c3e5ad0878b2438c69f49174e6e21da781b35fef0b`.
4. NCT03745638: `https://clinicaltrials.gov/ProvidedDocs/38/NCT03745638/Prot_000.pdf`; expected SHA-256 `035f37d3fece57f5dd238378b6b36c186babb7c2a27afafc78005bafeb021c91`.
5. NCT02407236: `https://clinicaltrials.gov/ProvidedDocs/36/NCT02407236/Prot_000.pdf`; expected SHA-256 `f5d4e6498cba6b78c1d41fc186b1865b066727019c63831d8ea198bd12abc923`.

Required work:
1. For the two local files, verify source SHA before copying; copy atomically and verify target SHA.
2. For the three downloads, use curl with redirect following, fail-on-HTTP-error, bounded retries and connection timeout. Record requested URL, final effective official CDN URL, HTTP status, content type and byte count without cookies/credentials.
3. Verify `%PDF-` header, non-trivial size, parseability and page count with the already installed permissive `pypdf` package. Verify the exact expected SHA before atomic rename.
4. Produce machine-readable receipts with schema version, NCT, source class, requested/final URL or local source path, target relative path, expected/observed SHA, bytes, page count and verification status. Do not add wall-clock-dependent fields that impair deterministic comparisons; a separate report may state execution date.
5. Produce compact QC Markdown. Re-run an all-five verify-only pass after placement.

End with `WORKER_06_E3_PROTOCOL_ACQUISITION_COMPLETE` only if all five canonical files exist, parse and match exact hashes. Otherwise `WORKER_06_E3_PROTOCOL_ACQUISITION_BLOCKED`.
