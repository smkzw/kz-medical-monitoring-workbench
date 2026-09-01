This is continuation round 3 in the same session. Do not restart the task or open a new session.

Re-audit the CURRENT filesystem only. Earlier line numbers and findings may be stale. Codex has implemented additional corrections after your round-2 REVISE verdict:

1. Object-specific joins: risk rows require an R5 risk; query/output rows may bind directly to a typed R5 event without a risk association. Risk fields remain blank when no risk is bound.
2. R2 lifecycle semantics: risk rows now validate legal state/transition/evidence combinations for new, upgraded, continued, downgraded, closed, reopened, and needs_rejudgment.
3. Severity uncertainty: contract-permitted missing severity is retained with the closed Chinese attention text, while invalid aliases still fail closed.
4. Artifact provenance: every item now requires a non-empty source_artifact_sha256 equal to the committed R1 envelope content hash; optional source_run_id must match; committed bytes are verified.
5. Public window/baseline dates: comparison windows must be ISO dates with start <= end; baseline cutoff must be a valid ISO date.
6. Authority integrity: duplicate site/subject/event/source/risk and risk-instance identities are rejected before mapping.
7. Continuity-specific closure failures now return continuity_unavailable while a nonexistent result-context token remains result_context_unavailable.

New decisive tests include event-bound Query without risk mapping, false-closed lifecycle rejection, retained new risk with unconfirmed severity, source-artifact hash mismatch rejection, and incomplete R6 closure rejection. Current local evidence:

- product-router suite: 74 passed before the newest four tests; focused Slice-08C-1 now 14 passed;
- continuity/bridge/launch-registry adjacent suite: 60 passed.

Known questions that require a current-source judgment rather than assumption:

- whether the remaining site label `中心 {site_ref}` is acceptable under the frozen contract or still needs an upstream audience label;
- whether source_object_id/target_object_id and a canonical 08B atom receipt must be added in this slice beyond the now-enforced R1 artifact hash/run/member checks;
- whether the existing synthetic endpoint fixture still blocks acceptance despite the added negative/edge tests, and what smallest canonical integration test would close it;
- whether query/output should bind to a typed 08B query/material projection rather than the currently available typed R5 event.

Inspect at minimum:

- services/api/app/medical_monitoring_r7_product_router.py
- tests/test_medical_monitoring_r7_product_router.py
- poc/medical_monitoring_ai_native_r7/src/mm_r7/continuity.py
- poc/medical_monitoring_ai_native_r7/src/mm_r7/continuity_bridge.py
- reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_2_20260829.md

Return a complete replacement Markdown report with a clear ACCEPT or REVISE verdict. Separate confirmed current defects from upstream/future-slice improvements. Do not edit files, start services/browsers, use real project data, or claim final acceptance. Codex remains the final authority.
