This is continuation round 5 in the SAME conference session. Do not restart, replace, or open a new conference.

Re-audit the CURRENT filesystem only. Round-4 line numbers are stale. Codex addressed every confirmed round-4 defect and narrowed the canonical success fixture to the actual daily 08B atom boundary:

1. Canonical R2 projection now receives data absence from `current_present is False` and `data_change_kind in {"missing", "cannot_compare"}`. Focused negative cases cover both paths.
2. Top-level `identity.site_scope_text` now follows publication coverage order but takes every display label from the typed R5 `site_audience` projection. A custom non-derived Chinese label is asserted at both identity and row levels.
3. The canonical daily success fixture now contains exactly one risk item and one Query item, matching its one extracted risk atom and one extracted Query atom. Its ordinals are reindexed contiguously. The separate >200-row case is an algorithmic truncation stress case; it is not offered as evidence of one-to-one source semantics.
4. Non-risk rows now resolve `risk_ref` and `risk_instance_ref` independently, reject unresolved hints, and require both hints to identify the same R5 risk when both are present.
5. Risk rows with a nonempty but missing event now fail closed, and the risk anchor must exist in the bound event's `risk_anchor_refs`. Two focused endpoint negatives cover missing event and mismatched anchor.
6. The canonical producer helper `build_verified_carry_forward_item` now materializes `source_object_id`, `source_identity`, and `target_object_id`; the endpoint still independently verifies member/hash/run/bytes and the exact re-extracted `(artifact_id, object_type, source_object_id, item_digest)` tuple.
7. The product-authority sidecar remains bound into the R5 product `authority_hash`, and that hash remains bound into the R5 publication aggregate digest when available, with the legacy generic handoff path unchanged.

Current deterministic evidence from this exact filesystem:

- Product router + R5 subject-flow suites: `115 passed`.
- R5 publication-authority focused suite: `5 passed`.
- R7 continuity + continuity bridge + launch-registry suites: `60 passed`.
- Focused Slice-08C-1 subset: `25 passed`.
- No service, browser, or real project was started or used.

Please judge only the frozen Slice-08C-1 endpoint contract and distinguish:

- a confirmed product defect;
- an evidence-strength improvement;
- future work not required by the frozen contract.

The frozen contract does not declare that every target object must have a unique source atom or prohibit legitimate many-to-one carry-forward provenance. Do not invent such a new invariant. The canonical success fixture no longer duplicates a source atom within one object type. The >200 stress test exists only to verify deterministic display capping.

Return a COMPLETE replacement Markdown report with a clear `ACCEPT` or `REVISE` verdict. If `REVISE`, identify a concrete current contract violation with current file evidence and a bounded remedy. Do not edit files, start services/browsers, use real project data, or claim final Codex acceptance.
