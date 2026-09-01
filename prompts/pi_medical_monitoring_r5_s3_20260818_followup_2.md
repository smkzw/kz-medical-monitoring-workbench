Continue the current NIGHT session and repair only the existing R5-S3 v0.2 contract artifacts/tests. Runtime remains forbidden. Writable paths are unchanged from the prior pass.

Independent review found four remaining P1 classes. Close them with exact executable gates:

1. **Hard-pin all semantic recipes, not only typed-input source_count paths.** In verifier code (outside artifact-owned data), define exact immutable expected structures and require byte/structure equality for:
   - root hash DAG, every algorithm (`sha256` only), canonicalization (`utf8_nfc_sorted_keys_compact_json_newline`), excluded fields and dependency edges;
   - receipt-content hash recipe = canonical SHA-256 of the complete `R5AuthorityReceipt`, with exact prefix/ref rule;
   - packet-id constraint exactly single-colon `r5-s3-contract:<audience_replay_content_hash>`;
   - all `sourced_from` paths for clinical domain, severity, lifecycle/current state, center domain/severity and member expansion.
   Parse every `sourced_from`/source path anywhere in overlay/schema/recipes through the hard-coded allowlist/typed-input denylist. A re-signed change to typed `Member.domain` or `Member.monitoring_priority` must fail. A self-edge in audience replay hash, sha1 receipt recipe, or double-colon packet-id descriptor must fail even after generator/source-pins/manifest are re-signed. Add explicit joint-re-sign probes for all four.

2. **Packet oracle must validate actual authority relations.** Strengthen the sample packet and `_packet_oracle` (or equivalent) to mechanically verify:
   - high/medium/current refs have only `d09_marker:`/`d10_marker:` prefixes and resolve exactly one `R5S3RiskLifecycleAuthority` plus the corresponding public marker;
   - low cluster refs resolve their canonical cluster and every member/risk ref resolves a low/current lifecycle authority;
   - resolved refs resolve a resolved lifecycle plus exact `R5S3ClosureAuthority`; current/proposed_close and resolved planes are disjoint;
   - lifecycle marker id/hash/kind and member expansion equal the authority unit's public `D09/D10RiskMarker` values;
   - lifecycle severity exactly equals the corresponding public `D09R2RiskHandoff.monitoring_priority` or `D10R2RiskHandoff.monitoring_priority` (critical/unknown/unmapped fail closed);
   - lifecycle R2 handoff id/action and lifecycle mapping match the public handoff;
   - lifecycle clinical domain equals a separate exact `R5S3ClinicalDomainAuthority` bound to receipt/visibility/source pairs/content hash and referenced by the authority unit; never read typed input/Member;
   - center cell domain/severity/pattern/individual refs equal the resolved lifecycle/public marker/hotspot authority; single individual never becomes pattern.
   Add direct re-signed packet attacks: raw member in high refs, lifecycle domain drift, severity drift without public handoff change, action drift, member expansion drift, current/resolved overlap. Each must return an exact error code. Existing closure-missing and low-cluster-stale-replay attacks must remain.

3. **Remove all no-op challenge rows.** R5S3C-026..033 and 057..060 currently set fields to existing values. Replace every one with a mutation that actually changes canonical input/state. Valid/accept cases must build a genuinely different valid variant (for example hidden-only private mutation with unchanged replay, unit-order permutation canonicalized to same replay, zero-count projectable membership with different valid member set, or another exact accepted variant) and assert the declared hash relation/projection. Reject cases must change one leaf and assert exact error. Parameterized test must assert:
   - pre/post canonical bytes differ for every mutation;
   - exact `error_code` or accepted typed outcome;
   - exact `expected_projection` (`emitted`, `not_emitted`, `unchanged`, as appropriate);
   - exact public/private hash relation from the row;
   - `error_marker` when declared.
   Do not generate all packet_assert failures with `expected_projection=emitted`. Challenge rows must be 60 real independent executable oracles, not labels.

4. **Packet-id descriptor consistency.** Machine schema, human contract, generator, verifier and packet oracle must all use exactly `r5-s3-contract:<hash>` (single colon). Hard-code and test the full descriptor and output.

Also add the separate `R5S3ClinicalDomainAuthority` exact object to schema/overlay/source matrix and update supplemental-object counts, source pins, manifest, human contract and tests. It is synthetic/offline authority only, bound to receipt/visibility/source pairs/canonical hash; it exists because D09/D10 public projection lacks clinical domain, and it must not be misrepresented as public R4.

Run: generator write then repeated `--check`; normal and `PYTHONOPTIMIZE=2` verifier; collect-only exact nodeids; normal pytest contract suite; R5 full normal; R4 readonly gate; Ruff F; normal/optimized compile; 8911 stopped check. Report final SHAs and any residual gap. Status remains only `R5_S3_CONTRACT_READY_FOR_REVIEW`.

