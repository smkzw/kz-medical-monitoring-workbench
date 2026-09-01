# mm_r4 — R4 Medical Monitoring Common Contract (AI-Native POC, Synthetic Only)

Isolated R4 package implementing the frozen common coverage contract
(`FROZEN_R4_CONTRACT_V1`) for the medical monitoring AI-native POC. Imports
frozen public APIs read-only (R1 `CoverageUnitStatus` for L0 values, R2
`RiskLifecycleState` for L3 authority); does not copy or fork lifecycle or
normalization authority. The runtime library does not mutate `sys.path`; the
caller/test environment supplies the R1/R2 source roots.

## Status

- **worker_01:** common coverage contract — layer namespaces, value objects,
  deterministic canonical hashing, expected-set ledger, completeness
  predicate, and focused contract tests.
- **worker_02:** AE/MH semantic-role slice and Query/journey projection
  (`aemh.py`, `projection.py`, `tests/test_aemh_slice.py`).
- **worker_03:** R2 lifecycle adapter, synthetic challenge fixtures, and
  N→N+1 / adversarial tests (`lifecycle.py`, `fixtures.py`,
  `tests/test_lifecycle_projection.py`, `tests/test_challenge_matrix.py`).
- **worker_02 (D04):** D04 protocol-compliance domain model — applicability
  gates, routing, component/package evaluation, Chinese Query drafts and
  coverage-gap notices (`protocol.py`, `tests/test_protocol_slice.py`).
- **worker_03 (D04):** D04 journey projection, synthetic fixtures and the
  full 83-case challenge matrix with golden hashes
  (`protocol_projection.py`, `protocol_fixtures.py`,
  `tests/test_protocol_projection.py`,
  `tests/test_protocol_challenge_matrix.py`).
- **worker_01 (D05):** D05 visit/assessment/sample timing domain model —
  immutable planned/actual objects, dual cutoff, encounter bundles, gates
  and typed anchors (`visit_schedule.py`,
  `tests/test_visit_schedule_contract.py`).
- **worker_02 (D05):** D05 evaluator — gates, applicable expected-set,
  bidirectional assignment, consumption ledgers, five-L1-disposition
  evaluation, priority policy and Query/lifecycle wiring
  (`visit_schedule_evaluator.py`, `tests/test_visit_schedule_slice.py`).
- **worker_03 (D05):** D05 renderer-neutral journey projection, synthetic
  fixtures and the full 116-case challenge matrix with golden hashes
  (`visit_schedule_projection.py`, `visit_schedule_fixtures.py`,
  `tests/test_visit_schedule_projection.py`,
  `tests/test_visit_schedule_challenge_matrix.py`).
- **worker_01 (D06):** D06 efficacy domain model — canonical
  serialization, closed D06 enumerations, fail-closed errors, canonical
  priority policy and typed identity objects (`efficacy.py`,
  `tests/test_efficacy_contract.py`).
- **worker_02 (D06):** D06 evaluator — the contract-ordered pipeline with
  gates, unit evaluation across the eleven closed unit kinds, priority
  resolution, risk identity binding, enrollment-aware Chinese Query
  drafts and audience payload validation (`efficacy_evaluator.py`,
  `tests/test_efficacy_slice.py`).
- **worker_03 (D06):** D06 renderer-neutral journey projection and the
  full 219-case frozen challenge matrix executed through the real
  entrypoints with DSL/oracle verification (`efficacy_projection.py`,
  `efficacy_fixtures.py`, `tests/test_efficacy_projection.py`,
  `tests/test_efficacy_challenge_matrix.py`).
- **Package public surface:** `import mm_r4` re-exports the coverage contract,
  AE/MH evaluators, Query/journey projectors, lifecycle adapter,
  challenge-matrix builders, the D04 protocol slice (domain model +
  journey projection + 83-case challenge matrix), the D05 visit/assessment/
  sample timing slice (domain model + evaluator + journey projection +
  116-case challenge matrix) and the D06 efficacy slice (domain model +
  evaluator + journey projection + 219-case challenge matrix). Submodules
  remain importable directly.

## Common Coverage Contract (worker_01)

### Layer namespace separation (matrix §3.2)

R4 never reuses the same string for different layers. Each layer has its own
type, field name, and counter:

