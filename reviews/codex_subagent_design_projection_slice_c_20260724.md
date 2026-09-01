# Dynamic Design Projection Slice C Remediation

Date: 2026-07-24  
Owner: Codex  
Scope: real synopsis, chapter/applicability, SoA, study-flowchart and DOCX
consumers; Slice A/B typed semantics frozen

## Result

Slice C is implemented and verified. The five design-sensitive output surfaces
now share one source-current boundary:

```text
StudyDefinition
  -> confirmed current ProtocolAssemblyPlan
  -> normalize_study_design(..., include_sources=True)
  -> NormalizedDesignProjection
  -> synopsis / chapters / SoA / flowchart / DOCX
```

`MedicalWritingPlanConsumptionHelper.require_confirmed_design_projection`
verifies the current StudyDefinition identity, confirmed plan source identity,
normalized projection identity and projection-specific blockers before
returning any design fact to a consumer. Missing, unconfirmed, stale or
projection-blocked plans fail closed.

The real typed path no longer reads the five legacy booleans or treats
`framing.design_pattern` as downstream authority. Matrix fixtures deliberately
contain a conflicting legacy design sentence; every output asserts that it is
absent. Remaining `design_pattern` references are limited to pre-plan authoring
or lightweight backward-compatibility adapters, not a plan-gated Slice C
consumer.

## Consumer Changes

### Synopsis and chapters

- Company synopsis design rows render normalized randomization, blinding,
  comparator, Phase I Parts, treatment switch, crossover, OLE, blinded or
  unblinded sample-size re-estimation, adaptive design and SRC/DMC.
- Chapter applicability and section selection consume the same projection.
- Typed complex designs are mapped into existing semantic chapters rather than
  creating mechanical chapters:
  - treatment switch, crossover and OLE -> treatment regimen and
    treatment/follow-up;
  - sample-size re-estimation -> sample size;
  - adaptive design -> statistical principles;
  - interim analysis -> interim analysis;
  - SRC/DMC -> safety review/data monitoring committee.
- Required background treatment is projected from the current PICOS fact into
  the existing background-treatment chapter.

### Schedule of activities

- SoA columns and rows are generated from normalized Parts, crossover periods
  and washout, treatment-switch timing, OLE duration, interim/adaptive decision
  points, SSR timing and SRC/DMC.
- Background therapy and comparator rows remain current StudyDefinition PICOS
  facts; design applicability and typed design facts come from the normalized
  projection.

### Study flowchart

- Phase I SAD, MAD and first-in-patient flows use typed selected Parts.
- Crossover has distinct sequence, period, washout and carryover-analysis nodes;
  it is not represented as treatment switch.
- Treatment switch, OLE, interim analysis, adaptive decisions, SSR and SRC/DMC
  use explicit nodes with canonical structured source bindings.
- Complex background treatment appears in the intervention details.
- The washout node uses the existing allowed `other` node kind with the
  clinically explicit label `洗脱期`; no contract expansion was required.

### DOCX

- Export requires the confirmed `docx_toc` projection and verifies optional
  document-to-StudyDefinition binding.
- Export metadata records plan revision and normalized definition identity.
- Actual DOCX packages were generated and inspected through
  `word/document.xml`, including heading text, TOC field, body content, one
  structured SoA table and one rendered study-flowchart figure.

## Actual Output Matrix

The matrix is implemented in
`tests/test_medical_writing_design_projection_slice_c.py`. It asserts each
relevant output surface separately, not only plan objects or concatenated
text.

| Scenario | Synopsis / chapter assertions | SoA assertions | Flowchart assertions | DOCX assertions |
| --- | --- | --- | --- | --- |
| I期 SAD+MAD | SAD, MAD, I期研究组成 | SAD/MAD columns, SRC row | Part A/B, SRC gate | SAD/MAD body |
| I期 SAD+MAD+首次患者 | three typed Parts | three Part columns | Part A/B/C | three-Part body |
| III期复杂背景治疗+安慰剂 | placebo and MTX background | comparator/background rows | placebo arm and MTX detail | both facts in body |
| III期期中分析+安慰剂转组+OLE | interim, switch, OLE chapters/text | three timed rows/columns | switch, OLE and interim nodes | all three facts |
| III期阳性药对照 | active-control wording | active-control row | active-control arm | no placebo leakage |
| 2x2交叉 | sequences, periods, washout | sequence/washout rows | crossover graph, no switch | crossover facts |
| 盲态样本量再估计 | blinded SSR and variance | SSR timing row | blinded SSR decision gate | blinded SSR body |
| 适应性无缝II/III | seamless/adaptive/statistical controls | adaptive decision point | interim and adaptive gates | seamless design body |
| SRC/DMC存在 | both committees | both committee rows | both committee gates | both committee facts |
| SRC/DMC不存在 | committee chapter not applicable | no committee rows | no committee gates | no SRC/DMC leakage |

All scenarios also assert:

- the injected conflicting legacy `design_pattern` is absent;
- `1.1 方案摘要`, `1.2 研究示意图`, `1.3 研究流程表` and
  `4.1 总体设计` agree between document structure and exported body;
- the Word TOC field is present;
- normalized definition SHA-256 equals the source StudyDefinition;
- table and figure counts are non-zero.

An additional test proves all five consumer routes fail closed without a
confirmed current plan.

## Changed Files

- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/medical_writing_design_projection.py`
- `services/api/app/medical_writing_plan_consumption.py`
- `services/api/app/medical_writing_protocol_template.py`
- `services/api/app/medical_writing_table_templates.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_document_exporter.py`
- `tests/test_medical_writing_study_schema.py`
- `tests/test_medical_writing_design_projection_slice_c.py`

No competitor-triage file, frontend reference panel, or Slice B consumer-excluded
surface was changed. No security audit was performed.

## Verification

Python compilation passed for every changed contract, service and test file.

Slice C actual-output matrix:

```text
python3 -m pytest -q tests/test_medical_writing_design_projection_slice_c.py
11 passed in 2.57s
```

Frozen Slice A/B contract suite:

```text
138 passed in 2.66s
```

Existing synopsis/chapter/SoA/flowchart/DOCX consumer suite:

```text
116 passed in 51.63s
```

Export API, greenfield runtime and real-project flow regression:

```text
42 passed in 45.06s
```

Final deduplicated focused regression:

```text
296 passed in 98.46s
```

The runs emitted eight existing FastAPI `on_event` deprecation warnings. No
test failed; those warnings are outside Slice C.

