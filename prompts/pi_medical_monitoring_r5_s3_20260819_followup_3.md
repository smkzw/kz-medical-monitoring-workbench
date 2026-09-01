# R5-S3 contract same-session targeted correction after independent review

Resume session `01a01580-b82d-7000-89ad-38be7ca8157d`. The frozen snapshot was independently rejected. Execute the correction now; do not return a plan-only response.

Workspace: `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`

Keep all prior gates and protections. Close exactly these four blockers:

1. Current-risk exact-set closure
   - Build expected high, medium, low-cluster, and resolved projections from lifecycle + public marker + severity/domain authority.
   - Enforce bidirectional exact-set equality: every eligible authority member is projected once in the correct plane, and no projection ref exists without its authority member.
   - Re-signed mutations moving high→medium, deleting all high current, or deleting all low clusters must fail with stable specific error codes.

2. Center-map exact authority closure
   - Add the exact public D09/D10 hotspot member↔site bindings needed to derive center cells; do not infer member identities from counts.
   - Reconstruct the expected complete center-cell set, enforce exact site_ref, stable-id order, and D09 pattern versus D10 individual classification.
   - Re-signed mutations deleting all cells, changing a site, reordering cells, or changing D09 pattern to individual must fail with stable specific codes.

3. Closure bidirectional integrity
   - Bind closure prior_risk_instance_ref to the corresponding public R2 handoff/instance.
   - Verify closure decision, receipt/source pairs, visibility, and content hashes in both directions; no orphan closure and no resolved lifecycle without exactly one valid closure.
   - Re-signed fake prior instance and changed closure_decision_hash must fail with stable specific codes.

4. Executable accept challenge oracle
   - Replace label-only assertions for R5S3C-025..044 and R5S3C-053 with actual projection/hash production and exact output comparison.
   - Every accept case must execute a real projector/oracle path, compare canonical projection and required hashes, and fail if the projector is stubbed or the expected projection label is changed.

Add focused negative and mutation tests for every attack above. Preserve all prior 60 distinct non-no-op challenge locators and all earlier coordinated re-sign attack tests.

Run: generator --check; normal and O2 verifier with byte-identical result; focused test file; full R5 tests; R4 readonly gate; Ruff F; compileall normal/O2; read-only 8911 listener check. Do not start services, modify R4/frontend/medical-writing/real data, or create an acceptance digest. Return a compact evidence handoff with exact SHAs and residual scope.
