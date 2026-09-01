# R5-S5 Subject Workspace Contract Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Freeze, independently accept, then implement a synthetic/offline renderer-neutral R5-S5 Subject Workspace in which Patient Journey, indicator trends, and event details share one authoritative temporal spine, time window, selection, risk anchors, source locators, and append-only AE/MH later-recorded history.

**Architecture:** S5 remains a pure projection layer over accepted S1-S4. Current stage artifacts still mark `subject-temporal-public-v1` and `aemh-match-history-public-v1` as deferred, so the first hard gate is to establish and independently accept those upstream public authority contracts with receipt/hash/visibility/source lineage; a fixture, R1 reference renderer, or S5-local derivation may never substitute for them. Only after that gate may S5 introduce exact typed contracts, an authority adapter/builder, a deterministic projection, and an untrusted-Mapping validator; no UI, server, browser, real project/model, clinical writeback, or medical-writing path is touched.

**Tech Stack:** Python frozen dataclasses, canonical JSON/SHA-256, pytest normal and `PYTHONOPTIMIZE=2`, Ruff, existing R4/R5 typed public objects, synthetic fixtures only.

---

## Current accepted baseline

- S4 verdict: `ACCEPT_R5_S4` for synthetic/offline renderer-neutral runtime only.
- S4 focused: 495 passed normal/O2; adjacent R5: 1637 passed plus five contract-authorized deselects normal/O2.
- S4 cardinality erratum: current accepted authority maximum `min(10,A)=6`; no N=10 claim.
- Root `src/mm_r5/__init__.py` remains frozen and must not be edited without a later integration contract.
- 8911 remains stopped through S5 contract/runtime work.

## Task 1: Freeze the S5 source-authority inventory

**Objective:** Identify every upstream leaf that may lawfully drive Subject Workspace and mark unavailable authority as named deferred instead of fabricating it.

**Files:**

