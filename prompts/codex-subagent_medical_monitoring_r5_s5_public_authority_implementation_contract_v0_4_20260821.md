You are a Codex native subAgent under a parent Codex task. Use `gpt-5.6-sol` with reasoning effort `high`. Work directly in the current medical-workbench workspace.

Hard boundaries:

- The exact nine-file write boundary is listed below; every other workspace path is read-only.
- Runner-managed output path: `runs/codex-subagent_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_20260821.md`. Do not write that report path with tools; return the complete handoff and let the runner persist it.
- Do not start services, browser, real projects, models, or port 8911. Do not self-accept.

Read these files only, completely before editing:

- latest applicable `AGENTS.md` and `/Users/smkzw/.codex/skills/clinical-research/mw-workbench-wave-audit/SKILL.md`;
- System Design v1.1, R0-R8 implementation plan, current R5-S5 context/plan;
- accepted public-authority parent contract, artifacts, tools and acceptance record;
- accepted semantic-authority delta v0.1 artifacts/tools/acceptance record;
- accepted temporal-projection-authority delta v0.1 artifacts/tools/acceptance record;
- accepted temporal-projection-authority delta v0.2 nine files and acceptance record;
- rejected implementation-contract v0.1/v0.2/v0.3 nine-file snapshots, rejection records and reviewer findings, only as immutable negative evidence;
- parent 236 challenge registry, parent validators, and every pinned R1/R2/R4/R5 typed source required by accepted temporal v0.2.

## Exact write boundary

Create or modify only these nine new v0.4 files:

1. `context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_20260821_context.md`
2. `reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_20260821.md`
3. `artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/public_api.json`
4. `artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/source_join_matrix.json`
5. `artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/invariant_error_matrix.json`
6. `artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/test_matrix.json`
7. `artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/manifest.json`
8. `tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4.py`
9. `tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4.py`

Everything else is read-only. Do not create producer/runtime/tests/evidence/acceptance files, edit root init, accepted or rejected snapshots, frontend/services/packages/deploy, medical-writing or real-project files. Do not start 8911, services, browser, real projects or models. Do not self-accept. The nine files must contain no acceptance token or acceptance record; manifest status is exactly `candidate_unaccepted`.

## Objective and authority chain

Create one immutable, exact, contract-spec-only implementation contract v0.4 for `subject-temporal-public-v1` and `aemh-match-history-public-v1`.

The only active authority chain is:

`accepted public parent v0.1 → accepted semantic delta v0.1 → accepted temporal v0.1 primitives → accepted temporal v0.2 full_parent_graph`.

v0.1-v0.3 implementation contracts are negative history only. Do not copy their mirrors, aliases, expected planes, local authority records or acceptance implications. v0.4 must project the already accepted v0.2 full-parent-graph execution closure into a future producer contract. It must not claim that the absent producer or its tests have run.

Pin, verify and preserve the exact accepted manifests and records:

- parent manifest `92bbf2d7fe4cd591949982a3d29666a8b6090aab645679dbff997630a3702270`, record `23fed5b186057a79cd0ec43a7718e43934ebafdc8f62fd251077d4fb6891639d`;
- semantic manifest `66605a46c10e2aa4d36b06e566158666a08cdc92ec0e630364aad5b9ffb2385d`, record `bf50156fa82d825309fce72115ddf971fc4e0bdbd60936ea45e2362a6aa3eb4c`;
- temporal v0.1 manifest `e606e517c07dcb499657b418dbd16e4dacd98c7e7010770845dbccb91af59f97`, record `523351f1b5536b12c1a5be9251ad01f4e8b7a70f5088073a2333aefc241d1b79`;
- temporal v0.2 manifest `466b0ae605b83a57f0e184446db311beb05ff5e4e1998a7dc5be9bb44d2b7de8`, record `d08b4ed27f9829db4cdcab0837f3623c244ee8c888cce699c55580621bd68ef4`.

Also freeze and actively verify temporal v0.2's 15 typed-source pins, its parent/semantic/nine-file pins, exact rejected v0.1/v0.2/v0.3 nine-file SHA maps and existing rejection records, root `mm_r5/__init__.py`, S4/exact-contract/readonly-evidence pins, and the medical-writing protected inventory count 542 / aggregate `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`. Duplicate pin surfaces must be exact-equal or removed; fully resealed drift at either surface must fail.

## `public_api.json`

Freeze future Python >=3.9 modules:

- `mm_r5.public_authority_common`
- `mm_r5.subject_temporal_public`
- `mm_r5.aemh_match_history_public`

Freeze exact signatures:

