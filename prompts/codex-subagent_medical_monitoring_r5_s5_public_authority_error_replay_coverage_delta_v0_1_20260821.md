You are a Codex native subAgent under a parent Codex task. Use `gpt-5.6-sol` with reasoning effort `high`. Work in the current medical-workbench workspace.

Hard boundaries:

- Only the exact nine create-only paths below are writable. Everything else is read-only.
- Runner-managed output path: `runs/codex-subagent_medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1_20260821.md`. Do not write it with tools.
- Do not modify the blocked implementation-contract v0.4 snapshot, accepted authority bytes, producer/runtime/tests/evidence/root init/frontend/medical-writing/real projects.
- Do not start 8911, services, browser, real projects or models. Do not self-accept.

Read these files only, fully before editing:

- latest `AGENTS.md` and `/Users/smkzw/.codex/skills/clinical-research/mw-workbench-wave-audit/SKILL.md`;
- System Design v1.1, R0-R8 plan and current R5-S5 context;
- accepted public parent, semantic v0.1, temporal v0.1 and temporal v0.2 artifacts/tools/acceptance records;
- parent and semantic challenge registries, schemas, validators and verifier entrypoints;
- the blocked implementation-contract v0.4 nine files as immutable negative evidence;
- all typed-source/protection surfaces pinned by temporal v0.2.

## Exact nine-file allowlist

Create only:

1. `context/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1_20260821_context.md`
2. `reviews/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1_20260821.md`
3. `artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/schema.json`
4. `artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/base_input_registry.json`
5. `artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/gate_registry.json`
6. `artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/challenge_registry.json`
7. `artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/manifest.json`
8. `tools/generate_medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1.py`
9. `tools/verify_medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1.py`

## Objective and truth boundary

Create one append-only, synthetic-test-only replay coverage delta for exactly 22 existing public error codes that accepted challenge execution does not currently emit. Add no error code, rename, priority, invariant, clinical rule, fallback or production behavior. Parent/semantic/temporal bytes remain immutable.

The independent verifier must first actually execute existing accepted challenge entrypoints and prove the pre-delta emitted union is exactly 170/192 and the missing set is exactly the 22 codes below. The delta then supplies one executable replay gate per missing code; union must be exactly 192. Never fill expected errors without invoking a real parser/validator/constructor/governance gate.

Pin accepted parent/semantic/temporal v0.1/v0.2 manifests and acceptance records, temporal v0.2 15 typed sources and nine files, root/S4/exact-contract/readonly evidence, 542 aggregate, rejected v0.1-v0.3 histories, and the blocked v0.4 nine-file SHA map:

```text
dd6c803175a37bb8ee573c7d13f5b213b51734fd0470bd7deb988050b756bf65 context
3928e8069ef68e0dc19f2ada18b5fa24943e795c170362a095975cfe67fc384e review
d27523ec4a85218136f2640160a99ef85b9418a9224fdf24f290fac2fecc7d18 public_api
ea825e18733611a69c354a93d555a555a76fa0b35df914bb1915c526cab0de59 source_join
83064fbc0935b59510cc2fd463b7946165d86bec315b67ca3eda624efe1ed0d9 invariant_error
86061b6609a75d2b576d76c6b8b8bf13324322d396e79facb66dd09c22b63e46 test_matrix
c363811be037a107a369523c47f43a7e589ddc9f8e608ca87309e1f15b6f7a94 manifest
be0fa7f6aa8c91767c35d2842116bd7c36cca1f19eb58ef01ae592f339129a6b generator
a4df9626112e3fa5ee45d0ad538a298b29dab98cf122e912211cbe21d307a2fe verifier
```

The delta verifier must independently recompute the blocked v0.4 `170/192` STOP; do not trust a manifest count.

## Artifact contracts

`base_input_registry.json` stores only accepted-source paths/pointers, raw/canonical identities and constructor recipes. It must not store packet/output/issue mirrors. Parent bases come from accepted temporal v0.2 Subject and AEMH authority inputs and are built by the real 16-recipe/32-node constructor. Semantic bases come from accepted semantic baselines/manifest.

`gate_registry.json` freezes exact gates with:

`gate_id, entrypoint_class, accepted_source_path, accepted_source_raw_sha256, accepted_ast_selector, accepted_ast_normalized_sha256, input_type, output_type, permitted_error_codes, algorithm_contract, constructor_precondition, mutation_phase, reseal_handler, issue_order_source, side_effect_boundary`.

