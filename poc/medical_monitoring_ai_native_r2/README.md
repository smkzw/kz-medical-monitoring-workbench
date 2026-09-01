# medical_monitoring_ai_native_r2

Framework-neutral R2 domain kernel for the medical monitoring AI-native POC.
**Synthetic/offline fixtures only.** No real-project paths, credentials, or
network.

## Scope (Batch A)

Batch A (worker_01) owns the schema registry, immutable source/snapshot/
knowledge/rule/mapping/fact entities, record/risk identity, content-addressed
artifacts, and the snapshot acceptance state chain.

| Module | Responsibility |
|---|---|
| `schema_registry.py` | Sole schema/version declaration point; fail-closed compatibility; frozen after construction |
| `domain.py` | Immutable `StudyProject`/`SourceRevision`/`ListingSnapshot`/`StudyKnowledgePack`/`RuleActivation`/`MappingDefinition`/`MappingResult`/`CanonicalFact` with provenance + real content-addressed hashes |
| `identity.py` | `RecordIdentity`/`AmbiguousIdentity`/`RiskIdentity` with project-scoped, deterministic IDs, lineage-bound + order-canonicalized digests |
| `artifacts.py` | `ArtifactEnvelope` (artifact_id excluded from content address) + content-addressed `ArtifactStore` |
| `acceptance.py` | `SnapshotAcceptanceState` chain, `SnapshotBinding` (real verified bundle), frozen `SnapshotAcceptanceRecord`, service-issued `AcceptanceEvidence`, `AcceptanceDecisionRecord`, copy-on-write `AcceptanceService` |

## Scope (Batch B)

Batch B (worker_02) owns the risk lifecycle, adjudication, dual baselines,
three ModeContracts, and full/incremental snapshot diff.

| Module | Responsibility |
|---|---|
| `risk.py` | `RiskCandidate` (never auto-promotes), `RiskInstance` (stable project-scoped identity + source snapshots), `RiskTransition` (append-only lifecycle covering established/escalated/deescalated/closed/reopened/identity_ambiguous/superseded/not_evaluable), `AdjudicationRecord` (binds evidence + exact target risk versions, never masquerades as user confirmation), `RiskLifecycle` (source-bound close and merge/split lineage-preserving service) |
| `baselines.py` | `DataBaseline` + `MedicalDecisionVersion` (orthogonal axes); only baseline-eligible accepted full snapshots become diff baselines |
| `modes.py` | Three immutable `ModeContract`s (daily/pre_lock/post_lock_pre_cfdi) with explicit entry/cutoff/revision/publication rules; post-lock uses a service-issued local-user locked-version selection; mode change creates a new `MonitoringRun` (no silent conversion) |
| `diff.py` | Full/incremental `SnapshotDiff` comparing accepted full snapshots; distinguishes add/change/disappear/scope_change; field-level provenance + impact inputs; config (knowledge/rule/mapping/mode) changes separated from clinical data changes |

## Key Contracts (Batch B acceptance)

1. **RiskCandidate never auto-promotes**. Promotion to `RiskInstance`
   requires an explicit `AdjudicationRecord` with a supporting outcome
   (`merged_supported` / `distinct_supported`). `rejected_by_evidence` /
   `version_mismatch` / `needs_user_attention` block establishment.
2. **RiskInstance identity is stable and project-scoped**. Identity is
   content-addressed over `(project, subject, domain, scope, classifier,
   derived_from)` and never overwritten. Transitions derive the current
   state from the last transition; state and history cannot diverge.
3. **RiskTransition is append-only** and covers all required states:
   established, escalated, deescalated, closed, reopened,
   identity_ambiguous, superseded, not_evaluable. Terminal states
   (superseded, not_evaluable) reject forward transitions. Closed can only
   reopen. Direct `RiskInstance` construction is blocked for public callers
   (authority token sealed at module load).
