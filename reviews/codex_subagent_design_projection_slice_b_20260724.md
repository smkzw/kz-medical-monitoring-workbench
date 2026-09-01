# Dynamic Design Projection Slice B Remediation

Date: 2026-07-24  
Owner: Codex  
Scope: typed complex designs only; no Slice C consumer implementation

## Result

Slice B is implemented on top of the frozen Slice A
`normalize_study_design(definition, include_sources=False)` entry point.

Five independent typed design objects are now authoritative:

1. `MedicalWritingTreatmentSwitchDesign`
2. `MedicalWritingCrossoverDesign`
3. `MedicalWritingOpenLabelExtensionDesign`
4. `MedicalWritingSampleSizeReestimationDesign`
5. `MedicalWritingAdaptiveDesign`

They remain distinct clinical and statistical concepts. No synopsis, SoA,
study-flowchart or DOCX consumer was added or changed.

## Typed writing facts

### Treatment switch

- planned status
- trigger or timing
- eligible population
- destination treatment
- blinding strategy
- analysis handling

### Crossover

- planned status
- treatment sequences
- study periods
- washout strategy
- carryover assessment
- period and sequence analysis

### Open-label extension

- planned status
- entry source and eligibility
- extension treatment regimen
- duration
- blind-break and transition handling
- long-term objectives

### Sample-size re-estimation

- planned status
- closed `blinded` / `unblinded` mode
- timing or information fraction
- parameter to re-estimate
- decision rule
- alpha protection
- operational protection

### Adaptive design

- planned status
- closed adaptive type
- adaptation timing
- decision criteria
- adaptable elements
- simulation and operating characteristics
- type-I error control
- operational control

For every typed design:

- `planned=True` retains details and reports one precise blocker per missing
  required writing fact.
- `planned=False` clears fields that are not applicable.
- `planned=None` remains an unresolved planning decision.

## Legacy migration

The five old fields remain accepted as legacy input:

- `treatment_switch_planned`
- `crossover_planned`
- `open_label_extension_planned`
- `sample_size_reestimation_planned`
- `adaptive_design_enabled`

Migration is deterministic:

- `True` becomes typed `planned=True` with unresolved details.
- `False` becomes typed `planned=False`.
- `None` becomes typed `planned=None`.
- legacy `adaptive_features` migrate to typed `adaptable_elements`.

When a typed object and a contradictory old boolean are both supplied, the
typed object wins. Old attributes remain derived compatibility mirrors only
and are excluded from serialization. Serialized v2 payloads contain only the
typed authority, and serialize -> validate -> serialize is stable.

The authoring-prefill adaptive-design writer was updated to write the typed
object directly rather than recreating an obsolete boolean fact.

## Projection and assembly

`MedicalWritingNormalizedDesignView` now carries all five typed objects.
`include_sources=True` maps each semantic object to its canonical
`framing.structured_design.*` path.

Projection blocker scope:

- treatment switch, crossover and OLE affect the full design projection set;
- sample-size re-estimation affects document/statistical projections, not SoA
  or the study-schema flowchart;
- adaptive design affects document and flowchart projections, not SoA.

Assembly retains the existing semantic module identifiers. It does not create
five or seven mechanical protocol chapters. Each module resolves as:

- complete planned design: `conditional_applicable`;
- explicitly not planned: `not_applicable`;
- planned status unknown: unresolved;
- planned but incomplete: field-specific unresolved blockers.

Design drivers now include:

- `treatment_switch`
- `crossover`
- `open_label_extension`
- `sample_size_reestimation`
- `adaptive_design`

Each driver binds to the typed object path. No assembly code reads the five
legacy booleans.

## Consistency checks

Added blocking consistency checks for:

- crossover sequence semantics entered as treatment switch while crossover is
  not planned;
- OLE semantics entered as treatment switch while OLE is not planned;
- group-sequential adaptive design with interim analysis explicitly disabled;
- adaptive type `sample_size_reestimation` while typed SSR is explicitly not
  planned.

Legitimate co-existence of switch, crossover and OLE is not rejected merely
because more than one is planned.

## Verification

New Slice B tests:

```text
tests/test_medical_writing_complex_design_typed.py
29 passed
```

Final requested Slice A + Slice B + assembly + consistency + worker01/02
regression:

```text
138 passed in 2.32s
```

Combined Slice A, Slice B, assembly, consistency, worker01/02/03, plan
consumption, authoring-prefill, greenfield and export regression:

```text
279 passed in 7.36s
```

Additional synopsis-import compatibility regression:

```text
27 passed in 2.82s
```

Production import:

```text
production_import_ok AI Medical Manager Workbench True
```

Python compilation passed for all changed contract, service and test files.
The test runs emitted eight existing FastAPI `on_event` deprecation warnings;
no test failed and those warnings are outside Slice B.

## Changed surfaces

- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/medical_writing_design_projection.py`
- `services/api/app/medical_writing_protocol_assembly_plan.py`
- `services/api/app/medical_writing_study_consistency.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `tests/test_medical_writing_complex_design_typed.py`
- `tests/test_worker02_plan_consumption_cross_projection.py`  
  Only its confirmable Phase I fixtures were completed with the population and
  cohort/dose facts required by frozen Slice A.

## Boundary

No synopsis, schedule-of-activities, study-schema flowchart or DOCX consumer
implementation was changed. No security audit was performed.
