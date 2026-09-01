Continue the same `worker_03` session. Codex reviewed the current files and resolves the
contract question in favor of the written product decision: a non-empty candidate group may
have `recommended_candidate_id == ""` when every visible candidate is pending, manual-only,
or otherwise unsafe. Do not point the recommendation slot at an unbound pending scaffold.

You are now explicitly authorized to make the smallest compatible change to
`packages/contracts/workbench_contracts/models.py`: allow an empty recommended id for a
non-empty group, while preserving the invariant that any non-empty id must reference exactly
one candidate in the same group. Preserve existing payload compatibility. Inspect current
frontend/progress consumers; change them only if they do not already handle empty safely.

Then:

1. Change `_recommended_candidate_id_for_group` to return the first safe candidate or `""`;
   never fall back to a pending/manual/unsupported card.
2. Add exact model, serialization, progress, and enrich-level tests for pending-only empty,
   mixed safe selection, and invalid non-empty ids.
3. Add negation guards to the remaining ad-hoc `design.open_label_extension` extraction so
   “非开放标签扩展 / non-open-label extension” cannot yield a positive fact, while the
   positive r4 phrase still can.
4. Defense in depth in `adopt_prefill_candidate`: reject a target with
   `evidence_status == "insufficient"` or a
   `声称内容未在引用原文中出现：...` gap before any verifier result, with a no-mutation test.
   Preserve worker_01 and worker_02 state-machine/catalog/adoption work.

Re-read every shared target before editing. Run the impacted contract, AI, evidence-binding,
corpus-bridge, journey/single-gate, and complete focused authoring-prefill suite. Return the
complete report schema with round-2 changes, hashes, and any residual risk.