4. **Merge/split lineage preserves old identities**. Merge creates a new
   identity whose `derived_from` references the originals; the originals
   are superseded (not deleted). Split creates multiple new identities
   referencing the original; the original is superseded. Original history
   is always queryable. Any ancestor user confirmation and SAE/AESI flag is
   inherited by the new merged/split risk and cannot be downgraded by a
   machine-only lineage operation.
5. **AdjudicationRecord binds evidence and the exact target risk version**
   (candidate/risk/source/rule/
   model-analysis) and cannot masquerade as user confirmation: a machine
   adjudication (`is_machine_adjudicated=True`) cannot declare
   `user_confirmed=True`. The two flags are mutually exclusive by
   construction. A decision issued for an older last-transition hash cannot
   be replayed after the risk state changes.
6. **DataBaseline and MedicalDecisionVersion are orthogonal**. Neither
   blocks, depends on, or rewrites the other. Only baseline-eligible
   accepted full snapshots can become data baselines. Medical decision
   versions are append-only; signed/exported versions are immutable history.
7. **Three ModeContracts are immutable** with explicit entry conditions:
   daily (accepted snapshot), pre_lock (cutoff + lock-prep window),
   post_lock_pre_cfdi (RunManager-issued local-user locked-version selection
   + fixed total; no caller-asserted authorization boolean).
   **No silent mode conversion**: a mode change always creates a new
   `MonitoringRun` with explicit carry-forward declaration.
8. **Full/incremental diff compares accepted full snapshots** and
   distinguishes add/change/disappear/scope_change. Disappearing rows are
   flagged with `needs_scope_check` (no auto-risk-resolution). Field-level
   provenance (canonical field, old/new value, partial-date/unknown flags)
   is preserved. Impact inputs (subject, domain, canonical_field) are
   emitted for incremental recomputation. Nested field changes and impact
   domains are order-canonicalized before semantic hashing. Config changes (knowledge/rule/
   mapping/mode/identity-algorithm) are explicitly separated from clinical
   data changes via `ConfigChangeSet`.

9. **Automatic close is source- and coverage-bound**. Establishment records
   the exact source AcceptanceService and accepted source snapshot. Machine
   close requires a later baseline-eligible full snapshot from that same
   service, a close adjudication bound to that coverage snapshot, and a
   `rejected_by_evidence` outcome. High risk, SAE/AESI, or any risk with prior
   user confirmation cannot be machine-closed. Merge adjudication binds the
   exact resulting severity and classifier; merge/split cannot lower the
   strongest source-risk severity. SAE/AESI recognition covers exact terms,
   camel-case labels, full English medical terms, and common Chinese medical
   labels before the close gate is evaluated, while explicit negative labels
   remain unflagged. Merged scope is the sorted union of all source scopes, so
   reversing an identical merge target set cannot change the resulting risk
   identity.

## Key Contracts (Batch A acceptance)

1. **Content digests** (`SourceRevision.content_digest`,
   `ListingSnapshot.content_digest`) must be canonical 64-char lowercase hex
   SHA-256. `validate_sha256_hex` enforces this; empty/short/non-hex/uppercase
   are rejected.
2. **Authoritative construction (VETO3)**. `SourceRevision` and
   `ListingSnapshot` are constructed only from actual immutable source bytes /
   canonical full-listing rows via `SourceRevision.from_bytes(...)` and
   `ListingSnapshot.from_content(...)`, which compute the digest internally
   and verify row/shape metadata where feasible. `RecordIdentity` /
   `RiskIdentity` are built from a real `IdentityAlgorithm` or dimensions via
   `make_record_identity` / `make_risk_identity` / `from_verified` /
   `from_dimensions`. `CanonicalFact.from_bundle(...)` binds real
   project/source/snapshot/record-identity/identity-algorithm/mapping-result
   objects and validates cross-project/snapshot/source/algorithm consistency.
   Digest-only / fabricated-reference construction is unavailable to public
   callers: `_verified` is checked against a construction capability captured
   inside the authoritative factories/validators and absent from the module
   namespace, so an ordinary caller cannot retrieve a package attribute or
   pass `_verified=True` to bless an arbitrary digest/reference.
