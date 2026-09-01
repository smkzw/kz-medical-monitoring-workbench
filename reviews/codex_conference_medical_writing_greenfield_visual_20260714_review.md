# Codex Main-Venue Review: Medical Writing Greenfield Runtime

Date: 2026-07-14
Decision: accepted for the current product slice; production AI writing route unchanged

## Evidence used

- Live Chrome CDP workflow and screenshots: `records/visual_qc_20260714/medical_writing_greenfield_runtime_v4/`.
- Automated result: `medical_writing_greenfield_qc.json`, `failures=[]`.
- Backend/frontend regression: 182 medical-writing tests passed in 72.48 seconds.
- Production build: Vite build passed; the existing chunk-size warning is non-blocking.
- Advisory conference: MiniMax-M3 and qwen3.7-plus completed three rounds; Kimi and Mimo failed as recorded in conference metrics.

## Final visual and interaction judgment

1. The greenfield setup correctly occupies the existing editor column. It does not displace the AI interaction rail or document structure map, so the writing workbench remains editor-first.
2. The setup, decision-review panel, table designer and edited document preserve the same three-column desktop hierarchy at 1600x1000, 1920x1080 and 2048x1024. No horizontal page overflow or incoherent overlap was detected.
3. Candidate and pending states now use warning semantics. The document is never represented as approved, and formal Word remains blocked until approval gates pass.
4. Project decisions are no longer a one-way setup artifact. Users can revisit them, provide the determined value, rationale and source/confirmation record, and update the versioned baseline.
5. Structured tables are inserted and edited inside the same workbench; the full-screen designer is available once a table exists. Empty sections do not show table-specific controls because those actions have no valid target.

## Conference disposition

- Accepted: explicit post-creation decision review; stronger pending-state semantics; clearer greenfield candidate boundary.
- Rejected: permanently reserving toolbar space for table selector/full-screen controls in sections without a table. This would create disabled noise and conflicts with the current context-sensitive editor contract.
- Qualified: MiniMax-M3 source/CSS observations only, because its image backend failed. qwen3.7-plus visual observations were checked against live browser behavior before use.
- Excluded: Kimi timeout packet and Mimo HTTP 400 packet; neither produced evidence adequate for product judgment.

## Residual risks and next work

- The Vite bundle remains above the default 500 KB warning threshold. It does not block this slice but should be addressed as a separate performance task, not mixed into the greenfield feature.
- Greenfield production AI generation remains intentionally unchanged pending expression-governance and medical blind-review acceptance.
- The next medical-writing slice should be selected from the active records after resume; this completed slice should not be rerun unless a regression is introduced.
