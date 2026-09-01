# R5-S5 temporal-projection authority delta v0.1

## Disposition

`REVISED_AFTER_FRESH_REVIEW_FOR_NEW_INDEPENDENT_REVIEW` — not accepted. The delta is append-only, `synthetic_test_only`, and `non_clinical=true`.

## What this delta repairs

The accepted parent schemas expose 272 output leaves, but removal of candidate/target/example expected-output mirroring left 169 leaves unconstructible. The missing roots were systemic: cutoff endpoint selection, temporal/date/axis authority, visit/event/phase/risk membership, visibility universe and stable identity bridge, locator/revision consumption, pending membership, and AE/MH append decisions/evidence/thread membership. Dependent identifiers, hashes, memberships, projections, receipts and packets consequently had no honest construction order.

This delta adds independent authority input types and 18 exact recipes only. It does not add a producer, expected output, clinical value, fixture branch or owner-authored target. The accepted 17/13 output schemas and accepted semantic delta remain byte-identical.

## Frozen machine contract

- 25 exact-key authority objects, 37 closed named/nested types and 38 closed enums. The manifest-owned canonical schema baseline is verifier-hard-pinned by `9f2784b14c7e9f1ac6d151d340f98b834e449185af3c0ffcc0fd32f0a93c197c`; recursive exact comparison freezes object/field sets, required/optional partitions, type, enum members, cardinality, nullability, constraints and conditional rules.
- The external registry root is a manifest-owned contract artifact, not candidate data. Its independently hard-pinned content hash is `580d367783f8a00e68e8779fceec9146ddadd2bc3dd0040d26937d415b0589b3`, and the complete canonical section bytes are pinned by `65e2d571ba6858c65c2a82957639968b8f00431f2df56549a4c09f55733832cd`; candidate fixtures only reference it.
- The single accepted record's complete canonical payload is pinned by `295a916100ea53efe816fc79ae818fc4bb0ef38a75eaaf258f3a58e314cbf391`. Candidate authority content must exact-equal it; policy payload drift fails even with legitimate refs/root and a fully resealed chain. Strict operational evidence is separate and carries no policy semantics.
- Controlled packages cover only phase labels, timezone/day-zero, date state/range projection, empty-domain applicability, and AE/MH transitions. Accepted semantic event/risk authorities are referenced by immutable pins and are not copied.
- All 18 recipes are executable closed IR frozen only in the manifest-owned accepted registry. Its hard pin is `91687b6d7aa7acb3d0fa24732e2872d81e7ec597c76a9d4d863dfdab40f84e3a`, with 18 independently frozen per-recipe hashes. Candidates reference recipe IDs only.
- All 119 former-D authority mappings are executable and frozen only in the manifest-owned authority-output registry. Its hard pin is `2b92462366004c46bd460927514627d209cc608f3cf23688b8501ac03fad3607`. Each mapping binds one exact leaf to a minimal ordered fixture/field slice, fixture content pins, scope/join keys, exact operation with one closed op-specific parameter object, output type and canonical/hash recipe; mutable ledger rows are not proof.
- Recipe authority bindings are separately manifest-owned and pinned by `3bce92047ffb6d3173d1e22dbc7c59db922c4a4e75f7cf602c31511f4f71c463`. Each of 18 recipe fixtures must exact-match its ordered object-kind/role/scope/content-hash requirements before IR execution.
- The machine coverage ledger contains all 272 accepted parent leaves exactly once: A=53, B=46, C=4, D-before=169. Each row resolves to one declared authority output or a literal frozen recipe output for that exact qualified leaf, with a dependency chain. Exact bijection=272; nominal mappings=0; `unexplained=false`.
- Hash construction is explicitly upstream-first: authorities, members/endpoints, memberships, inner hashes, projections, external receipts, then packets.

## Adversarial contract

The 418-case registry contains 272 structural leaf-deletion probes plus 146 typed one-mutation attacks. Eighteen executable recipe fixtures exercise every accepted recipe, while 119 sealed authority-mapping fixtures execute every authority leaf against exact typed source records. This gives 283 semantic typed probes versus 272 structural coverage probes. Twenty attacks cover generic schema dimensions. Deletion probes are coverage evidence only.

The independent interpreter recomputes exact outputs and execution traces for all 119 authority mappings through six separate branches: `direct_field=67`, `derive_value=2`, `project_record=13`, `assemble_sorted_records=4`, `canonical_hash=13`, and `project_contract=20`. Each branch has distinct parameter/output rules, at least one positive fixture and one negative-output fixture. Each trace must exactly equal its declared fixture/field slice; operation dispatch, missing dependencies and unused dependencies fail closed. The registry has 91 unique slices, dependency counts min/median/max `9/15/194`, zero mappings with all 19 fixtures and zero unused declared dependencies. It validates target type/cardinality/nullability, stable two-event assembly, source content pins and full hash propagation. Reported closure remains `119/119`, with zero unconsumed refs and zero leaves without an emitter.

All 18 recipe fixtures independently resolve their ordered authority object-kind/role/scope bindings before recipe execution. Cyclic reassignment across the complete fixture set fails. Active controls also reject global-union dependency replacement, a no-op mapping operation, all 30 ordered cross-op substitutions with unchanged outputs, and six op-specific wrong outputs.

It also validates authority fixtures against the frozen schema, rejects arbitrary or valid-but-unaccepted recipe mutations before execution, rejects generic schema drift, proves exact accepted-record equality, and rejects a closure redirected to a recipe lacking that leaf. The generator never imports or executes the verifier and does not read a supplied target fixture to construct authority outputs.

The independent verifier must derive leaf paths from the accepted schemas, execute mutations without importing generator helpers or consulting case ids/expected labels, recompute canonical hashes, resolve frozen external registry/pins, and fail if any accepted/rejected/protected snapshot drifts. It also enforces exact nine-file scope, no producer/runtime/test/evidence/bytecode/cache, S5 locks, the 542-file medical-writing aggregate, and port 8911 stopped.

## Acceptance boundary

No acceptance record is produced. A fresh reviewer alone may return `ACCEPT_R5_S5_TEMPORAL_PROJECTION_AUTHORITY_DELTA_V0_1` for one immutable manifest SHA. Acceptance would unlock only implementation-contract v0.3 generation; it would not accept or unlock a producer, S5 runtime, UI/browser, real project/model, clinical authority, product, production or medical writing.