3. **Verified rehydration boundary (Batch C)**. The generic codec
   `from_dictable` **fails closed** for authoritative/content-addressed
   entities: it will not reconstruct a `SourceRevision`/`ListingSnapshot`/
   `MappingResult`/`CanonicalFact`/`RecordIdentity`/`RiskIdentity` from
   arbitrary serialized data, because that would trust a caller-chosen
   digest. Batch A deliberately provides no rehydration constructor for those
   entities. Batch C must add an adapter that first verifies the carried digest
   against the actual stored artifact bytes, then recreates the authoritative
   object. Non-authoritative entities round-trip normally through
   `to_dictable`/`from_dictable`.
4. **Deep immutability (VETO2)**. Every JSON-like field (scope, structure,
   config, layers, impact analysis, key fields, payload, source location,
   coverage, QC, lineage, params, claim_scope) is deep-frozen via
   `deep_freeze_json` at construction: nested dicts become immutable
   `ImmutableDict`s (a `collections.abc.Mapping` backed by
   `types.MappingProxyType` -- **not** a `dict` subclass, so there is no
   mutable base-class backdoor such as `dict.__setitem__(frozen, ...)` and no
   reachable mutable backing via `frozen._m[...]`), lists become tuples, and
   non-finite numbers / unsupported leaf types are rejected. Mutating the
   original caller input or any value reachable from the frozen object is
   impossible and cannot change a recomputed identity/hash. `canonical_json`
   rejects non-finite numbers.
5. **Acceptance chain** requires step-specific affirmative evidence at every
   transition: `structural_validation_complete` for `structurally_valid`,
   `critical_mapping_clean` + `identity_review_clean` for `mapping_reviewed`,
   `approved_scope` (+ `deterministic_mapping` for `system_policy`) for
   `snapshot_accepted`, and `source_coverage_complete` + all prior gates for
   `baseline_eligible`. Registration binds a real verified `SnapshotBinding`
   (snapshot + source + identity algorithm + **at least one** one-to-one
   consistent mapping definition/result whose `record_count` equals the
   complete snapshot row count + an **explicit**
   `IdentityResolution` bound to the same identity algorithm whose resolved +
   ambiguous outcome cardinality equals the complete snapshot row count).
   Neither
   mapping review nor identity review can be waived by any actor (including
   the local user); a zero-row snapshot may use an explicit empty-but-clean
   `IdentityResolution`. Evidence is **issued by the service** via
   `AcceptanceService.evidence(...)` and bound to the registered binding
   fingerprint; the critical-mapping / identity / deterministic properties
   are **derived from the registered binding** at construction and re-derived
   at advance time, so a caller cannot declare them. A real
   `confidence=0.0, is_critical=True` mapping cannot be promoted by
   substituting an unrelated high-confidence definition
   (missing/extra/substituted/duplicated/version-mismatched mappings all fail
   closed in `SnapshotBinding`). The binding `fingerprint` binds the **full
   canonical immutable contents** of every mapping definition/result and the
   identity-resolution outcome (not just IDs/clean booleans), so same-ID
   bindings with different material semantics hash differently. Every
   blocked/illegal/unknown-actor attempt (including unauthorized `reject`)
   appends an auditable `transition_blocked`/`rejected` decision record
   without changing the accepted state.
6. **Actor gate (VETO4)**. `AcceptanceService(local_user=...)` is initialized
   with the current local OS user (synthetic fixture name `local_test_user` in
   tests). Transitions are allowed only by that user or `system_policy`; any
   other actor is rejected and audited.
7. **Default schema registry** is frozen after construction; runtime mutation
   is rejected (VETO1). Freezing also deep-freezes the declaration table
   (`_by_name` and every inner mapping become read-only dict views), so
   callers cannot insert schemas by bypassing `register()`.
8. **Artifact content address** excludes `artifact_id` and `created_at`.
   A `payload_role="facts"` envelope accepts only one or more already verified
   `CanonicalFact` objects; a dictionary, candidate payload, mixed collection,
   or empty collection cannot be relabelled as facts.