- Read: `reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md`
- Read: `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- Read: `context/medical_monitoring_r5_s4_acceptance_record_20260819.md`
- Read: `poc/medical_monitoring_ai_native_r1/src/**` temporal/Journey public contracts
- Read: `poc/medical_monitoring_ai_native_r4/src/mm_r4/**` subject-temporal and AE/MH public objects
- Read: `poc/medical_monitoring_ai_native_r5/src/mm_r5/s2_*.py`
- Read: `poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_*.py`
- Create later: `context/medical_monitoring_r5_s5_contract_20260819_context.md`

**Steps:**

1. Enumerate exact upstream dataclass paths for project/run/snapshot/cutoff/site/subject/spine, visits, events, risk anchors, source locators, and AE/MH match history.
2. Classify each planned S5 leaf as `r4_direct`, `derived`, `canonical_derived`, `ui_state`, `contract_constant`, or named `deferred`.
3. Prove every direct path resolves segment-by-segment in current dataclasses.
4. Record protected SHA pins for S1-S4, root init, accepted artifacts, and medical-writing boundary.
5. Stop if the authoritative temporal or match-history object does not exist; create a named deferred contract rather than rebuilding medical truth in S5.
6. Freeze and independently accept `subject-temporal-public-v1` and `aemh-match-history-public-v1`, including exact leaf schemas, receipt/content hashes, visibility decision, source-revision lineage, identity joins, and fail-closed errors.
7. If either public authority still has a deferred core leaf after review, the only positive shape verdict is `ACCEPT_R5_S5_CONTRACT_SHAPE_RUNTIME_BLOCKED`; `ACCEPT_R5_S5_CONTRACT` is forbidden. Runtime creation is mechanically unlocked only when all three conditions are true: `ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1`, `ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1`, and `ACCEPT_R5_S5_CONTRACT`, with zero deferred core authority leaves.

## Task 2: Draft the exact S5 implementation contract

**Objective:** Define one unambiguous runtime contract before any implementation file is created.

**Files:**

- Create later: `reviews/medical_monitoring_r5_s5_implementation_contract_v0_1_20260819.md`

**Required objects:**

- `R5S5AuthorityReceipt`
- `R5S5SubjectWorkspaceState`
- `R5S5TemporalSpineProjection`
- `R5S5VisitNode`
- `R5S5JourneyTrack`
- `R5S5JourneyEvent`
- `R5S5RiskAnchor`
- `R5S5PendingDateItem`
- `R5S5IndicatorSeries` and point/interval value contracts
- `R5S5EventDetailRow`
- `R5S5SourceResolution`
- `R5S5AEMHMatchHistory` and append-only transition entries
- `R5S5AudienceEncodingRegistry`, `R5S5AudienceLexicon`, domain-encoding and severity-lexicon items
- `R5S5WorkspacePacket`, validation issue/result, and canonical hash objects

**Frozen semantics:**

1. One shared spine/axis/window/selection across Journey, indicator trends, and event details; no second Profile/Timeline time state.
2. Axis mode is a closed `calendar/study_day` choice only. Nominal/actual/unscheduled visits, treatment phases, first/last dosing, and cutoff are overlays on that single axis, never additional axis modes.
3. Visit nodes preserve nominal and actual identity; unscheduled and between-visit events retain actual chronology and are never snapped to planned visits.
4. Date states are closed: exact, partial, conflicted, missing. Geometry is closed: `point`, `closed_interval`, `open_start`, `open_end`. Start and end each carry their own state, candidate values/ranges, source refs, and main-axis projectability. Missing dates never enter the main axis; partial/conflicted dates remain visibly uncertain and are never compressed to a fabricated exact date.
5. Eight primary domains are closed: AE, MH, concomitant medication, investigational product, laboratory/examination, hospitalization/procedure, symptom/efficacy, protocol compliance. Unknown fails closed; no silent OTHER bucket.
6. The risk overlay is uniquely `double_chevron_badge + outer_ring`, forbidden to every event domain; protocol-compliance events use a single flag. Each of the eight domains has one unique short Chinese label, shape, and line style. `症状与疗效` is exactly `circle + trend` with a frozen subtype map.
7. Severity is exact `critical/high/medium/low ↔ 紧急/高/中/低`; R5 never promotes high to critical. Legacy severe/moderate/mild and background/non-drug convert only through frozen mappings; otherwise they enter `领域待确认`, never OTHER.
8. Every critical/high/medium risk anchor remains visible with no top-N truncation; overlap may cluster only with stable identity and lossless member expansion.
9. Journey, indicator trends, and event details all reference the same workspace state/content hash and verify identical visit/event/risk selection membership.
10. S5 consumes and verifies canonical deep-link/source refs and no-nearest membership only. URL encoding/decoding, return restoration, and accessibility are S6; real navigation/click/Playwright/performance and 8911 are S7.
11. AE/MH suspected-missed-reporting remains a risk/clinical clue, not a recorded AE/MH. Later-recorded exact/ambiguous/rejected/withdrawn/reappeared match entries are append-only, preserve the original reminder history, and never auto-close a risk.
12. Filtering, zooming, selecting, view switching, or opening a source never writes clinical/risk lifecycle state.
13. Audience Chinese uses clinical terms; internal labels such as “正式事实”“候选信号”“已记录事项”“通用风险点”“只读xx” and backend/model/hash identifiers are forbidden.

## Task 3: Freeze the S5 challenge registry and non-LLM anchors

**Objective:** Make the contract falsifiable with explicit mutations and deterministic expected outcomes.

**Files:**

- Create later: `artifacts/medical_monitoring_r5_s5_contract_v0_1/packet_schema.json`
- Create later: `artifacts/medical_monitoring_r5_s5_contract_v0_1/exact_overlay.json`
- Create later: `artifacts/medical_monitoring_r5_s5_contract_v0_1/source_matrix.json`
- Create later: `artifacts/medical_monitoring_r5_s5_contract_v0_1/challenge_registry.json`
- Create later: `artifacts/medical_monitoring_r5_s5_contract_v0_1/base_inputs.json`
- Create later: `artifacts/medical_monitoring_r5_s5_contract_v0_1/manifest.json`
- Create later: `tools/generate_medical_monitoring_r5_s5_contract_v0_1.py`
- Create later: `tools/verify_medical_monitoring_r5_s5_contract_v0_1.py`

**Inherited S5 challenge set (exactly 64 rows from the accepted 204-row ledger):**

- `R5C-101..108`: 8 `visit_semantics`
- `R5C-109..116`: 8 `axis_conversion`
- `R5C-117..124`: 8 `uncertain_dates`
- `R5C-125..140`: 16 `eight_domain_adaptation`
- `R5C-141..148`: 8 `encoding_registry`
- `R5C-149..156`: 8 `aemh_projection`
- `R5C-157..164`: 8 `aemh_match_history`

The S5 contract must copy neither quotas nor semantics into an unconstrained second ledger. It pins and projects these exact accepted case ids, rule ids, severities, test locators, one-mutation inputs, typed expected outcomes, forbidden audience outputs, and non-LLM anchors. Deep-link/return remains an S2 regression; source one-hop remains an S4 regression; interaction/replay belongs to S6; lexicon/performance belongs to S7. They may run as adjacent regressions but S5 cannot reassign them or claim those stages complete.

Every inherited row must execute at S5 through a real typed fixture and real validator/evaluator, with canonical projection hash evidence. The verifier must pin the exact artifact set, parent 204-row ledger SHA, 64-row S5 projection, and current contract SHA; run under normal and optimized Python; use explicit exceptions rather than `assert`; and never pretend later runtime behavior has already executed.

## Exact staged write boundaries

All listed paths are create-only. If any listed create-only path already exists before its gate, any allowlist-external path changes, or any protected old file changes, the stage fails closed.

**Contract stage allowlist:**

- `context/medical_monitoring_r5_s5_contract_20260819_context.md`
- `reviews/medical_monitoring_r5_s5_implementation_contract_v0_1_20260819.md`
- `artifacts/medical_monitoring_r5_s5_contract_v0_1/{packet_schema,exact_overlay,source_matrix,challenge_registry,base_inputs,manifest}.json`
- `tools/generate_medical_monitoring_r5_s5_contract_v0_1.py`
- `tools/verify_medical_monitoring_r5_s5_contract_v0_1.py`
- contract review/metrics/acceptance files named in Task 4

**Runtime stage allowlist:** exactly the 12 files listed in Task 5; all must be absent at contract acceptance.

**Closure stage allowlist:**

- `context/medical_monitoring_r5_s5_acceptance_record_20260819.md`
- `reviews/codex_execution_medical_monitoring_r5_s5_runtime_20260819_review.md`
- `metrics/medical_monitoring_r5_s5_runtime_20260819_execution_metrics.md`
- workflow-guard-owned execution archives only

Pre/post SHA and path-diff gates cover R4, R5 S1–S4, root init, `frontend/**`, `services/**`, `packages/**`, `runtime/**`, every path containing `medical-writing`, `medical_writing`, or the Chinese component `医学写作`, and all real project roots. Task 1 must resolve the actual medical-writing roots from the current filesystem and record their canonical absolute paths and starting SHA/path inventory in the contract context; string matching alone is insufficient. 8911 must have zero listeners throughout S5.

## Task 4: Independently accept the contract

**Objective:** Prevent implementation against an ambiguous or self-inconsistent contract.

**Files:**

- Create later after acceptance: `context/medical_monitoring_r5_s5_contract_acceptance_record_20260819.md`
- Create later: `reviews/codex_execution_medical_monitoring_r5_s5_contract_20260819_review.md`
- Create later: `metrics/medical_monitoring_r5_s5_contract_20260819_execution_metrics.md`

**Steps:**

1. Freeze raw SHA values for contract, generator, verifier, schemas, source matrix, registry, base inputs, and manifest.
2. Run generator check and verifier in normal and O2 modes.
3. Independently review the same immutable SHA set in a fresh context.
4. Accept implementation-capable contract state only as `ACCEPT_R5_S5_CONTRACT`; any P0-P4 or snapshot drift returns `REVISE_R5_S5_CONTRACT`. If contract shape is coherent but either public authority remains deferred, return only `ACCEPT_R5_S5_CONTRACT_SHAPE_RUNTIME_BLOCKED`; this verdict never unlocks Task 5.
5. Keep 8911 stopped and prove no S5 runtime files exist before acceptance.

## Task 5: Implement the renderer-neutral S5 runtime in ordered slices

**Objective:** Build the smallest coherent runtime only after Task 4 acceptance.

**Planned create-only files:**

- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_contracts.py`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_authority_builder.py`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_projection.py`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_validator.py`
- `poc/medical_monitoring_ai_native_r5/tests/s5_runtime_fixtures.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_s5_contracts.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_s5_authority_builder.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_s5_projection.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_s5_validator.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_s5_readonly_gate.py`
- `poc/medical_monitoring_ai_native_r5/tests/challenges/test_s5_runtime_challenges.py`
- `poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s5_readonly_sha256.json`

**Ordered implementation:**

1. Write failing typed-contract tests for exact bool/type/enum/nullability/hash/history rules.
2. Implement frozen dataclasses and closed Chinese mappings.
3. Write failing authority tests for every identity/source/temporal/history join.
4. Implement builder with real upstream typed joins; no S5 risk or medical-value recomputation.
5. Write failing projection tests for shared state, eight domains, date states, risk anchors, indicator/event views, and AE/MH history.
6. Implement deterministic renderer-neutral packet projection.
7. Write untrusted-Mapping recursive structure and mutation tests.
8. Implement validator that independently rebuilds expected packet and compares every leaf/hash/member.
9. Execute every frozen runtime challenge through the real builder/validator.
10. Add exact allowlist/no-cache/frozen-SHA gates; do not export through root init.

## Task 6: Verify and independently accept S5 runtime

**Objective:** Prove the runtime contract in the real local environment without entering UI scope.

**Verification commands:**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -q -p no:cacheprovider \
  tests/test_s5_contracts.py tests/test_s5_authority_builder.py \
  tests/test_s5_projection.py tests/test_s5_validator.py \
  tests/test_s5_readonly_gate.py tests/challenges/test_s5_runtime_challenges.py
```

```bash
PYTHONOPTIMIZE=2 PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -q \
  -p no:cacheprovider <same focused nodes>
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -q -p no:cacheprovider tests \
  <only contract-authorized historical deselects>
```

```bash
python3 -m ruff check <all S5 source/test files>
lsof -nP -iTCP:8911 -sTCP:LISTEN
```

**Acceptance:** A fresh isolated reviewer must replay identity, date, domain, shared-state, hash, history, source, and AE/MH attacks and return `ACCEPT_R5_S5`. Worker green tests are not acceptance.

## Task 7: Close and hand off the stage

**Objective:** Preserve a lossless resume point and prepare S6 without implying product readiness.

**Files:**

- Create later: `context/medical_monitoring_r5_s5_acceptance_record_20260819.md`
- Create later: S5 Codex closure review and metrics files; they must not pre-exist the closure stage.
- Archive later: execution prompts/runs/logs via workflow guard after acceptance.

**Done evidence:**

- Contract and runtime each have separate independent acceptance verdicts.
- Focused and adjacent normal/O2 tests pass with zero skips except explicitly frozen historical deselects.
- All protected SHA pins are unchanged; S5 `.pyc` is absent; 8911 is stopped.
- Acceptance states only synthetic/offline renderer-neutral S5, not UI/browser/real project/model/product/production.

## Risks and explicit non-goals

- Existing R1 Profile/Timeline renderers are migration references, not S5 authority.
- S5 must not infer actual dates from nominal visits, silently map unknown domains, collapse AE/MH clues into recorded events, or auto-close risks after later records appear.
- S5 does not start 8911, edit frontend/services, run Playwright, ingest real projects, call real models, modify medical writing, or design security controls.
- S6/S7 will handle deep-link/return/accessibility/performance completion and product/browser integration respectively; S5 must expose sufficient canonical state but cannot claim those later stages complete.