```python
canonical_json_bytes(value: object) -> bytes
canonical_sha256(value: object) -> str
validation_result(issues: Iterable[PublicAuthorityValidationIssue]) -> PublicAuthorityValidationResult

build_subject_temporal_authority(source: SubjectTemporalSourceBundle) -> SubjectTemporalAuthorityPacket
validate_subject_temporal_authority(candidate: SubjectTemporalAuthorityPacket, source: SubjectTemporalSourceBundle) -> PublicAuthorityValidationResult

build_aemh_match_history_authority(source: AEMHMatchHistorySourceBundle, previous_packet: Optional[AEMHMatchHistoryAuthorityPacket] = None) -> AEMHMatchHistoryAuthorityPacket
validate_aemh_match_history_authority(candidate: AEMHMatchHistoryAuthorityPacket, source: AEMHMatchHistorySourceBundle, previous_packet: Optional[AEMHMatchHistoryAuthorityPacket] = None) -> PublicAuthorityValidationResult
```

All source/output/result classes are exact `@dataclass(frozen=True)`. No `Any`, free `Mapping`, mutable list/dict fields, reflection or dynamic attributes. Rebuild the exact parent Subject 17-object and AEMH 13-object schemas, field order, types, nullability and cardinality from accepted parent sources; no extra serialization leaves.

Each source bundle contains the real pinned typed R1/R2/R4/R5 inputs and exactly one accepted v0.2 `temporal_authority: AuthorityBundleV02`, whose source variant is exact `SubjectFullGraphInputV02` or `AEMHFullGraphInputV02`. Recursively enforce exact keys/types/hashes and:

- `authority_scope == synthetic_test_only`
- `execution_profile == full_parent_graph`
- exact target contract
- `temporal_v01_manifest_sha256 == e606...`
- accepted v0.2 manifest and bundle identities.

Accepted manifest/record refs are module-internal pins, never runtime caller inputs. Dual real-typed-source and v0.2 authority values must cross-check; neither side may override the other. Candidate output may never backfill source authority.

Freeze exact issue/result classes:

```python
PublicAuthorityValidationIssue(code: str, path: str, message: str,
  origin: Literal["parent", "semantic_delta", "temporal_delta", "consumer"], priority: int)
PublicAuthorityValidationResult(ok: bool, primary_code: Optional[str],
  issues: tuple[PublicAuthorityValidationIssue, ...], packet_emitted: bool)
```

Success is exactly `True/None/()/True`; failure is `False/issues[0].code/nonempty tuple/False`. Builders return a packet only at zero issues; otherwise raise the single frozen `PublicAuthorityConstructionError(result)` with no partial packet.

## `source_join_matrix.json`

Freeze exactly 272 unique rows: Subject 156, AEMH 116, unique qualified leaf and final JSON pointer, aliases=0, unexplained=0. Every row contains at least:

`ordinal, contract, object_type, leaf, qualified_leaf, output_json_pointer, output_type, nullable, cardinality, ordering_rule, key_selector, authority_source_kind, typed_source_selector, v02_authority_selector, selector_cardinality, selector_zero_policy, selector_many_policy, reducer_id, recipe_id, recipe_content_hash, recipe_node_id, recipe_node_output_ref, recipe_output_json_pointer, recipe_registry_content_hash, dependency_output_leaves, dependency_recipe_nodes, construction_phase, parent_schema_ref, semantic_ref, expected_plane_ref, fail_closed_codes, candidate_backfill_forbidden, mirror_forbidden`.

Requirements:

- typed selectors resolve to concrete reachable fields in the 15 pinned Python typed surfaces;
- v0.2 selectors resolve to exact accepted `AuthorityBundleV02.source/...` schema pointers;
- exact-one/zero-or-one/ordered-many selection and fail-closed cardinality are executable;
- reducers use only accepted temporal v0.2 closed operations, never prose/Python/lambda/new formulas;
- recipe/node/output refs point to the accepted v0.2 16 recipes/32 real node outputs;
- the subject and AEMH DAGs independently resolve, are acyclic, have no self/future edge, and only use topologically earlier outputs;
- expected plane references only accepted v0.2 full-graph/trace baseline or post-graph identities;
- hashes, membership, projection, receipt and packet leaves derive from real recipe-node output, never final-target mirror or candidate backfill.

Delete v0.3 `target_output_path`, candidate/example/fixture output mirrors, prose resolvers, class-wide closure, nearest fallback, temporal constant override, D07 OTHER and S4 value transfer.

## `invariant_error_matrix.json`

Rebuild error authority from accepted parent/semantic/temporal registries, not rejected implementation files. Freeze parent 81, semantic 49, temporal v0.1 62, union 192 with exact code, integer priority, origin, contract, invariant, path and message semantics. Temporal v0.2 contract-closure failures remain STOP conditions, not new public errors.

Deduplicate by `(code, path, origin, message)` and total-order by `(priority, path, code, origin, message)`. `primary_code` is the first ordered issue. Any issue means no packet. All 226 reject specs must compare the complete ordered issue sequence, not only primary or a set.

## `test_matrix.json`

Separate current contract verification from future producer acceptance.

Current executable inventory is exactly:

- 236 distinct runtime specifications / 236 trace realizations / 0 aliases;
- Subject 143, AEMH 93;
- 10 accepts: R5C-109, 110, 116, 157-163;
- 226 rejects;
- 22 separate artifact-governance probes executed now.

