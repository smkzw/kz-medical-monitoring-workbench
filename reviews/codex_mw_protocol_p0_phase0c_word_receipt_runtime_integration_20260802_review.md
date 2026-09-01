# Codex Review: mw_protocol_p0_phase0c_word_receipt_runtime_integration_20260802

Date: 2026-08-02 (Asia/Shanghai)
Execution: direct parent Codex; no delegated output was dispatched.
Evidence: `/private/tmp/mw_word_runtime_integration.tTUCV1/runtime_integration_evidence.json`
Workflow guard/Hermes review-gate was used for task initialization, prompt preflight, and this acceptance record.

## Verdict

`PASS_FOR_BOUNDED_RUNTIME_INTEGRATION; NOT_READY_FOR_PROTOCOL_RELEASE`

## Boundary Check

- The only HTTP runtime root was task-owned `/private/tmp/mw_word_runtime_integration.tTUCV1`; no production or r42/v36 path was used.
- The app was started on port `18928`, then stopped; no listener remained.
- The temporary import-created provider settings/secrets files were task-local; the secrets file was `{}` and no credentials were copied into records.
- No OCR, translation, model, download, upstream document, Synopsis, CSR, or monitoring runtime operation occurred.

## Codex Verification

- Actual Uvicorn HTTP path: first receipt POST `200`, `preview_status=word_verified`, `replayed=false`.
- Same HTTP body/idempotency key: `200`, `replayed=true`, identical audit ID; restart read found the same verification ID and one audit row.
- Stale source snapshot: `422`, `Word verification receipt is stale for the current document snapshot`.
- Mismatched DOCX hash: `422`, `Word verification receipt DOCX hash does not match the exported document`.
- Durable export job: `completed`; artifact SHA-256 matched the receipt DOCX SHA-256 (`9698758634accda9...f9484b`).
- This review does not re-accept Word visual layout; that is covered by `reviews/codex_mw_protocol_p0_word_native_final_gate_fixture_20260802_review.md`.

## Delegated-Agent Output Review

Not applicable: no child agent or external provider was used. Direct Codex checked the actual files, HTTP responses, SQLite restart read, and listener shutdown.

## Residual Risk

- The synthetic seams bypass full production project/authoring state; this proves the route/job/repository contract, not end-to-end authoring or source-preserving export.
- A canonical page-byte hash adapter is still a release checklist item; the existing Word/PDF fixture used direct PDF and rendered-page hashes.
- Protocol P0 remains not release-ready until the broader framing/corpus/runtime acceptance gates are passed.