9. **CanonicalFact** is facts-only, binds `record_identity_digest`,
   `identity_algorithm_digest`, `mapping_result_id`, and the full semantic
   `mapping_definition_digest`, and derives a
   deterministic `fact_id` from project/source/snapshot/type/record/mapping/
   location/payload. Fact construction requires the MappingDefinition to
   declare the same `fact_type`, and MappingResult binds that definition's
   full semantic digest so a same-ID mapping cannot be substituted.
   Candidate/inference/suggestion are ArtifactEnvelope payload roles only.
10. **MappingDefinition.version** is required. **RuleActivation.activated_by**
    is required.

## Verified construction / rehydration boundaries

- **Construct responsibly**: use the `from_bytes` / `from_content` /
  `from_verified` / `from_dimensions` / `from_bundle` factories or the
  `make_*` helpers. Direct dataclass construction of content-addressed
  entities (`SourceRevision`, `ListingSnapshot`, `MappingResult`,
  `CanonicalFact`, `RecordIdentity`, `RiskIdentity`) is blocked for normal
  public callers (`_verified` is checked against a captured construction
  capability, not a boolean/string, and that capability is absent from the
  module namespace).
- **Acceptance authority**: register a `SnapshotBinding` of real verified
  objects (>=1 mapping definition/result + an explicit `IdentityResolution`)
  and obtain evidence via `AcceptanceService.evidence(...)`. Direct
  `AcceptanceEvidence(...)` construction is blocked; its public signature has
  no issuance input, and the build-time issuance capability is absent from the
  loaded module namespace.
- **No digest-only rehydration in Batch A**: there is deliberately **no**
  callable `_rehydrate_verified` / digest-only path. `from_dictable` fails
  closed for authoritative entities, and direct construction is blocked.
  Batch C must add a verified rehydration adapter that verifies the actual
  stored artifact bytes/hash before recreating an authoritative object from
  untrusted/migrated data.

## Running

```bash
cd poc/medical_monitoring_ai_native_r2
python -m pytest tests/ -q
```

## Scope (Batch C)

Batch C (worker_03) owns the user-functional persistence foundation:
SQLite store, atomic commit, idempotency, publication read-consistency,
verified rehydration, migration, and the R1 read-only legacy adapter.

| Module | Responsibility |
|---|---|
| `verification.py` | Verified rehydration adapter: rebuilds authoritative entities ONLY after verifying stored artifact bytes/hash |
| `audit.py` | Hash-chained tamper-evident audit log (SQLite-backed, append-only, genesis-anchored) |
| `store.py` | SQLite `R2Store`: artifact-first atomic commit, idempotency ledger, publication pointer, reopen after restart |
| `migration.py` | Export/import/backup/restore/rollback: proves user data can be moved and restored without losing publication, history or identities |
| `legacy_adapter.py` | R1 read-only adapter: opens synthetic fixture in `mode=ro`, no write method, proven identity mappings, dual-read diff |

## Key Contracts (Batch C acceptance)

1. **Artifact-first commit**. Content-addressed bytes are written and
   hash-checked BEFORE one explicit SQLite transaction commits state +
   audit + business-history reference. A crash before COMMIT leaves no
   authoritative state.
2. **Idempotent submit**. One stable idempotency key makes duplicate
   save/retry return the same committed result without duplicate history.
3. **Publication read-consistency**. The publication pointer advances
   only to a COMPLETE, readable artifact. Incomplete/partial/truncated/
   not_evaluable/failed results can never become the current published
   result -- users must never open a half-finished dashboard.
4. **Verified rehydration boundary**. Authoritative entities are rebuilt
   ONLY after verifying the actual stored bytes/hash via `Rehydrator`.
5. **R1 adapter is read-only**. It opens only a synthetic legacy SQLite
   fixture in `mode=ro`, exposes no write method, performs only proven
   source/fact/risk identity mappings, and emits explicit
   matched/unmatched/ambiguous dual-read differences.
6. **Migration is functional recovery**. Export/import/backup/restore
   move user data and restore it without losing current publication,
   history, or identities.
