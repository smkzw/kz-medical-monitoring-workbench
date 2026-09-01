# R4-D07 Runtime Acceptance Record — 2026-08-14

Status: `ACCEPT_D07_RUNTIME`

## Accepted boundary

The isolated synthetic/offline R4-D07 clinical-safety, laboratory and examination runtime is accepted. This acceptance covers deterministic typed evaluation, fail-closed integrity and authority checks, Chinese three-part Query drafts, renderer-neutral Patient Journey events/risks/source jumps, replay and mutation behavior. It does not accept product UI, R5, real projects or data, real provider/model endpoints, D08-D10, production use, or the medical-writing subsystem.

Port 8911 remained stopped throughout. No real project was read or run. The medical-writing subsystem was not modified.

## Frozen authority anchors

- Contract file SHA-256: `0b1f42c108ab6d4f5caa11a879cd2233328518e061772f74668cf1afd520fe84`
- Contract semantic SHA-256: `6facbaed37a97f7963a3010072687d0a2509a0f0e768058bd71067b36ec3b02a`
- Catalog file/content SHA-256: `419f2a060e0d46550c0e1faaeabddd5094a12556ba7f9ba9f66d99be5b5ee4cd` / `cfc382ad81b786965da9a3e46c41218982eb2b6f93aafb3fcf1e0b0c51ce1669`
- Oracle file/content SHA-256: `c2c2c4694f4dfe49415c949664d5e174e9ffd0a42ddb83ddc03712aabe93881f` / `e0e244d03d06a30127daeb71769733439e8620d62722b78074eb2e2068a3f4e9`
- Registry file/content SHA-256: `f63ff8fa9e5857c574f8b9f924807f04def19d4089bc39cd72d1ba610f36a2d6` / `c6351e79d4e3bd088de24a6e8cf301bb729084b4e7219eb49b064e337708e5af`
- Generator SHA-256: `1b230c374830d69c7bc37323960696f9a50ed3bba16bfa9f8996e6a64ce44a9b`

Two narrow oracle errata were adjudicated before runtime acceptance and are recorded in `context/medical_monitoring_r4_d07_oracle_erratum_decision_20260814.md`: incorrect AST grading/priority and missing Journey anchored counts, followed by case 030 source-leaf equivalence. They do not claim recovery of any deleted conversation and do not alter the frozen contract, catalog or generator.

## Accepted implementation snapshot

- `d07_safety.py`: `309a9eb1515dc4bdb9e7fda7783505ffc6143b62ffbda02c53c1aec56e7f096e`
- `d07_safety_evaluator.py`: `b143f2237d1bb75a42d0635dccbd422037bcd1531a0091b2b060254118590010`
- `d07_journey.py`: `7c4f576b62fea6eb8b538680b3a3aba24d919dfc5b359c84db65a3bb4e842fce`
- `d07_query.py`: `a34ecd13981196f511ef45f5af1b83a7fb141e194c7e9a02740e5125386bde60`
- `d07_fixtures.py`: `be480b223e41bacbbae5161378cd10b8d29784ffd6c58ebc2e679cd7921ddd74`

The synthetic fixture adapter preserves the on-disk frozen catalog and registry identities, deep-copies a clearly named overlay, and separates `frozen_content_hash` from the recomputed `overlay_content_hash`. Production runtime modules do not import the fixture adapter or test-side oracle/registry.

## Closed verifier findings

1. Unknown/wrong-kind/tampered/missing-hash/scope/locator source targets now fail Journey jump, audience and projection together.
2. Query validates target schema, hash, scope and locator; raw `target_object_id` and materialized `target_ref` are supported, while conflicts and missing references fail closed.
3. Baseline-deviation and safety-priority thresholds are read from typed, versioned, hash-bound project rules; evaluator-internal `0.02`/`5` fallbacks were removed and missing fields fail closed.
4. Frozen catalog and synthetic overlay identities are explicit and self-consistent; the overlay no longer exposes the frozen top-level hash as its own.
5. No executable case/fixture-ID branch, oracle reverse dependency, `sys.path` mutation, runtime file I/O or fixture-output literal was accepted.

## Decisive evidence

- Generator `--check-inputs`, `--check-refs`, `--check`: all exit 0; 144 contiguous cases, 4,732 reference leaves, 7,607 resolved values, zero failing problems; only the two declared case-124 duplicate references remain.
- D07 challenge matrix: `303 passed`.
- Full R4: `3657 passed` with cache provider disabled and bytecode disabled.
- Adjacent R1/R2/R3: `327 / 598 / 339 passed`.
- Ruff: all checks passed.
- 8911 listener check: none.
- Independent same-session Luna verifier `019ffdb2-3613-7872-aa8e-47fcbaee88ad` returned `ACCEPT_D07_RUNTIME`; accepted report SHA-256 `7606bd255f801e4e6be06a5deea07667d353b0e0b0b7a23b87c9f03be32dbf65`.

## Route and recovery record

The original Pi implementation session completed the principal runtime correction, then later continuations failed terminally or drifted from the declared route. The declared CodeBuddy `deepseek-v4-pro:xhigh` fallback was used in the same CodeBuddy session; an empty placeholder-only response was rejected and recovered in-session before accepting any edits. Codex independently reran the checks. The original Luna verifier session retained veto authority through each corrective pass and accepted only the final stable snapshot.

## Next safe action

Freeze the R4-D08 multi-table medical-logic and data-quality slice before implementation. D08 must consume accepted upstream D01-D07 coverage and identities, compare typed record relationships and shared temporal precision, fail closed when any participating domain is incomplete, and produce traceable cross-table inconsistency/missing-link risks, three-part Query drafts and Journey highlights. Continue without services, real projects, R5 UI, medical-writing changes or system-security work.