| Layer | Object | Contract |
|---|---|---|
| **L0** execution coverage | input/table/row/subject/site/domain actually read | Values sourced directly from the frozen R1 `CoverageUnitStatus` enum via `.value` (not copied literals): `covered/partial/truncated/not_applicable/not_evaluable/failed/missing`. Says nothing about medical evaluability. |
| **L1** medical evaluation | one versioned EvaluationUnit's medical result | Exactly one exclusive disposition: `positive/negative/boundary/not_applicable/not_evaluable` |
| **L1b** evidence polarity | evidence relative to a unit/clue/risk | Multi-valued set: `supporting/counterevidence/context`; counterevidence coexists with negative/positive/boundary — it is NOT a sixth disposition |
| **L2** domain objects | source records, risk candidates, risk instances, Query drafts | Four separately-counted types; never inter-derived |
| **L3** risk lifecycle | established risk's append-only state | `L3RiskStateRef` IS the frozen R2 `RiskLifecycleState` class (object-identity alias, not a copy); R2 `RiskLifecycle` is the sole lifecycle authority |

### EvaluationUnit hash dimensions (matrix §3.4)

```
unit_id = hash(
  project_id, domain_id, scope_type, scope_key,
  normalized_concept_or_rule_item, temporal_window,
  rule_or_knowledge_lineage, unit_algorithm_version
)
```

The eight dimensions are frozen. Any dimension change produces a different
`unit_id` and therefore a different expected-set. The hash is a deterministic
canonical JSON + SHA-256 (`content_hash`), input-order independent.

### Expected-set hash

`expected_set_hash(unit_ids)` sorts the unit ids before hashing, so the hash
is independent of input order. Duplicate unit ids are rejected (matrix §3.4:
each `unit_id` appears exactly once).

### Count equation and join invariants (matrix §3.4, §6)

The `CoverageLedger` enforces at assignment and close time:

- `expected_units = positive + negative + boundary + not_applicable + not_evaluable`
- each `unit_id` appears exactly once (duplicate rejected)
- no evaluation for a unit not in the expected-set (unexpected rejected)
- no expected unit left without an evaluation at close (missing rejected)
- every positive unit associates with at least one risk candidate or an
  active/ambiguous risk instance
- every Query links to a source, EvaluationUnit, and a candidate or risk
- Query source links use exact deterministic locator IDs reachable from that
  EvaluationUnit; mismatched unit/source joins fail closed
- L2 counts (source/candidate/risk/query) are separate and never inter-derived

### Domain-complete predicate (matrix §6)

`is_domain_complete(summary)` fails closed — returns `(False, reasons)` —
when any of:

1. L0 has any `partial/truncated/failed/missing` status;
2. any L1 unit is `not_evaluable`;
3. the count equation is broken;
4. the expected-set hash is missing.

A *reasoned* L0 `not_evaluable` does NOT prove medical completeness (matrix
§3.2 last paragraph). Run success, R1 coverage acknowledgement, a model
"complete" output, or a zero risk count never separately proves completeness.

## File ownership

| File | Owner |
|---|---|
| `src/mm_r4/__init__.py` | worker_01 initially; manager may refresh public re-exports |
| `src/mm_r4/contracts.py` | worker_01 |
| `src/mm_r4/coverage.py` | worker_01 |
| `src/mm_r4/aemh.py` | worker_02 (+ authorized identity integration patches) |
| `src/mm_r4/projection.py` | worker_02 |
| `src/mm_r4/lifecycle.py` | worker_03 |
| `src/mm_r4/fixtures.py` | worker_03 |
| `src/mm_r4/protocol.py` | worker_02 (D04 domain model) |
| `src/mm_r4/protocol_projection.py` | worker_03 (D04 journey projection) |
| `src/mm_r4/protocol_fixtures.py` | worker_03 (D04 83-case matrix + goldens) |
| `README.md` (common-contract sections) | worker_01 |
| `tests/conftest.py` | worker_01 |
| `tests/test_coverage_contract.py` | worker_01 |
| `tests/test_aemh_slice.py` | worker_02 |
| `tests/test_lifecycle_projection.py` | worker_03 |
| `tests/test_challenge_matrix.py` | worker_03 |
| `tests/test_protocol_slice.py` | worker_02 (D04) |
| `tests/test_protocol_projection.py` | worker_03 (D04) |
| `tests/test_protocol_challenge_matrix.py` | worker_03 (D04) |
| `src/mm_r4/visit_schedule.py` | worker_01 (D05 domain model) |
| `src/mm_r4/visit_schedule_evaluator.py` | worker_02 (D05 evaluator) |
| `src/mm_r4/visit_schedule_projection.py` | worker_03 (D05 journey projection) |
| `src/mm_r4/visit_schedule_fixtures.py` | worker_03 (D05 116-case matrix + goldens) |
| `tests/test_visit_schedule_contract.py` | worker_01 (D05) |
| `tests/test_visit_schedule_slice.py` | worker_02 (D05) |
| `tests/test_visit_schedule_projection.py` | worker_03 (D05) |
| `tests/test_visit_schedule_challenge_matrix.py` | worker_03 (D05) |
| `src/mm_r4/efficacy.py` | worker_01 (D06 domain model) |
| `src/mm_r4/efficacy_evaluator.py` | worker_02 (D06 evaluator) |
| `src/mm_r4/efficacy_projection.py` | worker_03 (D06 journey projection) |
| `src/mm_r4/efficacy_fixtures.py` | worker_03 (D06 219-case matrix + DSL/oracle adapter) |
| `tests/test_efficacy_contract.py` | worker_01 (D06) |
| `tests/test_efficacy_slice.py` | worker_02 (D06) |
| `tests/test_efficacy_projection.py` | worker_03 (D06) |
| `tests/test_efficacy_challenge_matrix.py` | worker_03 (D06) |