Entrypoint classes:

- `untrusted_schema_parser`: real exact-key/type parser; malformed values must not be normalized through dataclass construction first.
- `typed_validator`: real parent/semantic validators plus two append-only narrowed replay gates below.
- `constructor_candidate_comparison`: real accepted constructor produces actual; candidate comparison cannot derive expected from candidate.
- `artifact_governance`: actual isolated filesystem/manifest gate, not declaration comparison.

The two append-only gates may only expose already accepted invariants/codes:

- `identity_dimension_replay_gate`: compare receipt/projection/visibility/member identity along project/run/snapshot/site/spine dimensions and emit only the existing matching code.
- `aemh_history_preservation_replay_gate`: require existing withdrawn/reappeared entries to remain a byte-identical ordered subsequence of the same stable thread; emit only `AEMH_WITHDRAW_REAPPEAR_HISTORY_LOSS`.

Generator and verifier implement these independently from accepted schema/invariant fields and priority arrays. They must not share helper code or use case/error identifiers to choose behavior.

`challenge_registry.json` has exactly 22 exact-key rows:

`case_id, surface, error_code, accepted_priority, entrypoint_class, gate_id, base_input_ref, base_input_content_identity, constructor_id, instance_selector, single_mutation, ordered_reseal, observed_ordered_issues, forbidden_output, trace_identity`.

Constraints:

- 22 distinct existing codes, 22 unique trace identities, aliases=0;
- one primary mutation per row; reseal may only update dependent hashes/derived fields;
- identity includes base identity, gate, selector, mutation, reseal and excludes case ID, error code, observed issues and labels;
- observed issues are author observations, never verifier oracle;
- verifier recomputes priority/order from accepted arrays.

Exact missing codes and accepted priorities:

```text
1 PUB_SCHEMA_EXACT_KEYS
2 PUB_TYPE_BOOL_REQUIRED
3 PUB_TYPE_MISMATCH
7 PUB_IDENTITY_PROJECT_MISMATCH
8 PUB_IDENTITY_RUN_MISMATCH
9 PUB_IDENTITY_SNAPSHOT_MISMATCH
11 PUB_IDENTITY_SITE_MISMATCH
13 PUB_IDENTITY_SPINE_MISMATCH
17 PUB_VISIBILITY_DEEP_LINK_INELIGIBLE
53 PUB_RUNTIME_TEST_SURFACE_FORBIDDEN
71 AEMH_WITHDRAW_REAPPEAR_HISTORY_LOSS
83 SEM_TYPE_MISMATCH
95 SEM_RISK_TAXONOMY_INCOMPLETE
96 SEM_RISK_TAXONOMY_AMBIGUOUS
104 SEM_SEVERITY_RULESET_INCOMPLETE
108 SEM_SOURCE_RECORD_UNRESOLVED
116 SEM_RECEIPT_HASH_MISMATCH
119 SEM_ACCEPTED_RECORD_HASH_MISMATCH
120 SEM_RECEIPT_PACKAGE_KIND_MISMATCH
128 SEM_AUTHORITY_HASH_MISMATCH
129 SEM_AUTHORITY_MISMATCH
130 SEM_MANIFEST_HASH_MISMATCH
```

## Exact challenge semantics

Use these real bases/mutations/gates; if actual entrypoints produce extra/different issues, record the full actual list and STOP rather than filtering:

