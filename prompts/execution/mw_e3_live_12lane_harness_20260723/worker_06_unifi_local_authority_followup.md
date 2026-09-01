Continue the same Hermes/aishuo/cms-model Worker 06 session. Fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. This is one bounded remediation after Codex resolved the UNIFI source discrepancy.

Work only inside runner workdir `.`. Do not call product AI, OCR, translation, browser automation or Word. Do not search the network.

Runner-managed report path: `runs/execution/mw_e3_live_12lane_harness_20260723/worker_06_unifi_local_authority_followup.md`. Never write the report with tools; return it in final text.

Read:
- prior Worker 06 report and its two receipt/QC artifacts
- `records/active_slices/medical_writing_soa_builder_20260713/protocol_source_inventory.jsonl`
- local source `/Users/smkzw/Documents/朗来项目资料/竞品分析/UC/IL12&23mab Ustekinumab 强生/【III期 UNIFI】Protocol.pdf`

Codex independently verified this local source exists, has 3,363,873 bytes, 151 pages, begins with the UNIFI Phase 3 Amendment 2 protocol identity, and has exact SHA-256 `f5d4e6498cba6b78c1d41fc186b1865b066727019c63831d8ea198bd12abc923`. The source inventory independently records the same path, size, hash, page count and NCT02407236 evidence. The current official CT.gov API lists `Prot_002.pdf`; the prior Worker 06 inference that the CDN file was necessarily replaced is not proven and must be corrected.

Authorized writes:
- new `protocol-corpus/raw/NCT02407236/UNIFI_Protocol_Amendment2_local_archive.pdf`
- update `records/active_slices/medical_writing_e3_12lane_harness_20260723/PROTOCOL_ACQUISITION_RECEIPTS.json`
- update `records/active_slices/medical_writing_e3_12lane_harness_20260723/PROTOCOL_ACQUISITION_QC.md`

Required:
1. Verify the local source exact hash/size/page count and PDF identity before copy.
2. Copy through a task-owned temp in the target directory and atomically rename to the explicit non-misleading canonical name above. Verify target hash/size/pages/first-page identity after rename.
3. Update receipts: preserve the two failed `Prot_000` official-download observations as historical evidence, but mark them non-selected; add selected local archive provenance with absolute source path, inventory locator, exact hash and target. Do not claim the official file was replaced unless independently evidenced.
4. Update QC to 5/5 acquisition PASS while clearly distinguishing selected local archive from current official `Prot_002` and failed wrong-filename `Prot_000` attempt.
5. All-five verify-only pass must succeed. Do not edit config/oracle/fixture extractor; Worker 01 will map this explicit canonical path later.

End `WORKER_06_E3_UNIFI_LOCAL_AUTHORITY_COMPLETE` only if all five selected source artifacts pass; otherwise `WORKER_06_E3_UNIFI_LOCAL_AUTHORITY_BLOCKED`.
