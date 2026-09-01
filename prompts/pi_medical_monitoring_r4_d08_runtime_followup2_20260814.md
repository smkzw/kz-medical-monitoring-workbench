# D08 runtime follow-up 2 — independent verifier REVISE remediation

Resume the same implementation session. Fresh independent verifier report: `runs/review/medical_monitoring_r4_d08_runtime_luna_acceptance_20260814.md`, verdict `REVISE_D08_RUNTIME`. Read it fully and remediate every P0-P2 finding below in the existing allowed D08 runtime/test files only. Do not touch frozen artifacts, D01-D07, medical-writing, services, or port 8911.

Blocking reproductions to fix:

1. Global ordered fail-closed: `evaluate()` must validate typed input and run the contract's ordered pre-evaluator integrity checks for **every** family before cutoff/medical evaluation. Snapshot mismatch, spine mismatch, required-producer L0 gap, authority gap, node identity/locator/correction gap, routing gap, expected-set admission, and producer binding gap must emit only first integrity error and absolutely no medical/risk/Query/Journey output. Empty/malformed bundles must not become positive.
2. Propagation: use structured facts; compare declared, actual consumed, and source revisions correctly; missing derived objects must be detected by absence/reference resolution rather than sentinel IDs. Add verifier's case: actual=REV5, source=declared=REV4, no derived object must not return in-sync negative. Faithfully represent/enforce the v0.6 propagation result states.
3. Temporal direction: in `temporal_matrix`, point inside interval must be `contained_by`, not `contains`; add direct point/interval and interval/point tests for all relevant directions without relying on the other family's flip.
4. Reverse conservation/cardinality: enforce exact bidirectional identity-set and cardinality constraints, including duplicate reverse edges. One forward + two duplicate reverse edges cannot be conserved negative. Cover missing, extra, duplicate, wrong-pair, and equality cases.
5. Visibility: reject or fail closed on projectable intersect blinded/forbidden, or deterministically subtract hidden nodes before every audience payload. `disclosure_leak_present` must reflect conflict; no hidden source/evidence/jump may leak. Add conflicting-set tests.
6. Enforce parsed structured fields that determine correctness: actual_consumed_revision, source_record_node_id, raw/materialized bijection, reverse identity sets, cardinality, relevant scope/coverage. Remove behavior that converts absent raw/resolve data into a positive risk unless a structured obligation proves a required missing relation.
7. Remove all synthetic sentinel decision coupling (`SRC-REV-000`, `SYN-STABLE-MISSING-000`, or equivalent magic values). Replace with closed typed facts and test-only adapter compatibility bridges if frozen fixtures are under-specified. Runtime must be invariant to ID/value renames.
8. Strengthen anti-overfit tests: `same_substantive_input_same_outcome` must execute runtime; run surface-renaming across all applicable 233 cases or a justified exhaustive partition, not three handpicked cases. Add independent regression tests matching each verifier probe.

Also resolve any newly exposed oracle mismatch semantically; do not relax exact matching, alter frozen files, branch on IDs/prose, or move expected decisions into runtime.

Run from workbench root: focused D08, full R4, R1-R3, generator tests, Ruff/compile, frozen hashes, and 8911 stopped. Return exact changed hashes/results and residual risks. Do not claim acceptance.