- `PUB_SCHEMA_EXACT_KEYS`: add unknown root key to untrusted Subject packet; exact parser; no reseal.
- `PUB_TYPE_BOOL_REQUIRED`: set Subject visibility `deep_link_eligible=1`; reseal dependent closure/projection/packet; untrusted parser.
- `PUB_TYPE_MISMATCH`: set Subject `projection.receipt_ref=7`; reseal projection/packet; untrusted parser.
- Five identity codes: change only receipt-scope project/run/snapshot/site/spine respectively, reseal scope→receipt→packet, use independent dimension gate.
- `PUB_VISIBILITY_DEEP_LINK_INELIGIBLE`: set subject visibility false, reseal, invoke real visibility/source validator.
- `PUB_RUNTIME_TEST_SURFACE_FORBIDDEN`: create one exact forbidden producer/test path inside `TemporaryDirectory`, then invoke an AST-equivalent parameterized accepted no-runtime-surface gate; no workspace write.
- `AEMH_WITHDRAW_REAPPEAR_HISTORY_LOSS`: delete the unique AE reappeared entry from current packet, reseal thread→projection/evaluation identities→receipt→packet, then invoke history preservation gate.
- `SEM_TYPE_MISMATCH`: set risk taxonomy `package_id=7`; accepted common parser.
- taxonomy incomplete: rules `[]`; accepted risk validator.
- taxonomy ambiguous: append a duplicate taxonomy rule; accepted risk validator.
- severity incomplete: remove the `critical` rule while legacy rules remain; accepted severity validator.
- source unresolved: set taxonomy evidence source record to missing and reseal evidence; accepted token-evidence validator.
- receipt hash mismatch: zero receipt hash without reseal; accepted receipt validator.
- accepted record hash mismatch: zero accepted-record hash and reseal receipt hash; accepted receipt validator.
- package-kind mismatch: set receipt kind to severity policy and reseal; accepted receipt validator.
- authority hash mismatch: zero candidate authority hash; accepted constructor plus candidate hash gate.
- authority mismatch: change candidate authority ref and reseal authority hash; accepted constructor comparison.
- manifest hash mismatch: zero accepted semantic manifest content hash; accepted parent/manifest validator.

## Independent non-LLM oracle

The verifier must not import the delta generator or trust gate/challenge expected fields. It independently:

1. executes accepted parent, semantic and temporal challenges to compute emitted codes;
2. proves pre-delta union=170 and missing set=exact 22;
3. constructs parent packet bases from accepted temporal v0.2 inputs with the real closed DAG and validates baseline hashes;
4. applies each declared primary mutation and proves the structural diff is exactly one primary operation;
5. independently reseals only declared dependencies and rejects stale/excess reseal;
6. dispatches by closed `gate_id → entrypoint` mapping, never case/error code;
7. collects actual ordered issue objects and recomputes accepted priority/order;
8. only then compares actual to the registry observation;
9. proves delta codes are exactly the missing 22 and union is 192;
10. rejects modified expected code/priority/observed issues without changing actual gate result.

Active fully resealed attacks must exercise the real verifier: expected poisoning, case/error/sentinel branching, gate substitution, parser normalization, multi-mutation smuggling, stale/excess reseal, local mirror oracle, dead-code replay, identity/history overreach, candidate self-equality, fake governance without actual temp path, priority drift, every accepted/negative/protection pin drift, duplicate pin disagreement, nine-path/producer/S5/bytecode/8911 boundary.

AST-check generator/verifier for mutual imports, shared expected plane, `assert`-only gates and case/error/sentinel dispatch.

## Manifest and verification

Manifest must state exactly:

```text
status=candidate_unaccepted
authority_scope=synthetic_test_only
pre_delta_executable_error_count=170
delta_challenge_count=22
post_union_error_count=192
new_error_code_count=0
renamed_error_code_count=0
reordered_error_code_count=0
clinical_truth_changed=false
parent_bytes_changed=false
semantic_bytes_changed=false
temporal_bytes_changed=false
implementation_v04_changed=false
producer_executed=false
port_8911_must_be_stopped=true
```

Run generator `--check` and independent verifier under normal, `-O`, `-OO` and `PYTHONHASHSEED=0,1,777`; two isolated byte-identical generations; exact offline Ruff; exact 5-artifact/nine-path set; all pins; 542 aggregate; producer/S5/bytecode/cache absence; 8911 stopped. No assert-only gate.

STOP on any mismatch, untriggerable code, extra issue, need to change accepted bytes/clinical truth, local expected mirror, nine-path write, pin/protection drift, optimization/seed/determinism/Ruff failure, absent real governance action or 8911 listener.

Only a fresh isolated reviewer may return `ACCEPT_R5_S5_PUBLIC_AUTHORITY_ERROR_REPLAY_COVERAGE_DELTA_V0_1` against one immutable manifest SHA. That token only allows a new append-only implementation-contract v0.4 revision snapshot to pin and consume these 22 replay cases. It does not accept the blocked v0.4, producer/runtime/tests/evidence/S5/UI/browser/real project/model/clinical authority/medical-writing/8911.

Return files, exact 170+22=192 execution evidence, gate observations, attacks, normal/O/O2/hashseed/double-generation/Ruff/pin/absence/8911 results, final nine SHA and next action. Do not self-accept.
