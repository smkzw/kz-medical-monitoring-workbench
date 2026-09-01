# Dynamic Design Projection Slice A Remediation

Date: 2026-07-24  
Owner: Codex  
Scope: Slice A only

## Result

Slice A now has one public normalization entry point:

```python
normalize_study_design(definition, include_sources=False)
```

The prior Qoder implementation did not satisfy this contract. The first
`enforce_structured_authority` function contained the intended normalizer but
was later overwritten by a second function with an incompatible tuple-based
signature. The module therefore exported no `normalize_study_design`, and
test collection failed.

## Remediation

### Contract

- Exported the typed Phase I and structured-design models through the package
  `__all__`.
- Preserved `MedicalWritingNormalizedDesignProjection` and its source-aware
  subtype as the Slice A projection contract.
- Changed projection validation so warning-only questions do not set
  `deterministic_projection_allowed=False`.
- Allowed several normalized semantics to reference the same canonical source
  path, which is required when randomization, blinding and comparator are all
  resolved from `framing.design_pattern`.

### Normalizer

- Replaced the conflicting functions with the single public
  `normalize_study_design` entry point.
- Removed the duplicated `_PHASE1_BLOCKED_PROJECTIONS`.
- Enforced authority order:
  1. a decided `framing.structured_design` value;
  2. conservative semantic resolution of `framing.design_pattern` and
     `picos.design_archetype`;
  3. `undecided` when source semantics are unsupported or contradictory.
- Added bounded support for Chinese and English randomization, open/single/
  double/triple blinding, placebo/active/no-control semantics.
- Added semantic-to-canonical-source-path output for `include_sources=True`.
- Filtered all residual Phase I Parts from normalized non-Phase I projections.

### Phase I semantics

- `_is_phase_one` accepts `I期`, `I/II期`, `I期/II期`, `PHASE1`,
  `Phase I`, `FIH`, `first-in-human` and `first-in-human=true`.
- It rejects Phase II, III and IV labels, including `II/III期`, and rejects
  `first-in-human=false`.
- A selected unresolved Phase I Part blocks only when `population` or
  `cohort_dose` is missing. PK/PD, safety, stopping rules, SoA summary and
  transition dependencies remain optional in the current Slice A model.

### Assembly and consistency

- The Phase I resolver consumes the normalized design projection.
- Only a selected unresolved Part blocks its own module.
- An unselected Part remains non-applicable and non-blocking.
- Each selected-Part question binds to its exact
  `framing.structured_design.phase1_parts[index]` source path.
- Non-Phase I residual Parts are checked from the original structured source
  before normalization, then reported as a reachable non-blocking warning.
- Structured-versus-legacy/PICOS conflicts are compared by normalized
  semantics. Decided structured facts remain authoritative and warnings do not
  disable deterministic projection.

## Verification

Production import:

```text
production_import_ok True AI Medical Manager Workbench
```

Core Slice A command:

```bash
python3 -m pytest -q \
  tests/test_medical_writing_design_projection.py \
  tests/test_medical_writing_structured_design_contract.py \
  tests/test_worker01_typed_phase1_parts_and_safe_prefill.py
```

Result:

```text
61 passed in 0.59s
```

Assembly and consistency command:

```bash
python3 -m pytest -q \
  tests/test_medical_writing_protocol_assembly_plan.py \
  tests/test_medical_writing_study_consistency.py
```

Result:

```text
28 passed in 1.62s
```

The second command emitted eight existing FastAPI `on_event` deprecation
warnings from `main.py`; no test failed and those warnings are outside Slice A.

Python compilation passed for all changed source and test files. Search
verification found exactly one `normalize_study_design` definition, no
`enforce_structured_authority` definition, and one
`_PHASE1_BLOCKED_PROJECTIONS` declaration.

## Boundary

No Slice B or Slice C implementation was changed. No security review was
performed.
