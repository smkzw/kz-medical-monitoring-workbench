# Worker 01 same-session corrective continuation

Codex reopened `test_slice08d_three_mode_matrix.py`. The 24 green tests do not yet prove the frozen v0.2 §12 independent-oracle contract.

Required corrections, in the same session and same bounded write scope:

1. `expected_from_inputs()` and every `_oracle_*` helper must not call product code under test. Remove product dependencies from expected computation, including `determine_disposition`, `project_risk_change_kind`, `canonical_digest`, `content_digest`, product DTOs, registry reads, and product payload fields. Rebuild canonical JSON/SHA-256/member-set and closed medical change/disposition expectations with local stdlib-only oracle logic from `CellFacts`.
2. Do not set `artifact_verified=True` or `artifact_member_verified=True` and then treat those values as authority. Positive reusable-item assertions must pass through the actual R1/R5/R6 verifier and use its result; negative cases must tamper member bytes/identity/closure rather than only booleans. If a case cannot honestly prove that path, narrow its assertion instead of overstating it.
3. Replace the tautological `set(CASE_KEYS) == set(CASE_KEYS)` with an explicit frozen 20-key expected set/order check.
4. Keep case keys only as pytest fixture selectors; no case key/name/id may enter product or oracle decision branches after `CellFacts` construction.
5. Rerun the focused file and report exact count. Add an explicit test that monkeypatches product digest/disposition/change helpers to fail if the oracle calls them, or an equally decisive static/runtime proof.

Do not edit product code unless a corrected test proves a real defect. Do not touch worker 02/03 files, UI, medical-writing, services, real projects/models, or visual artifacts. Return the full required execution report schema; do not claim final acceptance.
