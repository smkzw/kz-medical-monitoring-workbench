Continue the SAME session. Independent reviewer returned `REVISE_R5_S3_CONTRACT`; repair the existing v0.2 contract artifacts only. Do not implement runtime and do not broaden write paths.

Writable paths remain exactly:

- `reviews/medical_monitoring_r5_s3_implementation_contract_v0_2_20260818.md`
- `artifacts/medical_monitoring_r5_s3_contract_v0_2/**`
- `tools/generate_medical_monitoring_r5_s3_contract_v0_2.py`
- `tools/verify_medical_monitoring_r5_s3_contract_v0_2.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_s3_contract_artifacts.py`

Do not edit runner report, task context/review/metrics, R4/R5 runtime, frontend, medical writing or real-project files. Do not start 8911/browser/service.

Close every blocker below with executable machine semantics, not descriptive strings:

1. **60 real challenge nodeids.** Every challenge row must point to a real, unique pytest nodeid collected from `test_s3_contract_artifacts.py`. Implement a parameterized test whose ids are the 60 case IDs; each row must apply its declared mutation to an isolated artifact copy and verify the exact typed error/hash outcome. Verifier must run `pytest --collect-only -q` (or equivalent rigorous AST/param-id resolution) and prove every locator exists; non-existent locator rejects. The challenge test cannot merely invoke a generic verifier against labels—it must execute the row's mutation and exact expected oracle.
2. **Joint re-sign attack.** Convert every layer recipe from prose strings to closed structured fields and validate every source path with the same typed-input denylist/dataclass resolver used for source_matrix. Define closed enums for membership operator, denominator policy, rate policy, measure unit, conservation operator, disabled-path policy. Add a tamper that injects `D10TypedInput.members`, then re-runs generator/rewrites source_pins/manifest; it must still fail because the verifier has hard-coded denylist semantics. The contract must state that final Codex/reviewer acceptance creates an external immutable acceptance digest pinning exact human/generator/verifier/artifact/test SHAs; that digest is NOT generator-owned and later joint re-signing invalidates acceptance. Do not fabricate that acceptance record now.
3. **Current-risk and center authority.** Add exact typed supplemental objects, not a generic marker token:
   - `R5S3RiskLifecycleAuthority`: public marker identity/hash, marker kind d09/d10, receipt hash/ref, visibility id/hash, source pairs, clinical domain (closed eight domains), severity sourced specifically from public `D09R2RiskHandoff.monitoring_priority` or `D10R2RiskHandoff.monitoring_priority`, lifecycle state, R2 handoff id/action, member expansion refs, offline-only flag, canonical hash.
   - lifecycle mapping: create/continue/update/reopen => current; supersede => superseded; propose_close remains current/proposed-close and MUST NOT resolve; resolved requires the closure object below.
   - center cell domain/severity/pattern/individual membership must derive only from this object plus public marker/hotspot projections. Never read typed Member.
4. **Marker-absent/closure.** Add `R5S3ClosureAuthority`: prior public risk identity/hash, prior risk instance ref, closure decision id/hash, receipt hash/ref, visibility id/hash, source pairs, offline-only, canonical hash. `resolved` change requires this object. For initial_current/not_evaluable/not_comparable: if no public/prior risk identity, emit NO `R5ChangeBand` (rather than constructing an invalid mandatory risk_ref). Freeze an exact structured emission table with `emit_when_identity_available` and exact source object fields.
5. **Low clusters in replay.** Move full `low_risk_clusters` into `R5S3AudiencePayload` and thus `audience_replay_content_hash`; remove duplicate root location or make root reference the exact hashed audience object. Cluster ref must equal a fixed prefix plus its canonical content hash, and runtime validator must check it. Add a probe changing cluster member refs/content hash and prove replay hash changes or stale replay rejects.
6. **Exact typed supplementals.** Remove the generic `R5S3SupplementalQuantitativeAuthority.value`. Replace it with exact objects:
   - `R5S3DenominatorAuthority` (kind/state/value/unit/member refs/exclusion refs + receipt/visibility/source bindings/hash),
   - `R5S3LayerMembershipAuthority` (layer, membership_state, member refs, source count value/ref, disabled-state + bindings/hash),
   - `R5S3CutoffAuthority` (nullable cutoff ref + bindings/hash),
   - `R5S3EvaluationLimitAuthority` (closed exact limit refs/values needed by S3 + bindings/hash),
   - `R5S3CoverageAuthority` (closed coverage_state + bindings/hash),
   - `R5S3ChangeCauseMixtureAuthority` (closed cause set + bindings/hash),
   - risk lifecycle and closure objects above.
   Freeze every denominator kind/state/rate state/measure unit leaf and each layer's measure unit. No union-like prose type.
7. **Hash graph must be acyclic.** Remove root `content_hash` or define an acyclic recipe. `packet_integrity_hash` must exclude packet id and every hash field it depends on; public replay hash covers complete audience payload including low clusters; packet id may depend on public replay hash but no reverse edge. Freeze aggregate receipt ref as `receipt_content_hash = canonical_sha256(complete R5AuthorityReceipt)` and validate it; no unexplained `str`/`sha256` receipt refs.
8. **Optimized evidence.** Do not claim `PYTHONOPTIMIZE=2 pytest` as evidence when pytest assertions are disabled. Tests may use normal pytest to launch both normal and optimized verifier subprocesses and compare exact JSON. For optimized-mode logic itself, verifier/generator decision paths use explicit `_require`/exceptions. Human report must state this precisely.

Strengthen verifier and tests so these attacks are independently rejected even after ordinary artifact hashes are recomputed. Keep generator deterministic and `--check` byte-stable. Run normal generator check, normal verifier, optimized verifier, normal pytest contract suite, R5 full normal, R4 readonly gate, Ruff F and normal/optimized compile. Return exact SHAs and truthfully list any remaining gap. Status remains only `R5_S3_CONTRACT_READY_FOR_REVIEW`.