## D04 protocol-compliance slice (`FROZEN_R4_D04_CONTRACT_V1_1`)

The D04 slice evaluates versioned protocol eligibility/protocol-requirement
control points against accepted data and projects the result onto the
subject's protocol-compliance journey.  All inputs are synthetic; no real
project, drug name, fixed threshold, visit window or listing layout is
encoded.

- **Domain model** (`protocol.py`): closed owner-domain routing table
  (D02 CM / D03 IP / D05 visit-window stub / D08 relations), the mandatory
  per-subject `ProtocolApplicabilityDecision` (unique active version vs
  one subject-level gate), component-level evaluation with AND/OR/NOT/
  AT_LEAST_N parent issue expressions, exact cross-domain evidence gates,
  three-part Chinese Query drafts, and `ProtocolCoverageGapNotice`
  coverage-gap display payloads.
- **Journey projection** (`protocol_projection.py`): renderer-neutral
  `ProtocolJourneyEvent` / `ProtocolRiskMarker` payloads on the
  `protocol` track (AE/MH/CM/IP tracks stay distinct), actual/nominal
  visit-axis anchors, an unresolved area for events without any precise
  date, and a deterministic bidirectional `ProtocolEventMarkerJoin` index
  verified by stable ids with the closed join reasons
  `unit_identity | anchor_event | source_locator | producer_reference`.
  Producer-owned D02/D03/D05 control points surface only as typed
  `ProtocolProducerReference` entries and never create D04
  units/risks/Queries.
- **Challenge matrix** (`protocol_fixtures.py`): all 83 frozen §12
  challenge rows mapped to a focused executable D04 assertion or an
  explicit named adjacent accepted test, plus frozen golden
  unit/component/expected-set/candidate/projection-payload hashes.

## D05 visit/assessment/sample timing slice (`FROZEN_R4_D05_CONTRACT_V1_2`)

The D05 slice evaluates the versioned schedule of activities against
accepted actual encounter/assessment/sample records, producing a
traceable, repeatable "plan vs actual" evaluation unit.  All inputs are
synthetic and offline; no real project, provider, fixed visit number,
fixed window, fixed table name, fixed medication or fixed examination is
encoded, and port 8911 is never touched.

- **Domain model** (`visit_schedule.py`): immutable planned/actual objects
  with deterministic content addressing, the two non-interchangeable time
  boundaries (`snapshot_as_of` vs `clinical_event_cutoff`) and record scope
  classification, encounter bundles with canonical member ordering and
  merge/split rules, and exact typed schedule anchors.  `ScheduleGate` is a
  closed coverage/control-plane state (open + boundary/not_evaluable +
  blocks domain completeness, or closed + resolved) — an open gate never
  enters the medical expected-set and never creates a candidate/risk/Query.
