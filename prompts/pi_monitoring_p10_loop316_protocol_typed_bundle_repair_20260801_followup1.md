Continue the same bounded edit session. Codex reviewed the current implementation and
found the following actionable gaps. Re-read the four authorized current files before
editing; preserve all unrelated changes. Do not read any new source, start services,
inspect runtime data, call a provider, retry jobs or run the full suite.

Fix all of these in the same four authorized paths:

1. Empty list identity is not typed identity.
   - A list title/item with empty `parent_match_source_ids` must not form a repairable
     group even when both are present.
   - Provider focus must not add a title for such an item.
   - Helper and service validation must fail closed with a deterministic error.
   - Add a test where title and item both have empty ancestry.

2. Repair must cover every provider-selected semantic evidence ID, not only
   `structured_payload.evidence_ids`.
   - Build the ordered original selection from structured evidence IDs, exact
     conflict evidence IDs and every claim evidence ID.
   - Expand structural context from that union, persist the union/repair lineage and
     keep exact conflict evidence sets unchanged.
   - Automatically added structural context must never be inserted into a claim's
     evidence IDs.
   - Apply the post-expansion 50-ID cap to the final union.
   - Add tests proving a table/list ID cited only by a claim is closed and validated,
     and that a claim-only header/title without a data-row/item semantic anchor fails.

3. Add claim-level original semantic-anchor validation.
   - If a claim cites table structure, it must cite at least one provider-selected
     non-header data-row cell; header-only claims fail.
   - If a claim cites list structure, it must cite at least one provider-selected list
     item from each cited list; title-only claims fail.
   - Server-added headers/titles remain context-only and cannot make a claim pass.
   - Do not use text similarity or infer claim semantics.

4. Bind candidate identity to the server-normalized protocol structured payload,
   including repair lineage/version.
   - For protocol candidates only, the candidate-ID seed must replace the raw provider
     structured payload with the normalized server payload.
   - Other task identity behavior must remain unchanged.
   - Add a deterministic test proving identical raw provider output under different
     repair lineage/version cannot silently retain the same candidate identity, or a
     direct unit test proving the normalized protocol payload participates in the ID
     seed.

5. Strengthen persisted lineage typing.
   - Replace the untyped optional `Dict[str, Any]` repair lineage field with explicit
     Pydantic models/literals for schema version and table/list binding shapes.
   - Keep provider-forged lineage rejection before normalization.

Re-run:

- `python -m pytest tests/test_monitoring_ai_source_packet.py -q`
- `python -m pytest tests/test_monitoring_ai_service.py -q -k "protocol"`
- both authorized test files in full.

Return a compact delta handoff with changed-path hashes, exact test counts, remaining
risk and Codex-owned checks. Do not claim final acceptance.
