# R5-S5 Public Authority Implementation Contract v0.4.2 Plan

State: `ACCEPTED_2026-08-25`

## Goal

Create a new immutable v0.4.2 implementation contract that consumes the accepted
typed-authority model delta v0.1 and closes the four v0.4.1 fail-open findings without
modifying any accepted or rejected historical snapshot. Only a fresh acceptance of
v0.4.2 may unlock the exact eleven create-only producer paths.

## Immutable inputs

- typed-authority delta acceptance record:
  `context/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1_acceptance_record_20260825.md`
- typed-authority manifest content hash:
  `38a8cadee3bcac6dd74a5ce9d522c9f744e82592f87089423e7783be7f6be976`
- accepted parent, semantic, temporal v0.1/v0.2 and error-replay delta pins already
  named by the typed delta and v0.4.1 pause record.
- rejected v0.4.1 remains immutable negative/scaffolding evidence only. Its values,
  selectors, issue metadata and self-reported execution flags are never authority.

## Required authoritative surfaces

1. `leaf_execution_registry.json`
   - exactly 272 rows from the accepted typed-authority contract;
   - 268 `accepted_recipe_to_parent_packet_compare` rows;
   - four `subject_public_cutoff_from_binding` rows with parent object-hash validation;
   - no R1/R2/R4 mutable-class selector and no second typed truth plane.
2. `error_replay_execution_registry.json`
   - exactly 192 independently reconstructed rows: accepted pre-delta 170 plus accepted
     error-replay delta 22;
   - every row binds source challenge, base, mutation, reseal program, gate entrypoint,
     complete ordered issues and execution evidence;
   - candidate matrix metadata cannot supply expected path/message/origin/priority.
3. `active_gate_execution_registry.json`
   - exactly 58 independently reconstructed executable attacks: 22 accepted governance,
     22 accepted error-delta and 14 v0.4.2 contract attacks;
   - verifier consumes every row, executes its gate and compares the exact issue;
   - replacing the registry with fake rows, preserving only count 58, must fail.
4. `runtime_reject_metadata_registry.json`
   - exactly 226 rejecting runtime traces;
   - issue objects are rebuilt from independently reconstructed accepted error authority,
     never backfilled from the candidate error registry;
   - trace identity, full ordered code sequence and issue-object digest are frozen.
5. `future_producer_contract.json`
   - exact eleven create-only paths and packet-only public API;
   - accepted `AuthorityBundleV02` is the internal serialized input authority;
   - AST, pytest, sensitivity and isolation gates are machine executable but remain
     unexecuted until v0.4.2 acceptance.
6. `manifest.json`, generator, independent verifier, context and author review complete
   the exact path set and pin all accepted inputs and protected boundaries.

## Mandatory attacks

- Replace all 272 leaf rows with v0.2-mirrored fake typed selectors.
- Mutate one recipe-to-packet leaf, one cutoff constructor digest and one authority root.
- Replace all 192 error rows with fake gate/base/mutation/reseal values.
- Replace all 58 active gates with fake specifications while retaining count.
- Backfill all 226 reject issue objects from the candidate registry.
- Drift any accepted input pin, 542-file aggregate, producer absence or port 8911 state.
- Add candidate/expected/target output as an input authority.

Every attack must fail for its primary gate, not only through a generic content-hash
mismatch. Normal, `-O`, `-OO`, hash seeds 0/1/777, deterministic double generation,
generator `--check`, compile and independent fresh review are required.

## Boundaries

- Do not modify v0.4.1 or the accepted typed delta.
- Do not create the eleven producers, S5 runtime/UI files or acceptance evidence.
- Do not start 8911, browser, real project or model tests.
- Do not touch medical-writing or its protected 542-file aggregate.

## Next safe action

The v0.4.2 contract is accepted by
`context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2_acceptance_record_20260825.md`.
The next safe action is the exact eleven-path create-only producer stage. Keep 8911
stopped and do not enter S5 UI, browser, real-project or model testing until the
producer package passes its own focused acceptance gates.