- **Evaluator** (`visit_schedule_evaluator.py`): the contract-ordered
  pipeline — applicability/owner-routing/anchor/cutoff gates, applicable
  matured expected-set (future/out-of-cutoff obligations stay on the plan
  axis), bidirectional visit/activity assignment with closed evidence
  predicates (never nearest-date/VISITNUM/row order), consumption ledgers
  that prevent silent duplicate use, the closed five-L1-disposition
  evaluation with Chinese positive-subtype labels, first-match priority
  policy, and enrollment-aware three-part Chinese Query drafts wired through
  the shared R2 lifecycle adapter.
- **Journey projection** (`visit_schedule_projection.py`): renderer-neutral
  `VisitJourneyProjection` keeping planned-visit and actual-encounter
  markers separate on stable assignment edges, distinct domain lanes,
  a pending area for missing/partial/conflicting dates, a separate
  out-of-cutoff area for cutoff-later records, and audience payload QC that
  rejects internal/log vocabulary.
- **Challenge matrix** (`visit_schedule_fixtures.py`): all 116 frozen §13
  challenge rows mapped to a focused executable D05 assertion or an explicit
  named adjacent accepted test, plus pinned deterministic golden
  expected-set / projection / unit / candidate hashes.

`import mm_r4` re-exports the D05 domain model, evaluator, journey
projection and challenge-matrix builders.  Where a D05 constant name would
clash with an earlier slice's root export of the same spelling, the D05
value is exposed under a `D05_`-prefixed alias (e.g. `D05_OWNER_D05`,
`D05_PRECISIONS`, `D05_RELATION_TYPES`, `D05_POSITIVE_SUBTYPES`,
`D05_GOLDEN_UNIT_IDS`) so earlier exports are never overwritten.

## D06 efficacy endpoint / scale / individual-trend slice (`FROZEN_R4_D06_CONTRACT_V1_18`)

The D06 slice evaluates the frozen synthetic/offline efficacy endpoint,
scale, baseline, individual-trend, Query and renderer-neutral Patient
Journey slice.  All inputs are synthetic and offline; no real project,
provider, fixed scale, fixed threshold or service is encoded, and port
8911 is never touched.

- **Domain model** (`efficacy.py`): canonical serialization that reproduces
  the frozen generator's canonical JSON exactly (Unicode NFC, sorted keys,
  compact separators, NaN/Infinity rejected), closed D06 enumerations
  (unit kinds, positive subtypes, gate kinds/states, TTE states, scope
  statuses, query contexts, audience lexicon `d06-audience-zh-v1`),
  fail-closed error vocabulary, the canonical five-step `D06PriorityPolicy`,
  and the typed identity objects (`D06PriorityResolverInput`,
  `D06PriorityDecision`, `D06UnitStableCore`, `PublicR4RiskIdentity`,
  `D06RiskBinding`) with exact content addressing.
- **Evaluator** (`efficacy_evaluator.py`): the contract-ordered pipeline —
  exact project/run/subject/site/episode/cutoff/version identity with
  fail-closed authority, definition binding and applicability gates,
  D05 occurrence/timing binding and shared temporal spine, assessment scope
  decisions (cutoff / time roles / maturity), deterministic unit evaluation
  across the eleven closed unit kinds with the five exclusive L1
  dispositions, first-match priority resolution, risk identity binding for
  positive roots, enrollment-aware three-part Chinese Query drafts
  (PD wording only for `enrolled_or_post_enrollment`), and audience payload
  validation with the frozen lexicon.  The runtime never imports the
  catalog/oracle/registry and never branches on challenge/fixture/test ids.
  Integrity comes before priority: any typed scope/schema/pre-priority
  integrity failure (invalid typed scope override, mutated fixture scope)
  emits no priority resolution, no resolver input hash/object, no
  risk/public identity and no clinical projection, while unmutated
  frozen rows keep their oracle priority.  Supplied
  `risk_binding`/`public_r4_risk_identity` objects are validated
  bidirectionally field-for-field against the runtime-derived objects
  (drift fails closed; nothing is ignored and no canonical constant hides
  input drift); the `D06UnitStableCore` must carry `domain_id == D06` and
  its `stable_source_record_id` must resolve to an accepted-current
  `ActualAssessmentRecord` in the same scope/cutoff — a synchronized
  rehash of core + public identity + risk binding with a fake source or
  domain fails closed.  Every consumed accepted assessment is
  cross-resolved bidirectionally across the D05 binding ref, the
  accepted inventory and the foreign-key registry: lineage authenticated
  by `producer_payload_hash` (all three carriers), time authenticated by
  `actual_time_ref` (all three), D05 unit/planned/actual activity keys,
  occurrence/timing dispositions and assignment status agreed 4-way,
  foreign-key `binding_ref_id` linked, instrument/recall/admin resolved,
  item set/order enforced and every item's raw/normalized value
  authenticated against the typed item-values mapping with
  payload-consistent content hashes and locators.  TTE precedence ids resolve strictly from the
  typed TTE registry/bindings/events (binding linked to the typed
  `TTESourceRegistry`; selected-event time must match the typed TTE
  records and the evaluation window; no fixed fallback ids).  Every
  enrollment source event referenced by active decisions and context
  variants is resolved against the typed registry with decision-scope/
  cutoff/hash/locator/time-symbol linkage (missing/drifted sources fail
  closed and suppress the Query).  The typed fixture boundary is enforced
  by exact recursive schema validation (`validate_fixture_schema`)
  before evaluation: every typed nested object (definitions,
  assessment/source records, bindings/policies, TTE and enrollment
  events/registries, risk binding and public identity) must carry exactly
  its frozen key set, and unknown/missing/incompatible nested fields fail
  closed.  Unexpected non-typed exceptions are narrowed and never
  override an already-recorded typed error class/stage.
  The five frozen entrypoints are exposed: `evaluate_efficacy_fixture`,
  `evaluate_gate`, `validate_contract_schema`,
  `validate_audience_projection`, and
  `validate_challenge_registry_input`.
