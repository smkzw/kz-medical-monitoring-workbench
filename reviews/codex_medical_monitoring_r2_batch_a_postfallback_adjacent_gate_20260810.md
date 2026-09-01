# R2 Batch A post-fallback adjacent gate — VETO 2

Date: 2026-08-10
Scope: current Batch A implementation after `worker_01_fallback_repair_followup_01`
Decision: **VETO**; original six failures are closed, but five same-root failures remain.

## Closed original attacks

Codex independently re-ran the original six cases. Base-dict mutation, reachable config assignment, `_verified=True`, generic codec forgery, direct AcceptanceEvidence and substituted high-confidence mapping all failed closed.

## New executed failures

```text
reachable_private_backing_dict=FAIL_OPEN:True
empty_mapping_no_identity_reaches_eligible=FAIL_OPEN:True
identity_resolution_input_mutation=FAIL_OPEN:(True, False, 'list')
mapping_semantics_fingerprint_collision=FAIL_OPEN:True
direct_underscored_rehydration=FAIL_OPEN:'aaaaaaaa...'
```

Interpretation:

1. `ImmutableDict._d` is an ordinary reachable mutable dict, so the deep-immutability claim is still false.
2. A local-user path can reach `baseline_eligible` without mapping definitions/results or explicit identity resolution.
3. Identity-resolution lists remain mutable after frozen dataclass construction and can change `is_clean`.
4. The binding fingerprint does not bind material mapping semantics.
5. The current underscored rehydrators are callable digest-only authority shortcuts before Batch C verification exists.

## Required disposition

- Repair all five in the same fallback session's second/final targeted pass.
- Preserve the six already-closed regressions.
- Require explicit mapping and identity-review evidence for every actor.
- Remove any current callable digest-only rehydration path until real artifact verification exists.
- After Codex negative/full regression gates pass, use a fresh independent stable-snapshot reviewer.

This record is immutable history, not an implementation report.