Each identity is independently recomputed from real pre-input identity, exact instance selector, primary mutation, actual linked operations, lane and reseal mode/order. Exclude case ID, label, fixture name, sentinel, expected code/output, observed result/hash.

All 236 are actually executed by generator and independent verifier. Do not store an unexecuted label ledger.

For 10 accepts, consume accepted v0.2 exact trace operation records, build complete post graphs through the accepted 16-recipe DAG, call parent validators, and compare exact packet/projection hashes. Operation completeness must match accepted v0.2: a linked list may be empty only when structural pre/post diff is exactly the primary single operation; multi-operation transforms must list every linked path/op/pre/post.

For 226 rejects:

1. build a valid complete baseline from accepted typed input and the 16-recipe DAG;
2. apply the trace's exact primary and linked operations;
3. reseal in its exact mode/order;
4. call accepted parent validator;
5. compare the full nonempty ordered issues;
6. freeze the future public validator expectation to the same order and `packet_emitted=false`.

Never prebuild invalid output fixtures, select by case ID, or feed expected errors/observed values into the validator.

Future producer execution is false at this stage. Freeze but do not create or run the exact 11-file create-only producer allowlist used by v0.3. Freeze machine-executable future AST, sensitivity and `python3 -I -B` isolation specs, but report producer/runtime tests, AST, sensitivity, isolation and evidence as not executed while the files are absent.

## `manifest.json`

Freeze exact nine paths/raw SHA pins, all accepted/rejected/typed/protected pins, v0.2 schema/recipe/full-graph/trace content identities, exact counts, and these booleans:

- `spec_count=236`, `unique_trace_count=236`, `alias_count=0`
- `positive_count=10`, `reject_count=226`
- `leaf_count=272`, `recipe_count=16`, `recipe_node_count=32`
- `producer_executed=false`, `runtime_tests_executed=false`, `evidence_created=false`
- `contract_spec_only=true`, `non_clinical=true`, `authority_scope=synthetic_test_only`
- `status=candidate_unaccepted`, `port_8911_must_be_stopped=true`

`acceptance_token` is a forbidden key.

## Independent verifier and active attacks

The v0.4 verifier must not import the v0.4 generator or share its expected registry/helpers. Independently parse accepted sources, validate exact schemas, execute accepted v0.2 closed op handlers and DAG, construct complete graphs, call parent validators, execute all 236 transformations, compare 10 post graphs, 226 full ordered error sequences, 272 join results, and 236 unique identities.

Add active fully resealed attacks for at least:

- accepted/rejected/typed/root/S4/542 pin drift and duplicate pin disagreement;
- extra/missing/wrong authority keys/types/contract/schema/scope/profile/target/source variant and v0.1 pin;
- candidate/parent/expected packet, mirror/backfill, case/label/sentinel/expected-output self-authorization;
- selector zero/many/cross-scope, wrong key, same-type swap and join reflection;
- recipe arbitrary params, unknown or swapped op, phase/op mismatch, input/output drift, missing/extra/reordered node, cross-target edge and cycle; attack the interpreter directly, not only an outer structural gate;
- missing/fake/hidden linked operation, wrong pre/post/path/order/reseal;
- 272 duplicate/missing/nominal leaf, self/future dependency and candidate source;
- error priority/order/primary/packet-emitted drift;
- false claim that absent producer/tests/evidence ran.

AST-check generator/verifier for mutual imports, assert-only gates, case/sentinel branches and shared oracle. Future producer gate specs must forbid dynamic code/reflection, file/network/subprocess side effects, and require real candidate/source/previous sensitivity vectors, but must remain explicitly unexecuted.

## Verification and STOP

Run generator `--check` and verifier under normal, `-O`, `-OO`, `PYTHONHASHSEED=0,1,777`; generate twice in independent temporary directories and require byte equality; run exact offline Ruff on the two v0.4 tools; verify all pins, 542 aggregate, exact nine/5-artifact sets, future 11-file producer/S5/bytecode/cache absence and 8911 stopped. Use no assert-only gate.

STOP and report exact evidence without creating a fourth authority layer if any P0-P4 condition holds: accepted pin drift; rejected snapshot used as authority; 2/2 baseline, 10/10 positives, 236/236/0, 226 nonempty ordered rejects, 272 bijection or 16/32 recipe closure fails; API/schema/selectors/DAG/prefix contracts cannot be expressed; generator/verifier share oracle; optimization/seed/double-generation/Ruff drifts; nine-path boundary, 542/root/S4/typed protection, absence or 8911 fails.

Only a later fresh isolated reviewer may return `ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_V0_4` against one immutable manifest SHA. That accepts only this implementation contract and unlocks the exact 11-file producer implementation create-only stage. It does not accept producer/tests/evidence, S5/runtime, UI/browser, real project/model, clinical authority, product/production, medical-writing or 8911.

Return a compact handoff with files, counts, exact authority/recipe consumption evidence, 236/226/10 and 272 join execution evidence, active attacks, normal/O/O2/hashseed/double-generation/Ruff/pin/absence/8911 results, final nine SHA values, residual uncertainty and next action. Do not self-accept.