- **Journey projection** (`efficacy_projection.py`): renderer-neutral
  `EfficacyJourneyProjection` with an explicit visit axis, distinct
  efficacy/scale/response/trend lanes, typed event and risk markers with
  source jumps and risk anchors, and separate pending / out-of-cutoff
  areas — never collapsed into "已记录事项", never exposing internal terms
  such as "正式事实"/"候选信号"/"只读投影"/"positive"/"candidate".
  Projection id, shared temporal spine identity, marker ids/types, risk
  anchor/identity, marker priority and source-jump targets derive from
  the validated typed runtime objects and locators (no page/variant/
  static fallback identities); the risk marker priority comes from the
  typed `D06PriorityDecision`.  Every marker carries the actual typed
  `source_locator_ids` it was derived from and a content-addressed
  `payload_hash`, so a locator mutation/removal changes the projection
  hash or fails closed instead of retaining a generic payload.  The
  emitted audience journey payload is serialized from the constructed
  projection object (`journey_audience_payload_from_projection`) — never
  a static substitution disconnected from the projection; the direct
  serializer first verifies every marker's content-addressed
  `payload_hash` against a recomputation and every jump target against
  validated source locators (a dataclass-replaced/mutated projection
  with stale provenance raises a specific `ProjectionContractError`), a
  projection with no validated source locators suppresses the payload
  with the exact error state, and a valid projection still serializes to
  the frozen unchanged payload.
- **Challenge matrix** (`efficacy_fixtures.py`): the frozen 219-case
  catalog is adapted into typed runtime fixtures and executed through the
  real entrypoints; the frozen `d06-assert-v1` DSL is interpreted against
  the raw entrypoint output with an exact leaf bijection, and every raw
  outcome is compared with the independently persisted oracle — all 219
  rows exact under v1.18/8.0.3, including `clinical_outcome_contract`.
  No field is copied or replaced from the expected outcome, oracle,
  manifest trace edges, challenge number, fixture/test ids or
  annotations: the runtime derives every annotation leaf
  (`challenge_assertion_code`, `clinical_outcome_contract` via the frozen
  semantic-state mapping, `evaluated_fixture_hash`, `input_scope_hash`,
  trace provenance from the sources actually validated/consumed) from its
  typed input and frozen rules.  The definition-boundary resolver
  enforces the exact v1.18 instrument/endpoint schema key sets, canonical
  ids/stable keys/versions/object types, the exact complete definition
  scope and payload-consistent content hashes (v1.18), never case
  identity: a rehashed unknown field, rehashed version drift, missing
  field or wrong id/scope/schema/content fails closed instead of
  preserving a successful gate.  Fixture inputs are deeply frozen (nested
  mutation is inert) and the adapter boundary validates the exact
  recursive typed schema before evaluation;
  typed-input drift (baseline candidates, enrollment rules/events, risk
  binding / public identity fields, TTE event identities/binding ids,
  priority policy, scope, accepted report/result fields, definition
  schema/version/hash, nested source mappings, temporal spine) fails
  closed or changes the derived identity/hash.
  Mutation/tamper tests prove the raw output cannot be influenced by
  expected/manifest/case identity, and that removing only
  `fixture.challenge_number` leaves every non-case-bound outcome field
  identical (`tests/test_efficacy_mutations.py`).

