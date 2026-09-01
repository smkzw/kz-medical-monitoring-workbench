# Worker 03 same-session correction 3: close final product P2 findings

Continue in original Worker 03 session and product/harness/test boundary. Independent read-only acceptance found
four product P2 gaps. Fix them narrowly:

1. Before finalize, explicitly require the reserved publication snapshot_ref/source_revision/data_cutoff to equal
   the current snapshot resolved from the frozen snapshot option token; mapping drift must become blocked. Add a
   product test that mutates the token->snapshot mapping between launch/reserve replay and publication and proves
   result remains unavailable.
2. For completed runs with any non-available publication state, `publication_status_text` must include/follow the
   frozen contract text `分析已结束，结果整理未完成`; keep machine state fields for diagnosis and do not expose logs.
3. Reclassify audit-chain integrity failure from recoverable runtime read failure to a nonrecoverable blocked gate
   (reuse the narrow receipt/integrity gate code, no new public jargon). Add focused proof.
4. `result-entry` must reconstruct the authoritative publication gate/receipt attempts for the exact run and pass
   those attempts to the injected provider, then compare the reconstructed receipt-set digest/identities with the
   available publication before re-fetching R5. Do not use `attempts=()`. Extend the actual typed provider test so
   the second call requires non-empty persisted attempts and fails closed on receipt drift.

Run focused slice07c3 and full explicit-path product/R7/R5 regression; report exact counts. Do not edit registry or
R5 source, frontend, medical-writing, real projects, or start services/ports/models. Return complete updated Worker
03 report; no final acceptance.
