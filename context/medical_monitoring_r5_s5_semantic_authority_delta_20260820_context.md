# R5-S5 semantic authority delta context (2026-08-20)

## Goal and boundary

This append-only delta freezes deterministic semantic authority shapes and adversarial probes without changing the accepted parent, any producer/runtime/S5/UI surface, or port 8911. It does not create clinical authority and does not self-accept.

## External synthetic authority pins

The candidate `SemanticPolicyAcceptanceReceipt` is not authority. It must resolve through exact `registry_id + registry_content_hash + accepted_record_ref + accepted_record_content_hash` to the frozen registry below. A changed package and fully resealed receipt still fail when the frozen record remains unchanged. No status string is consulted.

- acceptance registry: `registry:r5-s5:synthetic-policy-acceptance:20260820`
- acceptance registry SHA-256: `71dc168b99dd1ea2d768284fe69e0c0cdd013b9fa261e85132f0b334cf20e075`
- authority scope: `synthetic_test_only`
- non-clinical: `true`
- `synthetic-accepted:event_classification:848bf06db5a222f9b96c` / accepted-record SHA-256 `c94504de8a27b6b97f01753de355d39a63eb15fb6a2b1b6614f1486fe80705a3` / package SHA-256 `848bf06db5a222f9b96c055ebba7cb898de0d36e43a15340886a51e9bdea76ef`
- `synthetic-accepted:risk_presentation_lexicon:5de62abace5faff39139` / accepted-record SHA-256 `395ac1ea0a4d93bacece9d9674cb4bab78da906d54338144d134097bc0f8b761` / package SHA-256 `5de62abace5faff39139486c1ec04df710fb327816f2fdff0d2cff6c3d495b32`
- `synthetic-accepted:risk_taxonomy:0f191fd24f11a1206750` / accepted-record SHA-256 `c3361dfb953c4888dd98fd4bfd3993b555b704c40967b39e474d6046df292786` / package SHA-256 `0f191fd24f11a120675052f8c5337ceb4fca808ecf89aaae0edcdeb0f4a6d268`
- `synthetic-accepted:severity_policy:cfb1d1ef2ad6f0450d9a` / accepted-record SHA-256 `12ef9d526904d9bcc954c424c6f2a4dcbc93b8b4c03a84b20f8d5acb8fb2af4c` / package SHA-256 `cfb1d1ef2ad6f0450d9a9ad1a182c755e366f9ae8d405aed510dfcbcab6d70e1`

The typed source registry is independently pinned as `registry:r5-s5:synthetic-typed-source-records:20260820` / `28d536579be39b80bdb3dc1033845cae0eea27d362eef1375ac66eb3a34c5939`. Every raw token or flag evidence object resolves to an exact typed record, owner, record content hash, field, value, source revision, locator and eight-field identity join. Candidate evidence resealing cannot change that record.

## Exact contracts

- S4 join is exactly eight keys: `project_ref, run_ref, snapshot_ref, cutoff_ref, site_ref, subject_ref, risk_ref, spine_ref`. Event, visit, source and join hash fields are forbidden.
- event relation is exactly 16 subtypes to 8 domains; every successful event classification has exactly one nonempty match.
- matching policy is only `exact_utf8_v1`; trim, casefold, fuzzy and fallback are forbidden.
- severity is exactly `critical, high, medium, low`; legacy severe/moderate/mild map to high/medium/low.
- SAE/AESI inputs use the real typed path `mm_r2.risk.RiskInstance.clinical_risk_flags` and never promote severity.
- package, rule, receipt, authority, API success/error and every nested object use exact key sets and content hashes.

## Challenge and done evidence

There are 66 active one-mutation cases. The verifier applies mutations mechanically, validates global packages and external registries, then evaluates semantics without importing the generator and without branching on case id, expected code or expected label. Codex remains the acceptance authority; this worker returns evidence only.