`import mm_r4` re-exports the D06 domain model, evaluator, journey
projection and challenge-matrix builders.

## D07 clinical safety / laboratory / examination slice (`FROZEN_R4_D07_CONTRACT_V1`)

The D07 slice implements the frozen synthetic/offline clinical safety,
laboratory, vital-signs, ECG, physical-exam and imaging/other-examination
slice on top of the D01–D06 typed handoffs.  All inputs are synthetic and
offline; no real project, product service, browser/R5 surface, port 8911,
center/project aggregation or formal safety report is involved.

- **Domain model** (`d07_safety.py`): frozen contract identity
  (`D07_CONTRACT_SEMANTIC_HASH`, `D07_SCHEMA_VERSION`,
  `D07_TYPED_INPUT_SCHEMA`), canonical serialization/content addressing
  (NFC, sorted keys, compact separators, Decimal strings, NaN/Infinity
  rejected), the closed typed enumerations (disposition, positive
  subtypes, range/grade/CS-NCS/seriousness/priority, unit kinds, trend/
  repeat/action/explanation/AE-record states, owner actions, record
  status, lifecycle transitions), exact-key typed schemas for every
  section of the flat typed-input container and the fail-closed
  pre-evaluator integrity model with its frozen stage order.
- **Evaluator** (`d07_safety_evaluator.py`): the frozen first-failure
  integrity pipeline (`schema_parse → canonical_hash → artifact_hash →
  contract_semantic_hash → scope_cutoff → authority_version →
  correction_chain → identity_duplicate → foreign_key_bijection →
  d05_gate_applicability → evaluator_admission`) with closed error classes
  and no medical/priority/risk/Query/Journey output on failure, then the
  deterministic medical evaluation: unit/range selection, project-bound
  CTCAE/protocol grading with reported-vs-recomputed comparison, baseline
  selection and trend classification, CS/NCS controlled-value consistency,
  follow-up obligations, organ-pattern clues, examination-context
  interpretation, owner routing / D01–D04 handoffs, monitoring priority
  through the frozen precedence policy, lifecycle transitions, the
  coverage ledger / domain-completeness gates and the raw output root with
  exact trace/source leaves.  The runtime never imports the frozen
  catalog/oracle/registry and never branches on case/test/fixture ids.
- **Journey projection** (`d07_journey.py`): the shared visit/time-spine
  `D07SubjectJourneyProjection` with content-addressed event markers (one
  per accepted result, time-ordered, pending-zone flag), risk markers
  (positive/boundary units anchored to the triggering result with lexicon
  domain/risk-type labels), reversible source jumps (cardinality-one
  contract, one reverse binding per jump, typed target refs), the
  recomputed twelve-field shared-spine scope/hash equality decision, and
  per-payload `D07AudiencePayloadValidationResult` /
  `D07SourceJumpValidationResult` checks (exact-key schemas, forbidden
  internal tokens, domain/risk specificity, visible path, scope equality).
  The raw root carries only the deterministic `journey.*` summary leaves.
- **Query draft** (`d07_query.py`): the three-part natural-Chinese
  `D07QueryDraft` (basis / finding / action sentences) with evidence refs
  and content addresses, and the unique `D07PDWordingPermissionDecision`
  gating "是否涉及 PD" wording on an accepted typed D04 context ref with
  all scope/hash/accepted conditions true.  Drafts are viewable/editable/
  exportable; they are never sent and no external reply is tracked.

`import mm_r4` re-exports the D07 domain model, evaluator, journey
projection, Query draft and validation entrypoints.

## Running tests

```bash
pytest -q -p no:cacheprovider poc/medical_monitoring_ai_native_r4/tests
```

The frozen R1, R2 and R3 local `src` roots are configured on `sys.path` by the
test environment (`tests/conftest.py`) before any `mm_r4` import; the runtime
library itself does not mutate `sys.path`. No package installation or
real-project data is required. Port 8911 must remain stopped.
