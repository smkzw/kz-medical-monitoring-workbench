You are continuing the same fallback Batch A repair session for the second and final same-session follow-up. Codex independently confirmed that your six original VETO reproductions now fail closed, but adjacent source review and executable attacks found five same-root fail-open contracts. Repair them without reopening Batch B/C.

Hard boundaries:
- Modify only Batch A files under `poc/medical_monitoring_ai_native_r2/`.
- Preserve every prior report and VETO record as immutable history.
- Runner-managed output path: `runs/execution/medical_monitoring_r2_kernel_execution_20260810/worker_01_fallback_repair_followup_02.md`. Do not write this report yourself; return it in the final response.
- Do not edit R1, product, medical-writing, real-project, shared-runtime or 8911 surfaces.
- Python 3.9 stdlib + existing pytest only; no package/service/network/credential/real data.
- This is the final repair pass for this fallback session. Make a coherent trust-boundary fix, not test-specific patches.

Read these files only:
- current Batch A source files under `poc/medical_monitoring_ai_native_r2/src/mm_r2/`
- current Batch A tests under `poc/medical_monitoring_ai_native_r2/tests/`
- `poc/medical_monitoring_ai_native_r2/README.md`
- `reviews/codex_medical_monitoring_r2_batch_a_postfallback_adjacent_gate_20260810.md`
- `reviews/codex_medical_monitoring_r2_batch_a_postfallback_negative_gate_20260810.md`
- `context/medical_monitoring_r2_kernel_execution_20260810_execution_context.md`

The original six are closed. Keep those regressions green. Fix these additional executed failures:

1. `ImmutableDict` now wraps a normal dict in public/reachable attribute `_d`. `frozen["outer"]._d["x"] = 2` succeeds and changes the content hash. The frozen representation must not expose any mutable backing object through ordinary attribute access. Use a `MappingProxyType`, an immutable tuple/index design, or an equivalently non-mutable backing. Add both outer and nested `_d`/backing access regressions and confirm caller input mutation is inert.

2. `SnapshotBinding` accepts zero mapping definitions/results and `identity_resolution=None`; `identity_clean` returns True. A trusted local user can issue booleans and reach `baseline_eligible` without any mapping review or identity review. A baseline-eligible binding must require at least one consistent mapping definition/result and an explicit `IdentityResolution` bound to the same algorithm. Missing mapping set or missing identity review must fail closed (at construction or gates); zero-row snapshots may still use an explicit empty-but-clean IdentityResolution. Do not let local-user authority waive required mapping/identity evidence.

3. `IdentityResolution` and `AmbiguousIdentity` are only shallow frozen. Passing a list for `ambiguities` allows appending after construction and flips `is_clean`; candidate digest collections can also drift. Defensively copy/canonicalize tuples, validate resolved identities/ambiguities against the resolution algorithm and project consistency, canonicalize candidate digests (including uniqueness/order and digest shape where they are named digests), and audit other identity collection fields for the same issue.

4. `SnapshotBinding.fingerprint` includes only mapping IDs (`result_by_mapping.keys()`), not full mapping definition/result semantics or identity-resolution contents. Two bindings with the same IDs but different `source_field`/`canonical_field` produce the same fingerprint. Bind the canonical immutable contents of every mapping definition and result, plus the identity-resolution outcome, not merely IDs/clean booleans. A caller-supplied nonempty fingerprint must be validated against the recomputed value rather than silently overwritten. Add semantic-collision regressions for field, confidence, ambiguity, record count and identity resolution changes.

5. `SourceRevision._rehydrate_verified(...)` and `ListingSnapshot._rehydrate_verified(...)` remain directly callable and accept arbitrary valid-looking digests without any verifier/capability. Batch C does not yet provide artifact verification, so Batch A must expose no callable digest-only trust escalator. Remove these methods now, or make them fail closed without a non-public verification capability that only a future artifact verifier can issue. Prefer removing the insecure hook and documenting that Batch C must add a verified rehydration adapter after actual bytes/hash verification. Replace current positive internal-rehydration tests with negative “no current digest-only rehydration” contracts.

Adjacent audit while touching the same contracts:
- Ensure unauthorized `reject(...)` attempts after registration append an audit record without changing state, matching the stated post-registration audit guarantee.
- Ensure `SnapshotBinding` collections are defensively copied and cannot change after fingerprint computation.
- Keep direct `_verified=True`, public `from_dictable`, direct `AcceptanceEvidence`, substituted mapping and actor/evidence mismatch paths fail-closed.

Required verification:
- All five exact new attacks fail closed.
- The original six attacks remain fail closed.
- A real binding with >=1 mapping result and explicit clean IdentityResolution still walks the full chain for both allowed actors under their existing deterministic rules.
- Missing/ambiguous identity and missing/ambiguous/low-confidence critical mapping cases block at the correct step.
- Fingerprint differs for all material mapping/result/identity-resolution semantic changes.
- Unauthorized advance and reject attempts are audited with state unchanged.
- Focused tests, full Batch A/all R2 tests and compile pass; report counts.
- Record stable target SHA, R1 tree digest by the established Codex method, and 8911 absent.

Return exact changed paths, API contract changes, negative reproduction results, commands/counts, and residual limitations. Do not claim Batch A acceptance.
