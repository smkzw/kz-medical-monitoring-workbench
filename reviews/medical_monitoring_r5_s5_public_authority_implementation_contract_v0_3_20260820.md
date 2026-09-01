# R5-S5 public authority implementation contract v0.3

Status: `FROZEN_FOR_FRESH_INDEPENDENT_REVIEW`

## Result

The v0.3 contract replaces the rejected v0.1/v0.2 local expected-authority design with direct consumption of the three accepted authority surfaces. No candidate or target output is an oracle. The future builder must execute accepted operation-specific emitters and recipe IR, then rebuild identifiers, hashes, memberships, projections, receipts and packets upstream-first.

The Python floor is 3.9. Exact dataclass and function signatures are frozen in `public_api.json`; imports use full module paths and root `mm_r5/__init__.py` remains unchanged. Serialized output schemas are byte-pinned to the accepted 17/13 schemas.

## Source and invariant closure

`source_join_matrix.json` contains the accepted temporal delta's exact 272-row bijection. It binds 119 leaves to accepted authority emitters, 50 former-D dependent leaves to accepted recipe IR, four leaves to the accepted semantic delta, and the remaining accepted parent/derived leaves to the parent-plus-temporal closure. No row permits output backfill, class-wide value closure, nearest fallback, nominal-to-actual inference, D07 OTHER, S4 semantic transfer, `Any`/`Mapping` authority, sentinel branching or model escalation.

`invariant_error_matrix.json` creates one deterministic total priority across the accepted parent codes and namespaced `SEM_*` and `TPA_*` delta errors. Any issue forbids packet emission. AE/MH prefix bytes, membership, evidence identity, reachable `CanonicalFact.fact_hash`, append lifecycle and packet hashes remain fail-closed.

## Test inventory

Exactly 231 executable future specs cover 236 accepted traces through five exact aliases. Identity is recomputed without case IDs, labels, fixture names, oracle fields, expected codes or sentinels. Each spec freezes a typed candidate/reference packet, one accepted trace mutation, actual-instance selector/linked operations, typed result/error, forbidden output, exact future pytest node and non-LLM oracle. Ten positive specs require full packet construction from transformed typed sources; baseline output patching is forbidden.

The 22 parent artifact-governance cases are separate and execute during contract verification. The accepted temporal verifier's 418 challenges and this verifier's exact emitter/recipe execution cover fully resealed self-authorization, simultaneous candidate/target drift, cyclic fixtures, same-type swaps, cross-scope joins, membership changes, forged endpoints/counts/locators/visibility/pending/phase/risk/AE-MH evidence, prefix rewrite and wrong fact identity.

## Non-transfer

This document is not an acceptance record and does not accept a producer, S5, UI/browser, real project/model, clinical authority, product, production or medical writing. A later independent reviewer alone may return `ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_V0_3`.
