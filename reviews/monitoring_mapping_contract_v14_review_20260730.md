# Review: monitoring_mapping_contract_v14_20260730

## What was verified

1. No project-specific identifiers (MG-K10, RUX, MY009, EXPDOSE, EXDOSE, ITOSSNUM) appear in production logic or test fixtures.
2. ROLE_CATALOG_V1 backward-compatible alias retained for adjacent scripts.
3. PROMPT_VERSION bump (v13→v14) causes old completed jobs to become stale under the normal job-contract lifecycle (mark_stale + supersede_business_key_except).
4. read_only_domain_context injects deterministic form/page-name fields as read-only context to the AI without allowing output mappings for them.
5. G-CMIP-005 treatment identity: domain name alone is never sufficient; requires same-mapping treatment identity evidence.
6. G-CMIP-006 dose ambiguity: indistinguishable same-domain dose fields or ambiguous roles cannot silently pick planned/actual.
7. G-SCALE-002: numeric scale totals in scale-form context cannot become procedure/record numbers.
8. G-CMIP-007: missing IP change lifecycle fields = capability unavailable, never "no changes occurred."
9. CM preserved as non-IP. All 8 IP action families remain separate.
10. No runtime database access, no port 8911 startup.

## Residual risk

- G-CMIP-005 uses global (mapping-wide) treatment identity evidence, not per-domain. This is intentional (randomization is subject-level), but in unusual designs where different domains test different products, a finer-grained check may be needed.
- G-CMIP-007 fires whenever IP administration fields exist but any of the 4 change families (dose_adjustment, interruption, discontinuation, restart) is absent. Real listings that genuinely lack all change events will show this as a capability limitation, which is the intended conservative behavior.
- G-SCALE-002 is a review warning, not a capability blocker, to avoid false positives on legitimate procedure numbers in scale domains.
